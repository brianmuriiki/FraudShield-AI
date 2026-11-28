from typing import Dict, List

from pydantic import BaseModel


class TrendPoint(BaseModel):
    date: str
    total: int
    suspicious: int


class TypeBreakdown(BaseModel):
    transaction_type: str
    total: int
    suspicious: int
    confirmed_fraud: int


class DashboardSummary(BaseModel):
    total_transactions: int
    suspicious_transactions: int
    not_flagged_transactions: int
    confirmed_fraud_cases: int
    pending_investigations: int
    open_investigations: int
    resolved_investigations: int
    total_amount: float
    suspicious_amount: float
    risk_level_distribution: Dict[str, int]
    suspicious_trend: List[TrendPoint]
    fraud_by_type: List[TypeBreakdown]
    generated_at: str
    note: str
