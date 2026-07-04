import json
from pathlib import Path
from fastmcp.server import Server
from datetime import datetime

app = Server("NotificationSystem")

DATA_DIR = Path(__file__).parent.parent.parent / "data"

def load_notifications():
    with open(DATA_DIR / "notifications.json") as f:
        return json.load(f)

def save_notifications(data):
    with open(DATA_DIR / "notifications.json", "w") as f:
        json.dump(data, f, indent=2)

def load_decisions():
    with open(DATA_DIR / "decisions.json") as f:
        return json.load(f)

def save_decisions(data):
    with open(DATA_DIR / "decisions.json", "w") as f:
        json.dump(data, f, indent=2)

@app.call_tool()
def send_decision_notification(
    applicant_id: str,
    decision: str,
    explanation: str,
    email: str,
    phone: str
) -> dict:
    """Send notification about loan decision to applicant"""
    notification = {
        "notification_id": f"NOTIF_{applicant_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "applicant_id": applicant_id,
        "decision": decision,
        "notification_type": "DECISION_NOTIFICATION",
        "email": email,
        "phone": phone,
        "timestamp": datetime.now().isoformat(),
        "status": "SENT"
    }

    notifications = load_notifications()
    notifications["notifications"].append(notification)
    save_notifications(notifications)

    return {
        "success": True,
        "notification_id": notification["notification_id"],
        "applicant_id": applicant_id,
        "decision": decision,
        "notification_sent_to_email": email,
        "notification_sent_to_phone": phone,
        "timestamp": notification["timestamp"],
        "status": "SENT"
    }

@app.call_tool()
def create_case_record(
    applicant_id: str,
    decision: str,
    risk_score: float,
    confidence_level: float,
    key_factors: list
) -> dict:
    """Create formal case record and audit log"""
    case_id = f"CASE_{applicant_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    case_record = {
        "case_id": case_id,
        "applicant_id": applicant_id,
        "decision": decision,
        "risk_score": risk_score,
        "confidence_level": confidence_level,
        "key_factors": key_factors,
        "creation_timestamp": datetime.now().isoformat(),
        "status": "ACTIVE",
        "assigned_to": "AUTO_SYSTEM"
    }

    decisions = load_decisions()
    decisions["decisions"].append(case_record)
    save_decisions(decisions)

    return {
        "success": True,
        "case_id": case_id,
        "applicant_id": applicant_id,
        "case_status": "CREATED",
        "creation_timestamp": case_record["creation_timestamp"]
    }

@app.call_tool()
def log_compliance_action(
    case_id: str,
    action: str,
    action_details: dict
) -> dict:
    """Log compliance and audit actions"""
    log_entry = {
        "log_id": f"LOG_{case_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "case_id": case_id,
        "action": action,
        "action_details": action_details,
        "timestamp": datetime.now().isoformat(),
        "status": "LOGGED"
    }

    return {
        "success": True,
        "log_id": log_entry["log_id"],
        "case_id": case_id,
        "action": action,
        "timestamp": log_entry["timestamp"],
        "compliance_status": "COMPLIANT"
    }

@app.call_tool()
def get_case_status(case_id: str) -> dict:
    """Retrieve status of a specific case"""
    decisions = load_decisions()

    for case in decisions["decisions"]:
        if case["case_id"] == case_id:
            return {
                "success": True,
                "case_id": case_id,
                "applicant_id": case["applicant_id"],
                "decision": case["decision"],
                "risk_score": case["risk_score"],
                "confidence_level": case["confidence_level"],
                "status": case["status"],
                "creation_timestamp": case["creation_timestamp"]
            }

    return {"success": False, "error": f"Case {case_id} not found"}

@app.call_tool()
def escalate_case(case_id: str, escalation_reason: str) -> dict:
    """Escalate case to manual review team"""
    decisions = load_decisions()

    for case in decisions["decisions"]:
        if case["case_id"] == case_id:
            case["status"] = "ESCALATED"
            case["escalation_reason"] = escalation_reason
            case["escalated_timestamp"] = datetime.now().isoformat()
            case["assigned_to"] = "MANUAL_REVIEW_TEAM"
            save_decisions(decisions)

            return {
                "success": True,
                "case_id": case_id,
                "escalation_status": "ESCALATED",
                "assigned_to": "MANUAL_REVIEW_TEAM",
                "escalation_timestamp": case["escalated_timestamp"]
            }

    return {"success": False, "error": f"Case {case_id} not found"}

@app.call_tool()
def generate_decision_summary(applicant_id: str, case_id: str) -> dict:
    """Generate comprehensive decision summary for record"""
    decisions = load_decisions()

    for case in decisions["decisions"]:
        if case["case_id"] == case_id:
            summary = f"""
LOAN DECISION SUMMARY
====================
Case ID: {case_id}
Applicant ID: {applicant_id}
Decision: {case["decision"]}
Risk Score: {case["risk_score"]}/100
Confidence: {case["confidence_level"]:.0%}
Timestamp: {case["creation_timestamp"]}

Key Factors Considered:
"""
            for i, factor in enumerate(case["key_factors"], 1):
                summary += f"{i}. {factor}\n"

            return {
                "success": True,
                "case_id": case_id,
                "applicant_id": applicant_id,
                "summary": summary,
                "summary_generated_at": datetime.now().isoformat()
            }

    return {"success": False, "error": f"Case {case_id} not found"}
