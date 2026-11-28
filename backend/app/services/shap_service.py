"""SHAP explanations computed on the underlying XGBoost estimator (raw log-odds space)."""
import logging
from typing import Any, Dict, Optional

import numpy as np

from app.core.exceptions import ExplanationError, ModelUnavailableError
from app.services.ml_service import ml_service
from app.utils.feature_processing import FEATURE_ORDER, build_feature_frame

logger = logging.getLogger(__name__)

_LABELS = {
    "step": "Transaction time step",
    "amount": "Transaction amount",
    "oldbalanceOrg": "Sender balance before the transaction",
    "oldbalanceDest": "Recipient balance before the transaction",
}


class ShapService:
    def __init__(self) -> None:
        self.explainer: Any = None
        self.error: Optional[str] = None

    @property
    def ready(self) -> bool:
        return self.explainer is not None

    def init(self) -> None:
        self.explainer, self.error = None, None
        if not ml_service.loaded:
            self.error = "Model not loaded"
            return
        try:
            import shap  # imported lazily: heavy import

            self.explainer = shap.TreeExplainer(ml_service.xgb_model)
            logger.info("SHAP TreeExplainer initialised on the XGBoost estimator.")
        except Exception as exc:  # noqa: BLE001
            self.error = f"{type(exc).__name__} while creating the SHAP explainer"
            logger.exception("SHAP initialisation failed")

    @staticmethod
    def _describe(feature: str, value: float, contribution: float) -> str:
        direction = "increased" if contribution > 0 else "decreased" if contribution < 0 else "did not change"
        if feature.startswith("type_"):
            ttype = feature[len("type_"):]
            subject = f"Transaction type {'is' if value >= 0.5 else 'is not'} {ttype}"
        else:
            subject = _LABELS.get(feature, feature)
        return f"{subject} {direction} the model's raw risk output."

    def explain(
        self, step: int, amount: float, oldbalance_org: float, oldbalance_dest: float, transaction_type: str,
        transaction_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not ml_service.loaded:
            raise ModelUnavailableError()
        if not self.ready:
            raise ModelUnavailableError("The explanation service is not available.")
        frame = build_feature_frame(step, amount, oldbalance_org, oldbalance_dest, transaction_type)
        try:
            values = self.explainer.shap_values(frame)
            if isinstance(values, list):  # older SHAP: one array per class
                values = values[-1]
            arr = np.asarray(values)
            if arr.ndim == 3:  # (samples, features, classes)
                arr = arr[..., -1]
            arr = arr.reshape(-1)
            if arr.shape[0] != len(FEATURE_ORDER):
                raise ValueError(f"Unexpected SHAP output shape {arr.shape}")
            base = float(np.asarray(self.explainer.expected_value).reshape(-1)[-1])
        except Exception as exc:  # noqa: BLE001
            logger.exception("SHAP explanation failed")
            raise ExplanationError() from exc

        row = frame.iloc[0]
        features = []
        for name, contrib in zip(FEATURE_ORDER, arr):
            c = float(contrib)
            features.append(
                {
                    "feature": name,
                    "value": float(row[name]),
                    "contribution": round(c, 6),
                    "influence": "Positive" if c > 0 else "Negative" if c < 0 else "Neutral",
                    "description": self._describe(name, float(row[name]), c),
                }
            )
        features.sort(key=lambda f: abs(f["contribution"]), reverse=True)
        return {
            "transaction_id": transaction_id,
            "explanation_method": "SHAP",
            "output_space": "XGBoost raw margin (log-odds), not a calibrated probability",
            "base_value": round(base, 6),
            "raw_output": round(base + float(arr.sum()), 6),
            "features": features,
            "warning": "SHAP contributions explain model behaviour and do not establish fraud.",
        }


shap_service = ShapService()
