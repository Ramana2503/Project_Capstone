from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class LoanApplicationRequest(BaseModel):
    """Schema for loan application submission"""
    applicant_id: str = Field(..., description="Unique applicant identifier")
    # Applicant profile
    name: str = Field(..., description="Full name")
    age: int = Field(..., ge=18, le=100, description="Age in years")
    income: float = Field(..., gt=0, description="Annual income in dollars")
    employment_type: str = Field(..., description="Employment type (e.g. Full-time, Contract, Self-employed, Part-time)")
    employment_years: float = Field(..., ge=0, description="Years in current employment")
    credit_score: int = Field(..., ge=300, le=850, description="Credit score")
    existing_liabilities: float = Field(..., ge=0, description="Total existing liabilities in dollars")
    location: str = Field(..., description="City or region")
    # Loan details
    loan_amount: float = Field(..., gt=0, description="Loan amount in dollars")
    tenure_months: int = Field(..., ge=6, le=360, description="Loan tenure in months")
    # Credit history
    late_payments: int = Field(0, ge=0, description="Number of late payments on record")
    default_accounts: int = Field(0, ge=0, description="Number of default accounts on record")
    # Optional timestamp — defaults to now
    application_timestamp: Optional[str] = Field(None, description="ISO 8601 application timestamp")

class LoanApplicationResponse(BaseModel):
    """Schema for loan application response"""
    application_id: str
    applicant_id: str
    status: str
    decision: Optional[str]
    risk_score: Optional[float]
    confidence_level: Optional[float]
    explanation: Optional[str]
    timestamp: str

class ApplicationStatusResponse(BaseModel):
    """Schema for application status inquiry"""
    application_id: str
    applicant_id: str
    status: str
    decision: Optional[str]
    risk_score: Optional[float]
    confidence_level: Optional[float]
    key_factors: Optional[List[str]]
    explanation: Optional[str]
    created_at: str
    updated_at: str

class HealthResponse(BaseModel):
    """Schema for health check"""
    status: str
    version: str
    timestamp: str
