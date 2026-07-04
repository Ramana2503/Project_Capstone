import json
from pathlib import Path
from fastmcp.server import Server
from typing import Any
from datetime import datetime

app = Server("DecisionSynthesis")

DATA_DIR = Path(__file__).parent.parent.parent / "data"

def load_rules():
    with open(DATA_DIR / "mock_risk_rules.json") as f:
        return json.load(f)

@app.call_tool()
def synthesize_decision(
    applicant_id: str,
    credit_score: int,
    dti_ratio: float,
    income_stability_score: int,
    has_defaults: bool,
    late_payments: int,
    anomaly_risk_score: int,
    employment_risk_factor: float
) -> dict:
    """Synthesize all inputs and make final loan decision"""
    rules = load_rules()
    approval_rules = rules["approval_rules"]

    # Initialize decision components
    decision = "PENDING"
    confidence = 0.0
    risk_score = 0.0
    factors = []

    # Credit score check
    if credit_score >= approval_rules["auto_approve_credit_score"]:
        decision = "APPROVED"
        confidence += 0.3
        factors.append("Excellent credit score")
    elif credit_score <= approval_rules["auto_reject_credit_score"]:
        decision = "REJECTED"
        confidence += 0.4
        factors.append("Critical credit score")
        risk_score += 40

    # DTI check
    if dti_ratio <= approval_rules["auto_approve_dti"]:
        confidence += 0.2
        factors.append("Excellent debt-to-income ratio")
    elif dti_ratio >= approval_rules["auto_reject_dti"]:
        decision = "REJECTED" if decision == "PENDING" else decision
        confidence += 0.3
        factors.append("Unacceptable debt-to-income ratio")
        risk_score += 35

    # Default accounts check
    if has_defaults:
        decision = "REJECTED" if decision == "PENDING" else decision
        confidence += 0.3
        factors.append("Applicant has defaulted accounts")
        risk_score += 50

    # Late payments check
    if late_payments > 3:
        decision = "REQUIRES_REVIEW" if decision == "PENDING" else decision
        factors.append("History of late payments")
        risk_score += 20
    elif late_payments > 0:
        risk_score += 10

    # Income stability check
    if income_stability_score >= 60:
        confidence += 0.15
        factors.append("Good income stability")
    elif income_stability_score < 30:
        risk_score += 15

    # Anomaly check
    if anomaly_risk_score >= 50:
        decision = "REQUIRES_REVIEW" if decision == "PENDING" else decision
        factors.append("Significant anomalies detected")
        risk_score += 25
    elif anomaly_risk_score > 0:
        risk_score += anomaly_risk_score * 0.5

    # Employment risk factor
    risk_score += employment_risk_factor * 20

    # Final decision logic
    if decision == "PENDING":
        if risk_score < 20:
            decision = "APPROVED"
            confidence = 0.95
        elif risk_score < 40:
            decision = "REQUIRES_REVIEW"
            confidence = 0.75
        else:
            decision = "REJECTED"
            confidence = 0.85

    # Normalize risk score to 0-100
    risk_score = min(100, max(0, risk_score))

    # Normalize confidence
    if decision == "APPROVED":
        confidence = min(1.0, max(0.5, confidence + 0.2))
    elif decision == "REJECTED":
        confidence = min(1.0, max(0.6, confidence))
    else:
        confidence = 0.65

    return {
        "success": True,
        "applicant_id": applicant_id,
        "decision": decision,
        "risk_score": round(risk_score, 2),
        "confidence_level": round(confidence, 2),
        "key_decision_factors": factors,
        "decision_timestamp": datetime.now().isoformat()
    }

@app.call_tool()
def generate_explanation(decision: str, factors: list, risk_score: float) -> dict:
    """Generate human-readable explanation for the decision"""
    explanations = {
        "APPROVED": "Application approved based on strong financial profile and low risk indicators.",
        "REJECTED": "Application rejected due to significant credit risk factors and inability to meet lending standards.",
        "REQUIRES_REVIEW": "Application requires manual review due to mixed signals and need for additional investigation."
    }

    base_explanation = explanations.get(decision, "Unable to determine explanation")

    detailed_explanation = f"{base_explanation}\n\nKey Factors:\n"
    for i, factor in enumerate(factors, 1):
        detailed_explanation += f"{i}. {factor}\n"

    detailed_explanation += f"\nRisk Score: {risk_score}/100"

    return {
        "success": True,
        "decision": decision,
        "brief_explanation": base_explanation,
        "detailed_explanation": detailed_explanation,
        "recommended_action": "PROCESS_IMMEDIATELY" if decision == "APPROVED" else "SCHEDULE_REVIEW" if decision == "REQUIRES_REVIEW" else "PREPARE_REJECTION_LETTER"
    }

@app.call_tool()
def calculate_final_risk_score(
    credit_risk: float,
    income_risk: float,
    employment_risk: float,
    anomaly_risk: float,
    liabilities_risk: float
) -> dict:
    """Calculate weighted final risk score from all components"""
    # Weighted average of risk components
    weights = {
        "credit": 0.35,
        "income": 0.20,
        "employment": 0.15,
        "anomaly": 0.20,
        "liabilities": 0.10
    }

    final_risk = (
        credit_risk * weights["credit"] +
        income_risk * weights["income"] +
        employment_risk * weights["employment"] +
        anomaly_risk * weights["anomaly"] +
        liabilities_risk * weights["liabilities"]
    )

    # Normalize to 0-100
    final_risk = min(100, max(0, final_risk))

    return {
        "success": True,
        "final_risk_score": round(final_risk, 2),
        "risk_components": {
            "credit_risk": round(credit_risk, 2),
            "income_risk": round(income_risk, 2),
            "employment_risk": round(employment_risk, 2),
            "anomaly_risk": round(anomaly_risk, 2),
            "liabilities_risk": round(liabilities_risk, 2)
        },
        "weights": weights,
        "risk_level": "CRITICAL" if final_risk >= 75 else "HIGH" if final_risk >= 50 else "MEDIUM" if final_risk >= 25 else "LOW"
    }
