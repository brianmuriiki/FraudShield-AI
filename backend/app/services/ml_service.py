"""Loads the trusted model artifacts once at startup and produces predictions.

The artifacts are Joblib (pickle) files and are therefore treated as trusted executable
inputs: only files from the project's own MODEL_DIR are ever loaded.
"""
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib

from app.core.config import settings
from app.core.constants import MODEL_NAME, PRED_NOT_FLAGGED, PRED_SUSPICIOUS
from app.core.exceptions import ModelLoadError, ModelUnavailableError, PredictionError
from app.schemas.transaction import TransactionInput
from app.utils.feature_processing import FEATURE_ORDER, build_feature_frame
from app.utils.helpers import risk_level_for

logger = logging.getLogger(__name__)

REQUIRED_FILES = {
    "xgboost": "fraudshield_xgboost_model.pkl",
    "calibrated": "fraudshield_calibrated_model.pkl",
    "metadata": "fraudshield_metadata.pkl",
}

LIMITATIONS = [
    "Trained on the PaySim synthetic mobile-money dataset, not real M-Pesa records.",
    "Uses only nine features: step, amount, oldbalanceOrg, oldbalanceDest and transaction type.",
    "Does not analyse location, device, IP address, account age, recipient relationships, "
    "transaction velocity, behaviour profiles or payment channel.",
    "Metrics are historical offline evaluation results, not live production performance.",
    "A Suspicious prediction is a flag for human review, never confirmed fraud.",
]


def _as_dict(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    try:
        return dict(vars(obj))
    except TypeError:
        return {}


class MLService:
    def __init__(self, model_dir: Path, approved_threshold: float) -> None:
        self.model_dir = Path(model_dir)
        self.approved_threshold = approved_threshold
        self.calibrated_model: Any = None
        self.xgb_model: Any = None
        self.metadata: Dict[str, Any] = {}
        self.threshold: float = approved_threshold
        self.positive_index: int = 1
        self.loaded: bool = False
        self.error: Optional[str] = None
        self.metrics_source: str = "unavailable"

    # ------------------------------------------------------------------ loading
    def load(self) -> None:
        self.loaded = False
        self.error = None
        try:
            missing = [n for n in REQUIRED_FILES.values() if not (self.model_dir / n).is_file()]
            if missing:
                raise ModelLoadError(f"Missing model artifact(s): {', '.join(missing)}")
            self.xgb_model = joblib.load(self.model_dir / REQUIRED_FILES["xgboost"])
            self.calibrated_model = joblib.load(self.model_dir / REQUIRED_FILES["calibrated"])
            self.metadata = _as_dict(joblib.load(self.model_dir / REQUIRED_FILES["metadata"]))
            self._validate_features()
            self._validate_classes()
            self.threshold = self._resolve_threshold()
            self._smoke_test()
            self.loaded = True
            logger.info("Model artifacts loaded (threshold=%s).", self.threshold)
        except Exception as exc:  # noqa: BLE001
            self.error = str(exc) if isinstance(exc, ModelLoadError) else f"{type(exc).__name__} while loading model"
            logger.exception("Model loading failed: %s", self.error)

    def _meta(self, *keys: str) -> Any:
        for key in keys:
            if key in self.metadata and self.metadata[key] is not None:
                return self.metadata[key]
        return None

    def _validate_features(self) -> None:
        meta_features = self._meta("features", "feature_names", "feature_list", "feature_columns")
        if meta_features is not None and list(meta_features) != FEATURE_ORDER:
            raise ModelLoadError("Metadata feature list does not match the required nine features")
        for label, model in (("calibrated", self.calibrated_model), ("xgboost", self.xgb_model)):
            names = getattr(model, "feature_names_in_", None)
            if names is None and hasattr(model, "get_booster"):
                try:
                    names = model.get_booster().feature_names
                except Exception:  # noqa: BLE001
                    names = None
            if names is not None and list(names) != FEATURE_ORDER:
                raise ModelLoadError(f"{label} model feature names/order differ from the required features")
            if names is None:
                logger.warning("%s model exposes no feature names; order cannot be verified.", label)
            n_in = getattr(model, "n_features_in_", None)
            if n_in is not None and int(n_in) != len(FEATURE_ORDER):
                raise ModelLoadError(f"{label} model expects {n_in} features, not {len(FEATURE_ORDER)}")

    def _validate_classes(self) -> None:
        classes = getattr(self.calibrated_model, "classes_", None)
        if classes is not None:
            classes = list(classes)
            if 1 not in classes:
                raise ModelLoadError("Calibrated model has no positive class (1)")
            self.positive_index = classes.index(1)

    def _resolve_threshold(self) -> float:
        value = self._meta("threshold", "optimal_threshold", "decision_threshold", "selected_threshold")
        if value is None:
            logger.warning("Metadata has no threshold; using approved value %s.", self.approved_threshold)
            return self.approved_threshold
        value = float(value)
        if abs(value - self.approved_threshold) > 5e-4:
            raise ModelLoadError(
                f"Metadata threshold {value} differs from the approved threshold {self.approved_threshold}"
            )
        return round(value, 6)

    def _smoke_test(self) -> None:
        frame = build_feature_frame(1, 100.0, 100.0, 0.0, "TRANSFER")
        proba = self.calibrated_model.predict_proba(frame)
        if not 0.0 <= float(proba[0][self.positive_index]) <= 1.0:
            raise ModelLoadError("Smoke-test prediction outside [0, 1]")

    # --------------------------------------------------------------- prediction
    def _require_loaded(self) -> None:
        if not self.loaded:
            raise ModelUnavailableError()

    def predict_transaction(self, tx: TransactionInput) -> Dict[str, Any]:
        self._require_loaded()
        ttype = tx.transaction_type.value
        try:
            frame = build_feature_frame(tx.step, tx.amount, tx.oldbalanceOrg, tx.oldbalanceDest, ttype)
            proba = self.calibrated_model.predict_proba(frame)
            score = float(proba[0][self.positive_index])
        except Exception as exc:  # noqa: BLE001
            logger.exception("Prediction failed")
            raise PredictionError() from exc
        if math.isnan(score) or not 0.0 <= score <= 1.0:
            raise PredictionError("The model returned an invalid score.")

        suspicious = score >= self.threshold
        return {
            "prediction": PRED_SUSPICIOUS if suspicious else PRED_NOT_FLAGGED,
            "fraud_score": score,
            "threshold": self.threshold,
            "risk_level": risk_level_for(score, self.threshold),
            "requires_investigation": suspicious,
            "transaction_type": ttype,
            "model_name": MODEL_NAME,
            "message": (
                "The model flagged this transaction for further investigation. "
                "This is not confirmation of fraud."
                if suspicious
                else "The model did not flag this transaction. This does not guarantee it is legitimate."
            ),
        }

    # ----------------------------------------------------------------- metadata
    def describe(self) -> Dict[str, Any]:
        self._require_loaded()
        metrics = self._meta("test_metrics", "metrics", "test_results")
        confusion = self._meta("confusion_matrix", "test_confusion_matrix")
        if isinstance(metrics, dict) and metrics:
            clean = {k: float(v) for k, v in metrics.items() if isinstance(v, (int, float))}
            self.metrics_source = "model metadata" if clean else "unavailable"
        else:
            clean = None
            self.metrics_source = "unavailable"
        if confusion is not None and hasattr(confusion, "tolist"):
            confusion = confusion.tolist()
        notes = self._meta("important_notes") or []
        calibration_warning = next((str(note) for note in notes if "calibration" in str(note).lower()), None)
        dataset = self._meta("dataset")
        return {
            "model_name": str(self._meta("model_name") or MODEL_NAME),
            "model_version": str(self._meta("version", "model_version") or "unspecified"),
            "algorithm": "XGBoost Classifier",
            "calibration": str(getattr(self.calibrated_model, "method", "unknown")),
            "threshold": self.threshold,
            "feature_count": len(FEATURE_ORDER),
            "features": list(FEATURE_ORDER),
            "supported_transaction_types": ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"],
            "dataset": str(dataset) if dataset else None,
            "training_versions": dict(self._meta("versions") or {}),
            "hyperparameters": dict(self._meta("hyperparameters") or {}),
            "calibrated": bool(self._meta("calibrated")) if self._meta("calibrated") is not None else None,
            "loading_status": "loaded" if self.loaded else "unavailable",
            "calibration_warning": calibration_warning,
            "metrics": clean,
            "metrics_source": self.metrics_source,
            "confusion_matrix": confusion,
            "metrics_note": "Historical offline evaluation from the model metadata; not live production performance." if clean else "No verified evaluation metrics are present in model metadata.",
            "limitations": [*LIMITATIONS, *[str(note) for note in notes if "calibration" not in str(note).lower()]],
        }


ml_service = MLService(settings.MODEL_DIR, settings.APPROVED_THRESHOLD)


def load_models() -> None:
    ml_service.load()


def predict_transaction(transaction: TransactionInput) -> Dict[str, Any]:
    return ml_service.predict_transaction(transaction)
