import pytest

from app.core.config import settings
from app.services.ml_service import REQUIRED_FILES

MODEL_PRESENT = all((settings.MODEL_DIR / f).is_file() for f in REQUIRED_FILES.values())
requires_model = pytest.mark.skipif(
    not MODEL_PRESENT,
    reason=f"Model artifacts not found in {settings.MODEL_DIR}; place the three .pkl files there to run this test",
)

TRANSFER_PAYLOAD = {
    "step": 379, "amount": 36942.13, "oldbalanceOrg": 36942.13, "oldbalanceDest": 0,
    "transaction_type": "TRANSFER",
}
PAYMENT_PAYLOAD = {
    "step": 12, "amount": 150.0, "oldbalanceOrg": 5000.0, "oldbalanceDest": 0, "transaction_type": "PAYMENT",
}
