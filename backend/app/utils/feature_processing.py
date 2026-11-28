"""Builds the exact 9-feature input the trained model expects (order matters)."""
from typing import Dict, List

import pandas as pd

FEATURE_ORDER: List[str] = [
    "step",
    "amount",
    "oldbalanceOrg",
    "oldbalanceDest",
    "type_CASH_IN",
    "type_CASH_OUT",
    "type_DEBIT",
    "type_PAYMENT",
    "type_TRANSFER",
]

SUPPORTED_TYPES = ("CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER")


def one_hot_type(transaction_type: str) -> Dict[str, int]:
    if transaction_type not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported transaction type: {transaction_type!r}")
    encoded = {f"type_{t}": int(t == transaction_type) for t in SUPPORTED_TYPES}
    assert sum(encoded.values()) == 1
    return encoded


def build_feature_dict(
    step: int, amount: float, oldbalance_org: float, oldbalance_dest: float, transaction_type: str
) -> Dict[str, float]:
    features: Dict[str, float] = {
        "step": step,
        "amount": amount,
        "oldbalanceOrg": oldbalance_org,
        "oldbalanceDest": oldbalance_dest,
    }
    features.update(one_hot_type(transaction_type))
    return {name: features[name] for name in FEATURE_ORDER}


def build_feature_frame(
    step: int, amount: float, oldbalance_org: float, oldbalance_dest: float, transaction_type: str
) -> pd.DataFrame:
    row = build_feature_dict(step, amount, oldbalance_org, oldbalance_dest, transaction_type)
    return pd.DataFrame([row], columns=FEATURE_ORDER).astype("float64")
