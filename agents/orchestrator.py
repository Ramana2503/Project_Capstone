"""
LangGraph-based orchestration engine.
Each stage is a LangGraph node. Claude drives decisions by calling
MCP server functions exposed as Anthropic tool-use tools.
"""

import os
import json
from typing import Optional, TypedDict, List, Any
from pathlib import Path
from anthropic import Anthropic
from langgraph.graph import StateGraph, END
from orchestration.state import LoanApplication, ApplicationState

client = Anthropic()
DATA_DIR = Path(__file__).parent.parent / "data"
MODEL = "global.anthropic.claude-haiku-4-5-20251001-v1:0"

# ── MCP Tool Definitions (all 4 servers) ─────────────────────────────────────

APPLICANT_DB_TOOLS = [
    {
        "name": "get_applicant_profile",
        "description": "Retrieve full applicant profile with financial details",
        "input_schema": {
            "type": "object",
            "properties": {
                "applicant_id": {"type": "string"},
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "income": {"type": "number"},
                "employment_type": {"type": "string"},
                "employment_years": {"type": "number"},
                "credit_score": {"type": "integer"},
                "existing_liabilities": {"type": "number"},
                "location": {"type": "string"},
            },
            "required": ["applicant_id"],
        },
    },
    {
        "name": "calculate_income_stability_score",
        "description": "Calculate income stability score based on employment type and tenure",
        "input_schema": {
            "type": "object",
            "properties": {
                "employment_type": {"type": "string"},
                "employment_years": {"type": "number"},
            },
            "required": ["employment_type", "employment_years"],
        },
    },
    {
        "name": "evaluate_credit_history",
        "description": "Evaluate credit history for red flags",
        "input_schema": {
            "type": "object",
            "properties": {
                "late_payments": {"type": "integer"},
                "default_accounts": {"type": "integer"},
                "accounts": {"type": "integer"},
                "accounts_in_good_standing": {"type": "integer"},
            },
            "required": ["late_payments", "default_accounts"],
        },
    },
]

RISK_RULES_TOOLS = [
    {
        "name": "calculate_debt_to_income",
        "description": "Calculate debt-to-income ratio",
        "input_schema": {
            "type": "object",
            "properties": {
                "monthly_income": {"type": "number"},
                "existing_liabilities": {"type": "number"},
                "loan_amount": {"type": "number"},
                "tenure_months": {"type": "integer"},
            },
            "required": ["monthly_income", "existing_liabilities", "loan_amount", "tenure_months"],
        },
    },
    {
        "name": "detect_anomalies",
        "description": "Detect anomalies in application data",
        "input_schema": {
            "type": "object",
            "properties": {
                "credit_score": {"type": "integer"},
                "late_payments": {"type": "integer"},
                "defaults": {"type": "integer"},
                "existing_liability": {"type": "number"},
                "loan_amount": {"type": "number"},
            },
            "required": ["credit_score", "late_payments", "defaults", "existing_liability", "loan_amount"],
        },
    },
    {
        "name": "get_employment_risk_factor",
        "description": "Get risk factor for employment type and stability",
        "input_schema": {
            "type": "object",
            "properties": {
                "employment_type": {"type": "string"},
                "employment_years": {"type": "number"},
            },
            "required": ["employment_type", "employment_years"],
        },
    },
]

DECISION_TOOLS = [
    {
        "name": "calculate_final_risk_score",
        "description": "Calculate weighted final risk score from all components",
        "input_schema": {
            "type": "object",
            "properties": {
                "credit_score": {"type": "integer"},
                "dti_ratio": {"type": "number"},
                "anomaly_risk_score": {"type": "number"},
                "employment_risk_factor": {"type": "number"},
                "liability_ratio": {"type": "number"},
            },
            "required": ["credit_score", "dti_ratio", "anomaly_risk_score", "employment_risk_factor", "liability_ratio"],
        },
    },
    {
        "name": "synthesize_decision",
        "description": "Make final APPROVED / REJECTED / REQUIRES_REVIEW decision with confidence level",
        "input_schema": {
            "type": "object",
            "properties": {
                "final_risk_score": {"type": "number"},
                "credit_score": {"type": "integer"},
                "has_defaults": {"type": "boolean"},
                "late_payments": {"type": "integer"},
                "dti_ratio": {"type": "number"},
                "anomaly_risk_score": {"type": "number"},
            },
            "required": ["final_risk_score", "credit_score", "has_defaults", "late_payments", "dti_ratio", "anomaly_risk_score"],
        },
    },
    {
        "name": "generate_explanation",
        "description": "Generate human-readable explanation for the loan decision",
        "input_schema": {
            "type": "object",
            "properties": {
                "decision": {"type": "string"},
                "key_factors": {"type": "array", "items": {"type": "string"}},
                "risk_score": {"type": "number"},
                "applicant_name": {"type": "string"},
            },
            "required": ["decision", "key_factors", "risk_score"],
        },
    },
]

COMPLIANCE_TOOLS = [
    {
        "name": "create_case_record",
        "description": "Create formal case record and audit log entry",
        "input_schema": {
            "type": "object",
            "properties": {
                "applicant_id": {"type": "string"},
                "decision": {"type": "string"},
                "risk_score": {"type": "number"},
                "confidence_level": {"type": "number"},
                "key_factors": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["applicant_id", "decision", "risk_score", "confidence_level", "key_factors"],
        },
    },
    {
        "name": "send_decision_notification",
        "description": "Send notification about loan decision to applicant",
        "input_schema": {
            "type": "object",
            "properties": {
                "applicant_id": {"type": "string"},
                "decision": {"type": "string"},
                "explanation": {"type": "string"},
            },
            "required": ["applicant_id", "decision", "explanation"],
        },
    },
    {
        "name": "log_compliance_action",
        "description": "Log compliance and audit action for the case",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string"},
                "action": {"type": "string"},
                "decision": {"type": "string"},
            },
            "required": ["case_id", "action", "decision"],
        },
    },
]

ALL_TOOLS = APPLICANT_DB_TOOLS + RISK_RULES_TOOLS + DECISION_TOOLS + COMPLIANCE_TOOLS

# ── Local MCP tool executors ──────────────────────────────────────────────────

def _exec_get_applicant_profile(inputs: dict) -> dict:
    return {
        "applicant_id": inputs.get("applicant_id"),
        "name": inputs.get("name", ""),
        "age": inputs.get("age", 0),
        "income": inputs.get("income", 0),
        "employment_type": inputs.get("employment_type", ""),
        "employment_years": inputs.get("employment_years", 0),
        "credit_score": inputs.get("credit_score", 0),
        "existing_liabilities": inputs.get("existing_liabilities", 0),
        "location": inputs.get("location", ""),
        "credit_history": {"accounts": 0, "accounts_in_good_standing": 0, "late_payments": 0, "default_accounts": 0},
    }


def _exec_calculate_income_stability_score(inputs: dict) -> dict:
    emp_type = inputs.get("employment_type", "").lower()
    years = inputs.get("employment_years", 0)
    employment_scores = {"full-time": 40, "full_time": 40, "contract": 25, "self-employed": 30, "self_employed": 30, "part-time": 15, "part_time": 15, "unemployed": 0}
    base = employment_scores.get(emp_type, 20)
    tenure = 30 if years >= 5 else 20 if years >= 2 else 10 if years >= 1 else 0
    return {"income_stability_score": base + tenure, "employment_type": emp_type, "years_employed": years}


def _exec_evaluate_credit_history(inputs: dict) -> dict:
    late = inputs.get("late_payments", 0)
    defaults = inputs.get("default_accounts", 0)
    accounts = inputs.get("accounts", 0)
    good = inputs.get("accounts_in_good_standing", 0)
    risk = "HIGH" if defaults > 0 else "MEDIUM" if late > 2 else "LOW"
    return {
        "late_payments": late,
        "default_accounts": defaults,
        "accounts_in_good_standing_ratio": good / max(accounts, 1),
        "risk_assessment": risk,
        "red_flags": {"late_payments": late > 0, "default_accounts": defaults > 0},
    }


def _exec_calculate_debt_to_income(inputs: dict) -> dict:
    monthly_income = inputs.get("monthly_income", 0)
    existing_liabilities = inputs.get("existing_liabilities", 0)
    loan_amount = inputs.get("loan_amount", 0)
    tenure = inputs.get("tenure_months", 60)
    monthly_rate = 0.06 / 12
    monthly_payment = (loan_amount * monthly_rate * (1 + monthly_rate)**tenure) / ((1 + monthly_rate)**tenure - 1) if tenure > 0 else 0
    monthly_liabilities = existing_liabilities / 36 + monthly_payment
    dti = (monthly_liabilities / monthly_income * 100) if monthly_income > 0 else 999
    return {"dti_ratio": round(dti, 2), "monthly_payment": round(monthly_payment, 2), "monthly_liabilities": round(monthly_liabilities, 2)}


def _exec_detect_anomalies(inputs: dict) -> dict:
    anomalies = []
    risk = 0
    if inputs.get("late_payments", 0) > 3:
        anomalies.append("Multiple late payments")
        risk += 20
    if inputs.get("defaults", 0) > 0:
        anomalies.append("Default accounts detected")
        risk += 30
    if inputs.get("credit_score", 700) < 550:
        anomalies.append("Critically low credit score")
        risk += 25
    if inputs.get("existing_liability", 0) > inputs.get("loan_amount", 1) * 0.5:
        anomalies.append("High existing liability relative to loan")
        risk += 15
    return {"anomalies": anomalies, "anomaly_risk_score": risk, "severity": "CRITICAL" if risk >= 50 else "HIGH" if risk >= 30 else "MEDIUM" if risk > 0 else "NONE"}


def _exec_get_employment_risk_factor(inputs: dict) -> dict:
    emp_type = inputs.get("employment_type", "full-time").lower().replace("-", "_")
    years = inputs.get("employment_years", 0)
    base = {"full_time": 0, "contract": 0.15, "self_employed": 0.10, "part_time": 0.25, "unemployed": 0.5}.get(emp_type, 0.0)
    stability = 0 if years >= 5 else 0.05 if years >= 2 else 0.10 if years >= 1 else 0.3
    return {"employment_risk_factor": round(base + stability, 3), "employment_type": emp_type, "years": years}


def _exec_calculate_final_risk_score(inputs: dict) -> dict:
    cs = inputs.get("credit_score", 700)
    dti = inputs.get("dti_ratio", 30)
    anomaly = inputs.get("anomaly_risk_score", 0)
    emp = inputs.get("employment_risk_factor", 0)
    liab = inputs.get("liability_ratio", 0)

    if cs >= 750: credit_risk = 10
    elif cs >= 700: credit_risk = 20
    elif cs >= 650: credit_risk = 35
    elif cs >= 600: credit_risk = 50
    else: credit_risk = 80

    if dti <= 20: dti_risk = 10
    elif dti <= 36: dti_risk = 20
    elif dti <= 50: dti_risk = 40
    else: dti_risk = 70

    liability_risk = 30 if liab > 0.5 else 10
    employment_risk = emp * 50

    score = credit_risk * 0.35 + dti_risk * 0.25 + anomaly * 0.20 + employment_risk * 0.10 + liability_risk * 0.10
    return {"final_risk_score": round(min(100, max(0, score)), 2), "components": {"credit": credit_risk, "dti": dti_risk, "anomaly": anomaly, "employment": employment_risk, "liability": liability_risk}}


def _exec_synthesize_decision(inputs: dict) -> dict:
    rs = inputs.get("final_risk_score", 50)
    cs = inputs.get("credit_score", 700)
    has_defaults = inputs.get("has_defaults", False)
    late = inputs.get("late_payments", 0)

    factors = []
    if cs >= 750: factors.append("Excellent credit score (750+)")
    elif cs >= 700: factors.append("Good credit score (700-749)")
    elif cs >= 650: factors.append("Fair credit score (650-699)")
    elif cs >= 600: factors.append("Poor credit score (600-649)")
    else: factors.append("Very poor credit score (<600)")

    dti = inputs.get("dti_ratio", 30)
    if dti <= 20: factors.append("Excellent debt-to-income ratio")
    elif dti <= 36: factors.append("Good debt-to-income ratio")
    elif dti <= 50: factors.append("Moderate debt-to-income ratio")
    else: factors.append("High debt-to-income ratio")

    if has_defaults: factors.append("Default accounts on record")
    if late > 3: factors.append("Multiple late payments")

    if rs < 30: decision, confidence = "APPROVED", 0.90
    elif rs < 60: decision, confidence = "REQUIRES_REVIEW", 0.70
    else: decision, confidence = "REJECTED", 0.95

    return {"decision": decision, "confidence_level": round(confidence, 2), "key_decision_factors": factors, "final_risk_score": rs}


def _exec_generate_explanation(inputs: dict) -> dict:
    decision = inputs.get("decision", "")
    factors = inputs.get("key_factors", [])
    rs = inputs.get("risk_score", 0)
    name = inputs.get("applicant_name", "Applicant")
    base = {"APPROVED": "Application approved based on strong financial profile and low risk indicators.", "REJECTED": "Application rejected due to significant credit risk factors.", "REQUIRES_REVIEW": "Application requires manual review due to mixed risk signals."}.get(decision, "")
    detail = f"{base} Risk score: {rs:.1f}/100. Key factors: {'; '.join(factors)}."
    return {"brief_explanation": base, "detailed_explanation": detail}


def _exec_create_case_record(inputs: dict) -> dict:
    from datetime import datetime
    import uuid
    case_id = f"CASE_{inputs.get('applicant_id', 'UNKNOWN')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    record = {
        "case_id": case_id,
        "applicant_id": inputs.get("applicant_id"),
        "decision": inputs.get("decision"),
        "risk_score": inputs.get("risk_score"),
        "confidence_level": inputs.get("confidence_level"),
        "key_factors": inputs.get("key_factors", []),
        "creation_timestamp": datetime.now().isoformat(),
        "status": "ACTIVE",
        "assigned_to": "AUTO_SYSTEM",
    }
    decisions_path = DATA_DIR / "decisions.json"
    with open(decisions_path) as f:
        data = json.load(f)
    data["decisions"].append(record)
    with open(decisions_path, "w") as f:
        json.dump(data, f, indent=2)
    return {"case_id": case_id, "status": "CREATED", "creation_timestamp": record["creation_timestamp"]}


def _exec_send_decision_notification(inputs: dict) -> dict:
    from datetime import datetime
    notif = {
        "notification_id": f"NOTIF_{inputs.get('applicant_id')}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "applicant_id": inputs.get("applicant_id"),
        "decision": inputs.get("decision"),
        "explanation": inputs.get("explanation", ""),
        "timestamp": datetime.now().isoformat(),
        "status": "SENT",
    }
    notif_path = DATA_DIR / "notifications.json"
    with open(notif_path) as f:
        data = json.load(f)
    data["notifications"].append(notif)
    with open(notif_path, "w") as f:
        json.dump(data, f, indent=2)
    return {"notification_id": notif["notification_id"], "status": "SENT"}


def _exec_log_compliance_action(inputs: dict) -> dict:
    from datetime import datetime
    return {"log_id": f"LOG_{inputs.get('case_id')}_{datetime.now().strftime('%H%M%S')}", "action": inputs.get("action"), "status": "LOGGED", "timestamp": datetime.now().isoformat()}


TOOL_EXECUTORS = {
    "get_applicant_profile": _exec_get_applicant_profile,
    "calculate_income_stability_score": _exec_calculate_income_stability_score,
    "evaluate_credit_history": _exec_evaluate_credit_history,
    "calculate_debt_to_income": _exec_calculate_debt_to_income,
    "detect_anomalies": _exec_detect_anomalies,
    "get_employment_risk_factor": _exec_get_employment_risk_factor,
    "calculate_final_risk_score": _exec_calculate_final_risk_score,
    "synthesize_decision": _exec_synthesize_decision,
    "generate_explanation": _exec_generate_explanation,
    "create_case_record": _exec_create_case_record,
    "send_decision_notification": _exec_send_decision_notification,
    "log_compliance_action": _exec_log_compliance_action,
}


def _call_claude_with_tools(prompt: str, tools: list, history: list) -> tuple[str, list, dict]:
    """Call Claude with a tool list. Runs the tool-use loop until Claude stops."""
    history.append({"role": "user", "content": prompt})
    tool_results = {}

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1000,
            tools=tools,
            messages=history,
        )
        # Collect assistant message
        assistant_content = response.content
        history.append({"role": "assistant", "content": assistant_content})

        if response.stop_reason == "tool_use":
            tool_results_content = []
            for block in assistant_content:
                if block.type == "tool_use":
                    executor = TOOL_EXECUTORS.get(block.name)
                    result = executor(block.input) if executor else {"error": f"unknown tool {block.name}"}
                    tool_results[block.name] = result
                    tool_results_content.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })
            history.append({"role": "user", "content": tool_results_content})
        else:
            # stop_reason == "end_turn" — extract final text
            text = next((b.text for b in assistant_content if hasattr(b, "text")), "")
            return text, history, tool_results


# ── LangGraph State ───────────────────────────────────────────────────────────

class GraphState(TypedDict):
    application: LoanApplication
    history: List[dict]
    tool_results: dict
    applicant_profile: Optional[dict]
    income_stability_score: Optional[float]
    credit_history: Optional[dict]
    dti_ratio: Optional[float]
    anomalies: Optional[List[str]]
    anomaly_risk_score: Optional[float]
    employment_risk_factor: Optional[float]
    final_risk_score: Optional[float]
    decision: Optional[str]
    confidence_level: Optional[float]
    key_decision_factors: Optional[List[str]]
    decision_explanation: Optional[str]
    case_id: Optional[str]
    notification_sent: Optional[bool]
    compliance_action: Optional[str]
    execution_log: List[str]
    errors: List[str]
    status: str


# ── LangGraph Node Functions ──────────────────────────────────────────────────

def node_profile_analysis(state: GraphState) -> GraphState:
    app = state["application"]
    history = state.get("history", [])
    log = state.get("execution_log", [])

    prompt = f"""You are an Applicant Profile Agent for a loan approval system.
Analyze the following applicant using the available tools:
- Applicant ID: {app.applicant_id}
- Name: {app.name}
- Age: {app.age}
- Annual Income: ${app.income:,.0f}
- Employment Type: {app.employment_type}
- Employment Years: {app.employment_years}
- Credit Score: {app.credit_score}
- Existing Liabilities: ${app.existing_liabilities:,.0f}
- Location: {app.location}
- Credit History: late_payments=0, default_accounts=0

Use get_applicant_profile, calculate_income_stability_score, and evaluate_credit_history tools.
Return a brief profile assessment."""

    try:
        text, history, tool_results = _call_claude_with_tools(prompt, APPLICANT_DB_TOOLS, history)
        profile = tool_results.get("get_applicant_profile", {})
        # Enrich with submitted data
        profile.update({
            "name": app.name, "age": app.age, "income": app.income,
            "employment_type": app.employment_type, "employment_years": app.employment_years,
            "credit_score": app.credit_score, "existing_liabilities": app.existing_liabilities,
            "location": app.location,
            "credit_history": {"accounts": 0, "accounts_in_good_standing": 0, "late_payments": 0, "default_accounts": 0},
        })
        stability = tool_results.get("calculate_income_stability_score", {})
        credit_hist = tool_results.get("evaluate_credit_history", {})
        log.append(f"[Profile Agent] {text}")
        return {**state, "history": history, "tool_results": tool_results, "applicant_profile": profile, "income_stability_score": stability.get("income_stability_score", 50), "credit_history": credit_hist, "execution_log": log, "status": "PROFILING"}
    except Exception as e:
        # Fallback — build profile from submitted data without LLM
        profile = {"applicant_id": app.applicant_id, "name": app.name, "age": app.age, "income": app.income, "employment_type": app.employment_type, "employment_years": app.employment_years, "credit_score": app.credit_score, "existing_liabilities": app.existing_liabilities, "location": app.location, "credit_history": {"accounts": 0, "accounts_in_good_standing": 0, "late_payments": 0, "default_accounts": 0}}
        stability = _exec_calculate_income_stability_score({"employment_type": app.employment_type, "employment_years": app.employment_years})
        log.append(f"[Profile Agent – fallback] API unavailable: {e}")
        return {**state, "history": history, "applicant_profile": profile, "income_stability_score": stability.get("income_stability_score", 50), "credit_history": {}, "execution_log": log, "status": "PROFILING"}


def node_risk_analysis(state: GraphState) -> GraphState:
    app = state["application"]
    profile = state.get("applicant_profile", {})
    history = state.get("history", [])
    log = state.get("execution_log", [])

    monthly_income = app.income / 12

    prompt = f"""You are a Financial Risk Analysis Agent.
Assess financial risk for this loan application using the available tools:
- Monthly Income: ${monthly_income:,.2f}
- Existing Liabilities: ${app.existing_liabilities:,.0f}
- Loan Amount: ${app.loan_amount:,.0f}
- Tenure: {app.tenure_months} months
- Employment Type: {app.employment_type}, Years: {app.employment_years}
- Credit Score: {app.credit_score}
- Late Payments: 0, Defaults: 0

Use calculate_debt_to_income, detect_anomalies, and get_employment_risk_factor tools.
Return a risk assessment summary."""

    try:
        text, history, tool_results = _call_claude_with_tools(prompt, RISK_RULES_TOOLS, history)
        dti_result = tool_results.get("calculate_debt_to_income", {})
        anomaly_result = tool_results.get("detect_anomalies", {})
        emp_result = tool_results.get("get_employment_risk_factor", {})
        log.append(f"[Risk Agent] {text}")
        return {**state, "history": history, "tool_results": {**state.get("tool_results", {}), **tool_results}, "dti_ratio": dti_result.get("dti_ratio", 30), "anomalies": anomaly_result.get("anomalies", []), "anomaly_risk_score": anomaly_result.get("anomaly_risk_score", 0), "employment_risk_factor": emp_result.get("employment_risk_factor", 0.1), "execution_log": log, "status": "RISK_ANALYSIS"}
    except Exception as e:
        dti = _exec_calculate_debt_to_income({"monthly_income": monthly_income, "existing_liabilities": app.existing_liabilities, "loan_amount": app.loan_amount, "tenure_months": app.tenure_months})
        emp = _exec_get_employment_risk_factor({"employment_type": app.employment_type, "employment_years": app.employment_years})
        log.append(f"[Risk Agent – fallback] API unavailable: {e}")
        return {**state, "history": history, "dti_ratio": dti.get("dti_ratio", 30), "anomalies": [], "anomaly_risk_score": 0, "employment_risk_factor": emp.get("employment_risk_factor", 0.1), "execution_log": log, "status": "RISK_ANALYSIS"}


def node_decision_making(state: GraphState) -> GraphState:
    app = state["application"]
    profile = state.get("applicant_profile", {})
    history = state.get("history", [])
    log = state.get("execution_log", [])

    dti = state.get("dti_ratio", 30) or 30
    anomaly_risk = state.get("anomaly_risk_score", 0) or 0
    emp_risk = state.get("employment_risk_factor", 0.1) or 0.1
    liability_ratio = app.existing_liabilities / app.loan_amount if app.loan_amount > 0 else 0

    prompt = f"""You are the Loan Decision Agent.
Make a final loan decision using the available tools:
- Credit Score: {app.credit_score}
- DTI Ratio: {dti:.2f}%
- Anomaly Risk Score: {anomaly_risk}
- Employment Risk Factor: {emp_risk}
- Liability Ratio: {liability_ratio:.2f}
- Has Defaults: false
- Late Payments: 0
- Applicant Name: {app.name}

Use calculate_final_risk_score first, then synthesize_decision, then generate_explanation.
Return final verdict with reasoning."""

    try:
        text, history, tool_results = _call_claude_with_tools(prompt, DECISION_TOOLS, history)
        risk_result = tool_results.get("calculate_final_risk_score", {})
        synth = tool_results.get("synthesize_decision", {})
        expl = tool_results.get("generate_explanation", {})
        log.append(f"[Decision Agent] {text}")
        return {
            **state,
            "history": history,
            "tool_results": {**state.get("tool_results", {}), **tool_results},
            "final_risk_score": risk_result.get("final_risk_score") or synth.get("final_risk_score", 50),
            "decision": synth.get("decision", "REQUIRES_REVIEW"),
            "confidence_level": synth.get("confidence_level", 0.70),
            "key_decision_factors": synth.get("key_decision_factors", []),
            "decision_explanation": expl.get("detailed_explanation", text),
            "execution_log": log,
            "status": "DECIDING",
        }
    except Exception as e:
        risk_result = _exec_calculate_final_risk_score({"credit_score": app.credit_score, "dti_ratio": dti, "anomaly_risk_score": anomaly_risk, "employment_risk_factor": emp_risk, "liability_ratio": liability_ratio})
        synth = _exec_synthesize_decision({"final_risk_score": risk_result["final_risk_score"], "credit_score": app.credit_score, "has_defaults": False, "late_payments": 0, "dti_ratio": dti, "anomaly_risk_score": anomaly_risk})
        expl = _exec_generate_explanation({"decision": synth["decision"], "key_factors": synth["key_decision_factors"], "risk_score": risk_result["final_risk_score"], "applicant_name": app.name})
        log.append(f"[Decision Agent – fallback] API unavailable: {e}")
        return {**state, "history": history, "final_risk_score": risk_result["final_risk_score"], "decision": synth["decision"], "confidence_level": synth["confidence_level"], "key_decision_factors": synth["key_decision_factors"], "decision_explanation": expl["detailed_explanation"], "execution_log": log, "status": "DECIDING"}


def node_compliance_action(state: GraphState) -> GraphState:
    app = state["application"]
    history = state.get("history", [])
    log = state.get("execution_log", [])

    decision = state.get("decision", "REQUIRES_REVIEW")
    risk_score = state.get("final_risk_score", 50)
    confidence = state.get("confidence_level", 0.70)
    factors = state.get("key_decision_factors", [])
    explanation = state.get("decision_explanation", "")

    prompt = f"""You are the Compliance & Action Orchestrator Agent.
Complete the post-decision compliance workflow using the available tools:
- Applicant ID: {app.applicant_id}
- Decision: {decision}
- Risk Score: {risk_score:.1f}/100
- Confidence: {confidence:.0%}
- Key Factors: {', '.join(factors)}
- Explanation: {explanation[:200]}

Use create_case_record first, then send_decision_notification, then log_compliance_action.
Confirm all compliance actions completed."""

    try:
        text, history, tool_results = _call_claude_with_tools(prompt, COMPLIANCE_TOOLS, history)
        case_result = tool_results.get("create_case_record", {})
        notif_result = tool_results.get("send_decision_notification", {})
        log.append(f"[Compliance Agent] {text}")
        return {**state, "history": history, "tool_results": {**state.get("tool_results", {}), **tool_results}, "case_id": case_result.get("case_id"), "notification_sent": notif_result.get("status") == "SENT", "compliance_action": f"Case created: {case_result.get('case_id', 'N/A')}, Notification: {notif_result.get('status', 'N/A')}", "execution_log": log, "status": "COMPLETED"}
    except Exception as e:
        case_result = _exec_create_case_record({"applicant_id": app.applicant_id, "decision": decision, "risk_score": risk_score, "confidence_level": confidence, "key_factors": factors})
        notif_result = _exec_send_decision_notification({"applicant_id": app.applicant_id, "decision": decision, "explanation": explanation})
        log.append(f"[Compliance Agent – fallback] API unavailable: {e}")
        return {**state, "history": history, "case_id": case_result.get("case_id"), "notification_sent": True, "compliance_action": f"Case: {case_result.get('case_id')}, Notification: SENT", "execution_log": log, "status": "COMPLETED"}


def node_should_continue(state: GraphState) -> str:
    if state.get("status") == "FAILED":
        return END
    return "continue"


# ── Build LangGraph ───────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(GraphState)
    graph.add_node("profile_analysis", node_profile_analysis)
    graph.add_node("risk_analysis", node_risk_analysis)
    graph.add_node("decision_making", node_decision_making)
    graph.add_node("compliance_action", node_compliance_action)

    graph.set_entry_point("profile_analysis")
    graph.add_edge("profile_analysis", "risk_analysis")
    graph.add_edge("risk_analysis", "decision_making")
    graph.add_edge("decision_making", "compliance_action")
    graph.add_edge("compliance_action", END)

    return graph.compile()


_compiled_graph = None

def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


# ── Public orchestrator class (keeps API surface unchanged) ──────────────────

class LoanApplicationOrchestrator:
    def __init__(self):
        self.model = MODEL

    def orchestrate(self, application: LoanApplication) -> ApplicationState:
        graph = get_graph()

        initial_state: GraphState = {
            "application": application,
            "history": [],
            "tool_results": {},
            "applicant_profile": None,
            "income_stability_score": None,
            "credit_history": None,
            "dti_ratio": None,
            "anomalies": None,
            "anomaly_risk_score": None,
            "employment_risk_factor": None,
            "final_risk_score": None,
            "decision": None,
            "confidence_level": None,
            "key_decision_factors": None,
            "decision_explanation": None,
            "case_id": None,
            "notification_sent": None,
            "compliance_action": None,
            "execution_log": [],
            "errors": [],
            "status": "INITIALIZED",
        }

        try:
            final_state = graph.invoke(initial_state)
        except Exception as e:
            # Graph-level failure — run fallback chain directly
            s = initial_state.copy()
            s["errors"] = [str(e)]
            try:
                s = node_profile_analysis(s)
                s = node_risk_analysis(s)
                s = node_decision_making(s)
                s = node_compliance_action(s)
            except Exception as e2:
                s["status"] = "FAILED"
                s["errors"].append(str(e2))
            final_state = s

        # Map GraphState → ApplicationState
        app_state = ApplicationState(application=application)
        app_state.applicant_profile = final_state.get("applicant_profile")
        app_state.income_stability_score = final_state.get("income_stability_score")
        app_state.credit_history = final_state.get("credit_history")
        app_state.application_complete = True
        app_state.dti_ratio = final_state.get("dti_ratio")
        app_state.anomalies_detected = final_state.get("anomalies", [])
        app_state.anomaly_risk_score = final_state.get("anomaly_risk_score")
        app_state.employment_risk_factor = final_state.get("employment_risk_factor")
        app_state.final_risk_score = final_state.get("final_risk_score")
        app_state.decision = final_state.get("decision")
        app_state.confidence_level = final_state.get("confidence_level")
        app_state.key_decision_factors = final_state.get("key_decision_factors")
        app_state.decision_explanation = final_state.get("decision_explanation")
        app_state.case_id = final_state.get("case_id")
        app_state.notification_sent = final_state.get("notification_sent")
        app_state.compliance_action = final_state.get("compliance_action")
        app_state.execution_log = final_state.get("execution_log", [])
        app_state.errors = final_state.get("errors", [])
        app_state.status = final_state.get("status", "COMPLETED")

        return app_state
