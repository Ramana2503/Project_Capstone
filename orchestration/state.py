from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class LoanApplication:
    """Loan application input data"""
    applicant_id: str
    loan_amount: float
    tenure_months: int
    # Applicant profile supplied at submission time
    name: str = ""
    age: int = 0
    income: float = 0.0
    employment_type: str = ""
    employment_years: float = 0.0
    credit_score: int = 0
    existing_liabilities: float = 0.0
    location: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ApplicationState:
    """Complete state of loan application processing"""

    # Input
    application: LoanApplication

    # Stage 1: Applicant Profile Analysis
    applicant_profile: Optional[Dict[str, Any]] = None
    income_stability_score: Optional[float] = None
    credit_history: Optional[Dict[str, Any]] = None
    application_complete: Optional[bool] = None

    # Stage 2: Financial Risk Analysis
    dti_ratio: Optional[float] = None
    credit_score_risk_level: Optional[str] = None
    loan_amount_risk: Optional[str] = None
    anomalies_detected: Optional[List[str]] = None
    anomaly_risk_score: Optional[float] = None
    employment_risk_factor: Optional[float] = None

    # Stage 3: Loan Decision Making
    decision: Optional[str] = None  # APPROVED, REJECTED, REQUIRES_REVIEW
    final_risk_score: Optional[float] = None
    confidence_level: Optional[float] = None
    key_decision_factors: Optional[List[str]] = None
    decision_explanation: Optional[str] = None

    # Stage 4: Compliance & Action
    case_id: Optional[str] = None
    notification_sent: Optional[bool] = None
    compliance_action: Optional[str] = None

    # Metadata
    status: str = "INITIALIZED"  # INITIALIZED, PROFILING, RISK_ANALYSIS, DECIDING, ACTION, COMPLETED, FAILED
    errors: List[str] = field(default_factory=list)
    execution_log: List[str] = field(default_factory=list)

    def to_dict(self):
        """Convert state to dictionary"""
        return {
            "application": {
                "applicant_id": self.application.applicant_id,
                "name": self.application.name,
                "age": self.application.age,
                "income": self.application.income,
                "employment_type": self.application.employment_type,
                "employment_years": self.application.employment_years,
                "credit_score": self.application.credit_score,
                "existing_liabilities": self.application.existing_liabilities,
                "location": self.application.location,
                "loan_amount": self.application.loan_amount,
                "tenure_months": self.application.tenure_months,
                "timestamp": self.application.timestamp
            },
            "applicant_profile": self.applicant_profile,
            "income_stability_score": self.income_stability_score,
            "credit_history": self.credit_history,
            "application_complete": self.application_complete,
            "dti_ratio": self.dti_ratio,
            "credit_score_risk_level": self.credit_score_risk_level,
            "loan_amount_risk": self.loan_amount_risk,
            "anomalies_detected": self.anomalies_detected,
            "anomaly_risk_score": self.anomaly_risk_score,
            "employment_risk_factor": self.employment_risk_factor,
            "decision": self.decision,
            "final_risk_score": self.final_risk_score,
            "confidence_level": self.confidence_level,
            "key_decision_factors": self.key_decision_factors,
            "decision_explanation": self.decision_explanation,
            "case_id": self.case_id,
            "notification_sent": self.notification_sent,
            "compliance_action": self.compliance_action,
            "status": self.status,
            "errors": self.errors,
            "execution_log": self.execution_log
        }
