# Multi-Agent Agentic AI Loan Application System - Architecture Guide

## System Overview

This document provides a detailed architecture guide for the Multi-Agent Agentic AI Loan Application System. It explains how all components interact to process loan applications and make automated decisions.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE LAYER                      │
│                     Streamlit Web Application                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Page 1: Submit Application  │  Page 2: Check Status    │  │
│  │  • Select Applicant          │  • Enter Application ID   │  │
│  │  • Enter Loan Details        │  • View Decision          │  │
│  │  • Submit & Get ID           │  • View Risk Score        │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────┬──────────────────────────────────────────┘
                        │ HTTP REST API
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MICROSERVICES API LAYER                       │
│                  FastAPI REST Endpoints                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ POST /submit-loan            → Submit application       │  │
│  │ GET /loan-status/{id}        → Check status            │  │
│  │ GET /applications/           → List all apps           │  │
│  │ GET /health                  → Health check            │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────┬──────────────────────────────────────────┘
                        │ Python Objects
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                  ORCHESTRATION LAYER (Core Engine)              │
│               LoanApplicationOrchestrator (Claude)              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Multi-Stage Workflow:                                   │  │
│  │ 1. Initialize → Load applicant data                     │  │
│  │ 2. Profile Analysis → Evaluate income & employment     │  │
│  │ 3. Risk Analysis → Calculate DTI, anomalies            │  │
│  │ 4. Decision Making → Final decision & risk score       │  │
│  │ 5. Save State → Persist results                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────┬──────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
    ┌────────┐   ┌──────────┐   ┌────────────┐
    │Claude  │   │Business  │   │State       │
    │API     │   │Rules     │   │Persistence│
    │(LLM)   │   │Engine    │   │(JSON)     │
    └────────┘   └──────────┘   └────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT LAYER (MCP Servers)                  │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐ │
│  │ ApplicantDB    │  │ RiskRulesDB    │  │ DecisionSynthesis│ │
│  │ Server         │  │ Server         │  │ Server           │ │
│  │ • get_profile  │  │ • calc_dti     │  │ • synthesize     │ │
│  │ • get_income   │  │ • get_risk     │  │ • calc_risk      │ │
│  │ • get_history  │  │ • detect_anom  │  │ • generate_exp   │ │
│  └────────────────┘  └────────────────┘  └──────────────────┘ │
│  ┌──────────────────────────────────┐                          │
│  │ NotificationSystem Server        │                          │
│  │ • create_case_record             │                          │
│  │ • send_notification              │                          │
│  │ • log_compliance_action          │                          │
│  └──────────────────────────────────┘                          │
└───────────────────────┬──────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER (Persistence)                   │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐ │
│  │ Applicants     │  │ Rules & Risk   │  │ Decisions & Logs │ │
│  │ mock_applicants│  │ mock_risk_rules│  │ decisions.json   │ │
│  │ .json (5 test) │  │ .json          │  │ notifications.json
│  │                │  │                │  │                  │ │
│  │ • Profiles     │  │ • Thresholds   │  │ • Case Records   │ │
│  │ • Credit Info  │  │ • Risk Factors │  │ • Audit Trail    │ │
│  │ • Employment   │  │ • Approval Rls │  │ • Notifications  │ │
│  └────────────────┘  └────────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. User Interface Layer (Streamlit)

**File:** `ui/streamlit_app.py`

**Functionality:**
- Multi-page web interface
- Application submission form
- Real-time status tracking
- Application history

**Pages:**
- **Submit Application:** Form to submit loan applications
- **Check Status:** Query status by application ID
- **View All Applications:** List all submitted applications

**Key Features:**
- Pre-populated applicant selector
- Loan amount and tenure inputs
- Real-time risk score visualization
- Decision status with icons
- Raw JSON data inspection

### 2. Microservices API Layer (FastAPI)

**File:** `api/app.py`

**Endpoints:**

```
POST /submit-loan
├─ Request: {applicant_id, loan_amount, tenure_months}
├─ Processing: Background task
└─ Response: {application_id, status: "PROCESSING"}

GET /loan-status/{application_id}
├─ Processing: Load state from file
└─ Response: {decision, risk_score, confidence_level, factors}

GET /applications/
├─ Processing: Scan application files
└─ Response: {total, [applications]}

GET /health
└─ Response: {status, version, timestamp}
```

**Design Patterns:**
- RESTful API design
- Background task processing (non-blocking)
- CORS enabled for web UI
- Pydantic validation
- JSON file persistence

### 3. Orchestration Layer (Claude Agent)

**File:** `agents/orchestrator.py`

**Core Component:** `LoanApplicationOrchestrator`

**Workflow Stages:**

#### Stage 1: Profile Analysis
- Load applicant profile from mock database
- Calculate income stability score
- Evaluate credit history
- Check application completeness
- **Claude Interaction:** Analyze employment and income stability

#### Stage 2: Financial Risk Analysis
- Calculate Debt-to-Income (DTI) ratio
- Determine credit score risk level
- Analyze loan amount risk
- Detect anomalies (late payments, defaults)
- **Claude Interaction:** Provide risk assessment with concerns

#### Stage 3: Decision Making
- Aggregate all risk components with weighted scoring:
  - Credit Score Risk: 35%
  - DTI Risk: 25%
  - Anomaly Risk: 20%
  - Employment Risk: 10%
  - Liability Risk: 10%
- **Claude Interaction:** Make final decision (APPROVED/REJECTED/REQUIRES_REVIEW)
- Generate confidence score

**State Management:**

**File:** `orchestration/state.py`

- `ApplicationState` dataclass tracks all processing stages
- Input parameters → Profile data → Risk metrics → Final decision
- Maintains execution log for auditability

### 4. Agent Layer (MCP Servers)

**MCP (Model Context Protocol) Servers** act as tool providers for agents.

#### 4.1 ApplicantDB Server
**File:** `agents/mcp_servers/applicant_db_server.py`

**Tools:**
- `get_applicant_profile(applicant_id)` → Full profile
- `calculate_income_stability_score(applicant_id)` → Income score (0-100)
- `evaluate_credit_history(applicant_id)` → Credit assessment
- `check_completeness(applicant_id, loan_amount, tenure)` → Validation

**Data Source:** `data/mock_applicants.json`

#### 4.2 RiskRulesDB Server
**File:** `agents/mcp_servers/risk_rules_server.py`

**Tools:**
- `calculate_debt_to_income(applicant_id, loan_amount, tenure_months)` → DTI%
- `get_credit_score_risk_level(credit_score)` → Risk category
- `analyze_loan_amount_risk(applicant_id, loan_amount)` → Loan risk
- `detect_anomalies(...)` → Anomaly detection with risk score
- `get_employment_risk_factor(employment_type, years)` → Employment risk

**Data Source:** `data/mock_risk_rules.json`

#### 4.3 DecisionSynthesis Server
**File:** `agents/mcp_servers/decision_synthesis_server.py`

**Tools:**
- `synthesize_decision(...)` → Final decision + confidence
- `generate_explanation(decision, factors, risk_score)` → Decision explanation
- `calculate_final_risk_score(...)` → Weighted risk aggregation

#### 4.4 NotificationSystem Server
**File:** `agents/mcp_servers/notification_server.py`

**Tools:**
- `send_decision_notification(...)` → Send decision to applicant
- `create_case_record(...)` → Create formal case record
- `log_compliance_action(...)` → Log compliance action
- `get_case_status(case_id)` → Retrieve case status
- `escalate_case(case_id, reason)` → Escalate for manual review
- `generate_decision_summary(...)` → Generate summary report

**Data Sources:** `data/decisions.json`, `data/notifications.json`

### 5. Data Layer (JSON Persistence)

#### 5.1 Mock Applicants
**File:** `data/mock_applicants.json`

```json
{
  "applicants": {
    "APP001": {
      "applicant_id": "APP001",
      "name": "John Smith",
      "age": 35,
      "income": 75000,
      "employment_type": "Full-time",
      "employment_years": 5,
      "credit_score": 750,
      "existing_liabilities": 15000,
      "location": "New York",
      "credit_history": {...}
    }
    // ... 4 more applicants
  }
}
```

#### 5.2 Mock Risk Rules
**File:** `data/mock_risk_rules.json`

Contains:
- Credit score thresholds (very_poor → excellent)
- DTI thresholds
- Employment risk multipliers
- Stability factors
- Approval/rejection rules

#### 5.3 Decisions Audit Log
**File:** `data/decisions.json`

Stores all decision records with:
- Case ID
- Applicant ID
- Decision and risk score
- Confidence level
- Key factors
- Timestamps

#### 5.4 Application State Files
**Directory:** `data/applications/`

Each submitted application creates `{application_id}.json`:
```json
{
  "application": {...},
  "status": "COMPLETED",
  "decision": "APPROVED",
  "risk_score": 22.5,
  "confidence_level": 0.92,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:35:00"
}
```

## Data Flow

### Loan Application Processing Flow

```
1. USER SUBMITS APPLICATION (Streamlit)
   │
   ├─ Input: {applicant_id, loan_amount, tenure_months}
   │
   ▼
2. API RECEIVES REQUEST (FastAPI)
   │
   ├─ Validation: Check applicant exists
   ├─ Generation: Create unique application_id
   ├─ Storage: Save initial state
   ├─ Response: Return application_id (non-blocking)
   │
   ▼
3. BACKGROUND PROCESSING STARTS
   │
   ├─ Orchestrator receives LoanApplication object
   │
   ▼
4. STAGE 1: PROFILE ANALYSIS
   │
   ├─ Load applicant from ApplicantDB
   ├─ Claude analyzes: "Assess this applicant's employment stability..."
   ├─ Store: applicant_profile, income_stability_score
   │
   ▼
5. STAGE 2: FINANCIAL RISK ANALYSIS
   │
   ├─ Calculate DTI using RiskRulesDB
   ├─ Detect anomalies
   ├─ Claude analyzes: "Assess financial risk for this loan..."
   ├─ Store: dti_ratio, anomalies_detected, anomaly_risk_score
   │
   ▼
6. STAGE 3: DECISION MAKING
   │
   ├─ Calculate weighted risk score
   ├─ Claude decides: "Based on all factors, decide APPROVED/REJECTED/REQUIRES_REVIEW"
   ├─ Generate confidence level
   ├─ Store: decision, final_risk_score, confidence_level, key_factors
   │
   ▼
7. STAGE 4: COMPLIANCE & ACTION
   │
   ├─ Create case record (NotificationSystem)
   ├─ Log decision
   ├─ Trigger notification
   │
   ▼
8. STATE PERSISTENCE
   │
   ├─ Save complete state to data/applications/{application_id}.json
   ├─ Update decisions.json audit log
   │
   ▼
9. USER CHECKS STATUS (Streamlit)
   │
   ├─ Query: GET /loan-status/{application_id}
   ├─ API: Load state from file
   ├─ Display: decision, risk_score, confidence, factors
```

## Decision Algorithm

### Risk Score Calculation

```
Total Risk Score = (
  credit_risk * 0.35 +
  dti_risk * 0.25 +
  anomaly_risk * 0.20 +
  employment_risk * 0.10 +
  liability_risk * 0.10
) → Normalized to 0-100

Where:
- credit_risk: Based on credit score bands (10-80)
- dti_risk: Based on DTI ratio (10-70)
- anomaly_risk: Late payments, defaults (0-80)
- employment_risk: Type and tenure (0-50)
- liability_risk: Existing liability ratio (10-30)
```

### Decision Rules

```
Risk Score Decision Rules:
├─ Risk < 25     → APPROVED (Low Risk)
├─ Risk 25-50    → APPROVED (Medium-Low Risk)
├─ Risk 50-75    → REQUIRES_REVIEW (Manual intervention needed)
└─ Risk > 75     → REJECTED (High Risk)

Confidence Scoring:
├─ APPROVED: 0.7-0.95 (higher for low risk)
├─ REJECTED: 0.60-0.95 (higher for high risk)
└─ REQUIRES_REVIEW: 0.65-0.75 (medium confidence)

Override Conditions:
├─ Credit < 550: Auto-REJECTED
├─ Has defaults: Auto-REJECTED
├─ Credit >= 750 + DTI <= 20: Auto-APPROVED
└─ Multiple anomalies: Auto-REQUIRES_REVIEW
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **UI** | Streamlit | Web interface |
| **API** | FastAPI | REST endpoints |
| **Orchestration** | Claude AI | LLM-powered decisions |
| **MCP Servers** | FastMCP | Tool/function definitions |
| **Data** | JSON files | Persistence layer |
| **Python** | 3.8+ | Language/runtime |
| **HTTP** | REST/HTTP | Client-server communication |

## Scalability Considerations

### Current (Single-Server)
- JSON file-based persistence
- Single API instance
- In-memory orchestrator
- Suitable for: Development, testing, demos

### Production Enhancements Needed

1. **Database Layer**
   - PostgreSQL for structured data
   - MongoDB for audit logs
   - Redis for caching

2. **Load Balancing**
   - Multiple API instances
   - Load balancer (nginx)
   - Kubernetes orchestration

3. **Message Queue**
   - Celery + RabbitMQ for background tasks
   - Distributed task processing

4. **Monitoring**
   - Prometheus metrics
   - ELK stack for logs
   - NewRelic/DataDog APM

5. **Security**
   - JWT authentication
   - RBAC (role-based access control)
   - Data encryption at rest

## Deployment

### Local Development
```bash
./scripts/start_services.sh  # Starts both API and UI
```

### Docker Deployment
```dockerfile
# Multi-stage Dockerfile (to be created)
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0"]
```

### Cloud Deployment
- AWS: ECS + RDS + S3
- GCP: Cloud Run + Firestore
- Azure: App Service + Cosmos DB

## Testing Strategy

### Test Files
- `test_system.py` - Comprehensive test suite

### Test Coverage
1. ✅ Data loading tests
2. ✅ Orchestrator initialization
3. ✅ Single application processing
4. ✅ Batch processing
5. ✅ Data persistence
6. ⏳ API endpoint tests (to be added)
7. ⏳ UI interaction tests (to be added)

## Security Considerations

### Current Implementation
- ✅ API input validation (Pydantic)
- ✅ Application isolation (file-based)
- ✅ No sensitive data in logs

### Production Additions Needed
- [ ] API authentication (JWT/OAuth)
- [ ] Rate limiting
- [ ] SQL injection prevention (if using DB)
- [ ] Data encryption
- [ ] Audit trail signing
- [ ] PII redaction

## Monitoring & Logging

### Current Implementation
- Execution logs in application state
- File-based audit trail
- Console output for debugging

### Production Enhancements
- Centralized logging (ELK Stack)
- Application performance monitoring
- Alert thresholds
- Decision audit trail with signatures

---

## Architecture Diagrams

### Request/Response Flow
```
Client Request
     │
     ├─ User submits via Streamlit
     │
     ▼
FastAPI Endpoint
     │
     ├─ Validate input
     ├─ Create application record
     └─ Queue background task
     │
     ▼ (Async Processing)
Orchestrator
     │
     ├─ Stage 1: Profile Analysis
     ├─ Stage 2: Risk Analysis
     ├─ Stage 3: Decision Making
     └─ Stage 4: Compliance
     │
     ▼
Save State to File
     │
     ▼ (Poll for status)
User checks status
     │
     ├─ Load application state
     └─ Display results
```

### Component Interaction Diagram
```
┌─────────────┐
│  Streamlit  │
│     UI      │
└──────┬──────┘
       │ HTTP
       ▼
┌──────────────┐
│   FastAPI    │
│     REST     │
└──────┬───────┘
       │ Python Objects
       ▼
┌──────────────────────┐
│  Orchestrator        │
│  (Claude Agent)      │
└──────┬───────────────┘
       │ Prompt/Response
       ▼
┌──────────────────────┐
│  Claude API          │
│  (LLM Backend)       │
└──────────────────────┘
       │
       │ Tool calls
       ▼
┌──────────────────────────────────────┐
│  MCP Servers (Tool Providers)       │
│  ├─ ApplicantDB                    │
│  ├─ RiskRulesDB                    │
│  ├─ DecisionSynthesis              │
│  └─ NotificationSystem             │
└──────────┬───────────────────────────┘
           │ File I/O
           ▼
      ┌─────────────┐
      │ JSON Data   │
      │   Files     │
      └─────────────┘
```

---

This architecture is designed to be:
- **Modular**: Each component has a specific responsibility
- **Scalable**: Can be extended with additional agents or rules
- **Explainable**: Decisions include reasoning and factors
- **Auditable**: Complete audit trail of all decisions
- **Maintainable**: Clear separation of concerns
