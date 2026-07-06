import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from api.schemas import LoanApplicationRequest, LoanApplicationResponse, ApplicationStatusResponse, HealthResponse
from orchestration.state import LoanApplication
from agents.orchestrator import LoanApplicationOrchestrator

app = FastAPI(
    title="Loan Application AI System",
    description="Multi-Agent Agentic AI for loan application analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent.parent / "data"
APPLICATIONS_DIR = DATA_DIR / "applications"
APPLICATIONS_DIR.mkdir(exist_ok=True)

orchestrator = LoanApplicationOrchestrator()

def save_application_state(application_id: str, state_dict: dict):
    """Save application state to file"""
    filepath = APPLICATIONS_DIR / f"{application_id}.json"
    with open(filepath, "w") as f:
        json.dump(state_dict, f, indent=2)

def load_application_state(application_id: str) -> dict:
    """Load application state from file"""
    filepath = APPLICATIONS_DIR / f"{application_id}.json"
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return None

def process_application(application_id: str, loan_application: LoanApplication):
    """Background task to process loan application"""
    state = orchestrator.orchestrate(loan_application)
    save_application_state(application_id, state.to_dict())

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )

@app.post("/submit-loan", response_model=LoanApplicationResponse)
async def submit_loan_application(request: LoanApplicationRequest, background_tasks: BackgroundTasks):
    """
    Submit a loan application for processing.
    Returns immediately with application_id and status.
    Processing happens in background.
    """
    try:
        # Create application
        application_id = f"APP_{str(uuid.uuid4())[:8]}"
        app_timestamp = request.application_timestamp or datetime.now().isoformat()
        loan_app = LoanApplication(
            applicant_id=request.applicant_id,
            name=request.name,
            age=request.age,
            income=request.income,
            employment_type=request.employment_type,
            employment_years=request.employment_years,
            credit_score=request.credit_score,
            existing_liabilities=request.existing_liabilities,
            location=request.location,
            late_payments=request.late_payments,
            default_accounts=request.default_accounts,
            loan_amount=request.loan_amount,
            tenure_months=request.tenure_months,
            timestamp=app_timestamp,
        )

        # Create initial state
        initial_state = {
            "application": {
                "application_id": application_id,
                "applicant_id": request.applicant_id,
                "name": request.name,
                "age": request.age,
                "income": request.income,
                "employment_type": request.employment_type,
                "employment_years": request.employment_years,
                "credit_score": request.credit_score,
                "existing_liabilities": request.existing_liabilities,
                "location": request.location,
                "late_payments": request.late_payments,
                "default_accounts": request.default_accounts,
                "loan_amount": request.loan_amount,
                "tenure_months": request.tenure_months,
                "timestamp": app_timestamp,
            },
            "status": "PROCESSING",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # Save initial state
        save_application_state(application_id, initial_state)

        # Queue background processing
        background_tasks.add_task(process_application, application_id, loan_app)

        return LoanApplicationResponse(
            application_id=application_id,
            applicant_id=request.applicant_id,
            status="PROCESSING",
            decision=None,
            risk_score=None,
            confidence_level=None,
            explanation="Application submitted for processing",
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/loan-status/{application_id}", response_model=ApplicationStatusResponse)
async def get_application_status(application_id: str):
    """Get status of a submitted loan application"""
    try:
        state = load_application_state(application_id)
        if not state:
            raise HTTPException(status_code=404, detail=f"Application {application_id} not found")

        return ApplicationStatusResponse(
            application_id=application_id,
            applicant_id=state["application"]["applicant_id"],
            status=state.get("status", "UNKNOWN"),
            decision=state.get("decision"),
            risk_score=state.get("final_risk_score"),
            confidence_level=state.get("confidence_level"),
            key_factors=state.get("key_decision_factors"),
            explanation=state.get("decision_explanation"),
            created_at=state.get("created_at", ""),
            updated_at=state.get("updated_at", "")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/applications/", response_model=dict)
async def list_applications():
    """List all applications"""
    try:
        applications = []
        for filepath in APPLICATIONS_DIR.glob("*.json"):
            with open(filepath) as f:
                app_state = json.load(f)
                applications.append({
                    "application_id": filepath.stem,
                    "applicant_id": app_state["application"]["applicant_id"],
                    "status": app_state.get("status"),
                    "decision": app_state.get("decision"),
                    "created_at": app_state.get("created_at")
                })

        return {"total": len(applications), "applications": applications}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
