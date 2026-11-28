from typing import Any


def normalize_transaction_type(value: Any) -> Any:
    """'cash out' / 'Cash-Out' / 'cash_out' -> 'CASH_OUT'. Non-strings pass through to be rejected."""
    if isinstance(value, str):
        return value.strip().upper().replace(" ", "_").replace("-", "_")
    return value
