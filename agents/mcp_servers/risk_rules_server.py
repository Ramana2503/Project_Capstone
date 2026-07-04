import json
from pathlib import Path
from fastmcp.server import Server
from typing import Any

app = Server("RiskRulesDB")

DATA_DIR = Path(__file__).parent.parent.parent / "data"

def load_rules():
    with open(DATA_DIR / "mock_risk_rules.json") as f:
        return json.load(f)

def load_applicants():
    with open(DATA_DIR / "mock_applicants.json") as f:
        return json.load(f)

@app.call_tool()
def calculate_debt_to_income(applicant_id: str, loan_amount: float, tenure_months: int) -> dict:
    """Calculate debt-to-income ratio"""
    applicants = load_applicants()
    if applicant_id not in applicants["applicants"]:
        return {"success": False, "error": f"Applicant {applicant_id} not found"}

    applicant = applicants["applicants"][applicant_id]
    monthly_income = applicant["income"] / 12

    # Estimate monthly loan payment (simple approximation)
    monthly_rate = 0.06 / 12  # Assume 6% annual rate
    num_payments = tenure_months
    if num_payments > 0:
        monthly_payment = (loan_amount * monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    else:
        monthly_payment = 0

    monthly_liabilities = applicant["existing_liabilities"] / 36 + monthly_payment  # Assume existing liabilities amortized over 3 years

    dti_ratio = (monthly_liabilities / monthly_income * 100) if monthly_income > 0 else 999

    return {
        "success": True,
        "applicant_id": applicant_id,
        "debt_to_income_ratio": round(dti_ratio, 2),
        "monthly_income": round(monthly_income, 2),
        "monthly_liabilities": round(monthly_liabilities, 2),
        "loan_monthly_payment": round(monthly_payment, 2)
    }

@app.call_tool()
def get_credit_score_risk_level(credit_score: int) -> dict:
    """Determine credit score risk level"""
    rules = load_rules()
    thresholds = rules["credit_score_thresholds"]

    for level_name, threshold_data in thresholds.items():
        if threshold_data["min"] <= credit_score <= threshold_data["max"]:
            return {
                "success": True,
                "credit_score": credit_score,
                "risk_level": threshold_data["risk_level"],
                "score_category": level_name
            }

    return {
        "success": False,
        "error": f"Credit score {credit_score} out of valid range"
    }

@app.call_tool()
def analyze_loan_amount_risk(applicant_id: str, loan_amount: float) -> dict:
    """Analyze loan amount risk relative to applicant income"""
    applicants = load_applicants()
    if applicant_id not in applicants["applicants"]:
        return {"success": False, "error": f"Applicant {applicant_id} not found"}

    applicant = applicants["applicants"][applicant_id]
    income = applicant["income"]

    loan_to_income_ratio = (loan_amount / income * 100) if income > 0 else 999

    # Risk classification
    if loan_to_income_ratio < 50:
        risk = "LOW"
    elif loan_to_income_ratio < 100:
        risk = "MEDIUM"
    elif loan_to_income_ratio < 200:
        risk = "HIGH"
    else:
        risk = "VERY_HIGH"

    return {
        "success": True,
        "applicant_id": applicant_id,
        "loan_amount": loan_amount,
        "annual_income": income,
        "loan_to_income_ratio": round(loan_to_income_ratio, 2),
        "loan_amount_risk": risk
    }

@app.call_tool()
def detect_anomalies(applicant_id: str, credit_score: int, late_payments: int, defaults: int, existing_liability: float, loan_amount: float) -> dict:
    """Detect anomalies in application data"""
    rules = load_rules()
    anomaly_rules = rules["anomaly_detection"]

    anomalies = []
    risk_score = 0

    # Check for excessive late payments
    if late_payments > anomaly_rules["late_payment_threshold"]:
        anomalies.append(f"Excessive late payments: {late_payments}")
        risk_score += 20

    # Check for defaults
    if defaults >= anomaly_rules["default_accounts_threshold"]:
        anomalies.append(f"Default accounts found: {defaults}")
        risk_score += 30

    # Check credit score anomaly
    if credit_score < 550:
        anomalies.append(f"Critically low credit score: {credit_score}")
        risk_score += 25

    # Check high existing liability
    if existing_liability > loan_amount * 0.5:
        anomalies.append(f"High existing liability relative to loan: {existing_liability}")
        risk_score += 15

    return {
        "success": True,
        "applicant_id": applicant_id,
        "anomalies_detected": len(anomalies) > 0,
        "anomalies": anomalies,
        "anomaly_risk_score": risk_score,
        "severity": "CRITICAL" if risk_score >= 50 else "HIGH" if risk_score >= 30 else "MEDIUM" if risk_score > 0 else "NONE"
    }

@app.call_tool()
def get_employment_risk_factor(employment_type: str, employment_years: int) -> dict:
    """Get risk factor multiplier for employment type and stability"""
    rules = load_rules()
    employment_risk = rules["employment_risk"]
    employment_stability = rules["employment_stability"]

    emp_lower = employment_type.lower()
    if emp_lower not in employment_risk:
        emp_lower = "full_time"

    base_multiplier = employment_risk[emp_lower]["multiplier"]
    base_risk_factor = employment_risk[emp_lower]["risk_factor"]

    # Adjust for employment stability
    if employment_years >= employment_stability["min_years_excellent"]:
        stability_adjustment = 0
    elif employment_years >= employment_stability["min_years_good"]:
        stability_adjustment = 0.05
    elif employment_years >= employment_stability["min_years_fair"]:
        stability_adjustment = 0.10
    else:
        stability_adjustment = employment_stability["new_employment_risk_factor"]

    total_risk_factor = base_risk_factor + stability_adjustment

    return {
        "success": True,
        "employment_type": employment_type,
        "employment_years": employment_years,
        "base_multiplier": base_multiplier,
        "base_risk_factor": base_risk_factor,
        "stability_adjustment": stability_adjustment,
        "total_risk_factor": round(total_risk_factor, 3)
    }
