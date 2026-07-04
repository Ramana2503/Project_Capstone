# Multi-Agent Agentic AI Loan Approval System

An end-to-end loan application analysis system using a multi-agent architecture powered by Claude AI. The system automates loan decisions while providing explainability and auditability.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit UI Layer                      │
│            (Loan Application & Status Tracking)             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Microservices                      │
│           (REST Endpoints, Request Validation)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Orchestration Layer (Orchestrator)             │
│         (Claude-powered decision coordination)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────────┐
│  Profile    │ │ Risk        │ │ Decision        │
│  Analysis   │ │ Analysis    │ │ Synthesis       │
└─────┬───────┘ └────┬────────┘ └────────┬────────┘
      │               │                  │
      ▼               ▼                  ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────────┐
│Applicant DB │ │Risk Rules   │ │Compliance &     │
│ (MCP Server)│ │(MCP Server) │ │Action System    │
│             │ │             │ │(MCP Server)     │
└─────────────┘ └─────────────┘ └─────────────────┘
      │               │                  │
      └───────────────┼──────────────────┘
                      ▼
        ┌──────────────────────────────┐
        │   Data Layer (JSON Files)    │
        │ - mock_applicants.json       │
        │ - mock_risk_rules.json       │
        │ - decisions.json             │
        │ - notifications.json         │
        └──────────────────────────────┘
```

## System Components

### 1. **Presentation Layer** - Streamlit UI
- Loan application form with applicant selection
- Real-time status tracking
- Decision display with explanations
- Application history

### 2. **API Layer** - FastAPI Microservices
- `POST /submit-loan` - Submit loan application
- `GET /loan-status/{application_id}` - Check application status
- `GET /applications/` - List all applications
- `GET /health` - Health check

### 3. **Orchestration Layer** - Claude-Powered Orchestrator
- Multi-stage decision workflow:
  1. **Applicant Profile Analysis** - Income stability, employment risk
  2. **Financial Risk Analysis** - DTI ratio, credit score, anomalies
  3. **Loan Decision Making** - Final decision synthesis
  4. **Compliance & Action** - Notifications and audit logging

### 4. **Agent Layer** - MCP Servers (Tool Providers)
- **ApplicantDB Server** - Applicant profile and credit history lookup
- **RiskRulesDB Server** - Risk calculation and anomaly detection
- **DecisionSynthesis Server** - Decision logic and risk scoring
- **NotificationSystem Server** - Audit logging and notifications

### 5. **Data Layer** - Mock Databases
- Applicant profiles with financial information
- Risk rules and thresholds
- Decision audit trail
- Notification logs

## Getting Started

### Prerequisites
- Python 3.8+
- Anthropic API key
- FastAPI
- Streamlit
- LangChain/LangGraph

### Installation

1. **Clone/Setup Project**
```bash
cd /home/ubuntu/Desktop/Capstone_01
```

2. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure Environment**
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Running the System

#### Option 1: Run All Services with Script
```bash
chmod +x scripts/start_services.sh
./scripts/start_services.sh
```

#### Option 2: Run Manually

**Terminal 1 - Start API Server:**
```bash
python -m uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Start Streamlit UI:**
```bash
streamlit run ui/streamlit_app.py --server.port=8501
```

### Access the Application

- **Streamlit UI:** http://localhost:8501
- **API Documentation:** http://localhost:8000/docs
- **API Health Check:** http://localhost:8000/health

## Usage Example

### 1. Submit Loan Application
```bash
curl -X POST "http://localhost:8000/submit-loan" \
  -H "Content-Type: application/json" \
  -d "{
    \"applicant_id\": \"APP001\",
    \"loan_amount\": 100000,
    \"tenure_months\": 60
  }"
```

Response:
```json
{
  "application_id": "APP_a1b2c3d4",
  "applicant_id": "APP001",
  "status": "PROCESSING",
  "timestamp": "2024-01-15T10:30:00"
}
```

### 2. Check Application Status
```bash
curl "http://localhost:8000/loan-status/APP_a1b2c3d4"
```

Response:
```json
{
  "application_id": "APP_a1b2c3d4",
  "applicant_id": "APP001",
  "status": "COMPLETED",
  "decision": "APPROVED",
  "risk_score": 22.5,
  "confidence_level": 0.92,
  "key_factors": [
    "Excellent credit score (750+)",
    "Good debt-to-income ratio",
    "Stable employment"
  ]
}
```

## Decision Logic

### Risk Score Calculation (0-100)
- **Credit Score Risk** (35% weight) - Credit score based risk assessment
- **DTI Risk** (25% weight) - Debt-to-income ratio analysis
- **Anomaly Risk** (20% weight) - Late payments, defaults, unusual patterns
- **Employment Risk** (10% weight) - Employment type and stability
- **Liability Risk** (10% weight) - Existing liabilities assessment

### Decision Rules
| Risk Score | Decision | Action |
|-----------|----------|--------|
| < 25 | APPROVED | Process immediately |
| 25-50 | APPROVED/REVIEW | Based on factors |
| 50-75 | REQUIRES_REVIEW | Schedule manual review |
| > 75 | REJECTED | Prepare rejection letter |

## Mock Data

### Available Test Applicants
1. **APP001 - John Smith** (Likely Approval)
   - Credit Score: 750, Income: $75k, Employment: Full-time (5 yrs)

2. **APP002 - Sarah Johnson** (Mixed Profile)
   - Credit Score: 620, Income: $45k, Employment: Contract (1 yr)

3. **APP003 - Mike Davis** (Strong Profile)
   - Credit Score: 800, Income: $120k, Employment: Self-employed (8 yrs)

4. **APP004 - Emma Wilson** (Likely Rejection)
   - Credit Score: 580, Income: $85k, Employment: Full-time (10 yrs), 1 default

5. **APP005 - Robert Brown** (Good Profile)
   - Credit Score: 700, Income: $65k, Employment: Full-time (3 yrs)

## Project Structure

```
Capstone_01/
├── api/
│   ├── app.py                 # FastAPI application
│   ├── schemas.py             # Pydantic models
│   └── validators.py          # Input validation
├── agents/
│   ├── orchestrator.py        # Main orchestration engine
│   └── mcp_servers/
│       ├── applicant_db_server.py
│       ├── risk_rules_server.py
│       ├── decision_synthesis_server.py
│       └── notification_server.py
├── orchestration/
│   ├── state.py               # Application state schema
│   └── routing.py             # Decision routing logic
├── ui/
│   ├── streamlit_app.py       # Main Streamlit application
│   └── components.py          # Reusable components
├── data/
│   ├── mock_applicants.json   # Applicant profiles
│   ├── mock_risk_rules.json   # Risk rules and thresholds
│   ├── decisions.json         # Decision audit log
│   └── notifications.json     # Notification logs
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
└── README.md                  # This file
```

## Features

✅ **Automated Decision Making** - Claude AI-powered loan analysis
✅ **Multi-Stage Workflow** - Profile, Risk, Decision, Compliance stages
✅ **Explainable Decisions** - Detailed reasoning for each decision
✅ **Audit Trail** - Complete case history and decision logs
✅ **Real-time Status Tracking** - Check application status anytime
✅ **Scalable Architecture** - Loosely coupled microservices
✅ **Mock Data Support** - Built-in test data for demos
✅ **REST API** - Full API documentation with Swagger UI
✅ **User-Friendly UI** - Streamlit-based chatbot interface

## Testing

### Test with Sample Applicants
1. Open Streamlit UI (http://localhost:8501)
2. Select "Submit Application"
3. Choose an applicant from the dropdown
4. Enter loan amount and tenure
5. Submit and check status

### Test Different Scenarios
- **APP001 (John Smith)** - Expected: APPROVED
- **APP002 (Sarah Johnson)** - Expected: REQUIRES_REVIEW
- **APP003 (Mike Davis)** - Expected: APPROVED
- **APP004 (Emma Wilson)** - Expected: REJECTED
- **APP005 (Robert Brown)** - Expected: APPROVED

## API Response Examples

### Approved Application
```json
{
  "decision": "APPROVED",
  "risk_score": 18.5,
  "confidence_level": 0.94,
  "key_factors": [
    "Excellent credit score (750+)",
    "Good debt-to-income ratio",
    "Stable full-time employment (5 years)"
  ]
}
```

### Rejected Application
```json
{
  "decision": "REJECTED",
  "risk_score": 82.3,
  "confidence_level": 0.89,
  "key_factors": [
    "Critical credit score (<600)",
    "Applicant has defaulted accounts",
    "High debt-to-income ratio"
  ]
}
```

### Manual Review Required
```json
{
  "decision": "REQUIRES_REVIEW",
  "risk_score": 48.5,
  "confidence_level": 0.72,
  "key_factors": [
    "Fair credit score (650-699)",
    "History of late payments",
    "Moderate debt-to-income ratio"
  ]
}
```

## Performance Considerations

- API typically processes requests in 2-5 seconds
- Claude API calls handle profile and risk analysis
- Background task processing for non-blocking submissions
- JSON-based state persistence for simplicity
- Can be scaled to production with PostgreSQL/MongoDB

## Future Enhancements

- [ ] Implement LangGraph state machine for formal workflow
- [ ] Add WebSocket for real-time decision updates
- [ ] Integration with real credit bureaus
- [ ] Machine learning model for risk prediction
- [ ] Database persistence (PostgreSQL/MongoDB)
- [ ] User authentication and authorization
- [ ] Advanced analytics dashboard
- [ ] Decision appeal workflow
- [ ] Integration with notification services (email, SMS)
- [ ] Batch processing for bulk applications

## Troubleshooting

### API Connection Error
```
Error: Cannot connect to API. Make sure the server is running on http://localhost:8000
```
**Solution:** Start the API server with `python -m uvicorn api.app:app --reload`

### Applicant Not Found
```
Error: Applicant APP001 not found
```
**Solution:** Use valid applicant IDs from mock_applicants.json (APP001-APP005)

### Missing API Key
```
Error: ANTHROPIC_API_KEY not set
```
**Solution:** Set your API key in .env file or as environment variable

### Port Already in Use
```
Error: Address already in use
```
**Solution:** Kill existing process or use different port:
```bash
python -m uvicorn api.app:app --reload --port 8001
```

## Support & Documentation

For more information:
- Claude API Documentation: https://docs.anthropic.com
- FastAPI Documentation: https://fastapi.tiangolo.com
- Streamlit Documentation: https://docs.streamlit.io
- LangGraph Documentation: https://langchain-ai.github.io/langgraph/

## License

This project is part of the Capstone 01 series.

## Authors

Built as a demonstration of multi-agent AI systems for loan application analysis.
