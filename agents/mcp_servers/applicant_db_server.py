import json
from pathlib import Path
from fastmcp.server import Server
from typing import Any

app = Server("ApplicantDB")

# Load mock data
DATA_DIR = Path(__file__).parent.parent.parent / "data"

def load_applicants():
    with open(DATA_DIR / "mock_applicants.json") as f:
        return json.load(f)

@app.call_tool()
def get_applicant_profile(applicant_id: str) -> dict:
    """Retrieve complete applicant profile with financial details"""
    applicants = load_applicants()
    if applicant_id in applicants["applicants"]:
        profile = applicants["applicants"][applicant_id]
        return {
            "success": True,
            "applicant_id": profile["applicant_id"],
            "name": profile["name"],
            "age": profile["age"],
            "income": profile["income"],
            "employment_type": profile["employment_type"],
            "employment_years": profile["employment_years"],
            "existing_liabilities": profile["existing_liabilities"],
            "location": profile["location"],
            "credit_history": profile["credit_history"]
        }
    return {"success": False, "error": f"Applicant {applicant_id} not found"}

@app.call_tool()
def calculate_income_stability_score(applicant_id: str) -> dict:
    """Calculate income stability score based on employment and history"""
    applicants = load_applicants()
    if applicant_id not in applicants["applicants"]:
        return {"success": False, "error": f"Applicant {applicant_id} not found"}

    applicant = applicants["applicants"][applicant_id]
    employment_type = applicant["employment_type"]
    years = applicant["employment_years"]

    # Calculate base score
    base_score = 50

    # Employment type scoring
    employment_scores = {
        "full_time": 40,
        "contract": 25,
        "self_employed": 30,
        "part_time": 15,
        "unemployed": 0
    }
    base_score = employment_scores.get(employment_type.lower(), 20)

    # Employment tenure scoring
    if years >= 5:
        tenure_score = 30
    elif years >= 2:
        tenure_score = 20
    elif years >= 1:
        tenure_score = 10
    else:
        tenure_score = 0

    stability_score = base_score + tenure_score

    return {
        "success": True,
        "applicant_id": applicant_id,
        "income_stability_score": stability_score,
        "employment_type": employment_type,
        "years_employed": years,
        "components": {
            "employment_score": base_score,
            "tenure_score": tenure_score
        }
    }

@app.call_tool()
def evaluate_credit_history(applicant_id: str) -> dict:
    """Evaluate credit history for red flags"""
    applicants = load_applicants()
    if applicant_id not in applicants["applicants"]:
        return {"success": False, "error": f"Applicant {applicant_id} not found"}

    applicant = applicants["applicants"][applicant_id]
    credit_history = applicant["credit_history"]

    return {
        "success": True,
        "applicant_id": applicant_id,
        "credit_history_summary": credit_history,
        "red_flags": {
            "late_payments": credit_history["late_payments"] > 0,
            "default_accounts": credit_history["default_accounts"] > 0,
            "accounts_in_good_standing_ratio": credit_history["accounts_in_good_standing"] / max(credit_history["accounts"], 1)
        },
        "risk_assessment": "HIGH" if credit_history["default_accounts"] > 0 else "MEDIUM" if credit_history["late_payments"] > 2 else "LOW"
    }

@app.call_tool()
def check_completeness(applicant_id: str, loan_amount: float, tenure_months: int) -> dict:
    """Check if application is complete and valid"""
    applicants = load_applicants()
    if applicant_id not in applicants["applicants"]:
        return {"success": False, "error": f"Applicant {applicant_id} not found"}

    applicant = applicants["applicants"][applicant_id]

    # Validation checks
    checks = {
        "age_valid": 18 <= applicant["age"] <= 80,
        "income_provided": applicant["income"] > 0,
        "loan_amount_valid": loan_amount > 0,
        "tenure_valid": 6 <= tenure_months <= 360,
        "employment_valid": applicant["employment_type"] in ["Full-time", "Contract", "Self-employed", "Part-time"]
    }

    is_complete = all(checks.values())

    return {
        "success": True,
        "applicant_id": applicant_id,
        "application_complete": is_complete,
        "validation_checks": checks,
        "missing_fields": [k for k, v in checks.items() if not v]
    }
