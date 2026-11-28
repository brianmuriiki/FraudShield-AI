"""Shared enumerations and constants."""
from enum import Enum

MODEL_NAME = "FraudShield XGBoost"
PRED_SUSPICIOUS = "Suspicious"
PRED_NOT_FLAGGED = "Not Flagged"
TX_AWAITING = "Awaiting Investigation"
TX_NOT_REQUIRED = "Not Required"
RISK_LEVELS = ("Low", "Moderate", "Elevated", "High")


class Role(str, Enum):
    ADMINISTRATOR = "administrator"
    SENIOR_ANALYST = "senior_analyst"
    FRAUD_ANALYST = "fraud_analyst"
    BI_ANALYST = "bi_analyst"


class TransactionType(str, Enum):
    CASH_IN = "CASH_IN"
    CASH_OUT = "CASH_OUT"
    DEBIT = "DEBIT"
    PAYMENT = "PAYMENT"
    TRANSFER = "TRANSFER"


class InvestigationStatus(str, Enum):
    NEW = "New"
    UNDER_REVIEW = "Under Review"
    ESCALATED = "Escalated"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class InvestigationOutcome(str, Enum):
    CONFIRMED_FRAUD = "Confirmed Fraud"
    LEGITIMATE = "Legitimate Transaction"
    INCONCLUSIVE = "Inconclusive"
    PENDING = "Pending"


class Priority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


OPEN_STATUSES = (
    InvestigationStatus.NEW.value,
    InvestigationStatus.UNDER_REVIEW.value,
    InvestigationStatus.ESCALATED.value,
)
CLOSED_STATUSES = (InvestigationStatus.RESOLVED.value, InvestigationStatus.CLOSED.value)

# Role groups used by endpoint guards
ALL_ROLES = tuple(Role)
REVIEWER_ROLES = (Role.ADMINISTRATOR, Role.SENIOR_ANALYST)
INVESTIGATION_ROLES = (Role.ADMINISTRATOR, Role.SENIOR_ANALYST, Role.FRAUD_ANALYST)
ANALYTICS_ROLES = (Role.ADMINISTRATOR, Role.SENIOR_ANALYST, Role.BI_ANALYST)
