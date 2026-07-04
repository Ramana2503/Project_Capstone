# Quick Start Guide

Get the Multi-Agent Loan Application AI System running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- Anthropic API key (get it at https://console.anthropic.com)

## Step 1: Setup

```bash
cd /home/ubuntu/Desktop/Capstone_01

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
nano .env
```

## Step 2: Run the System

### Option A: Automated Start (Recommended)

```bash
chmod +x scripts/start_services.sh
./scripts/start_services.sh
```

The script will:
- Activate the virtual environment
- Install dependencies
- Start FastAPI server (http://localhost:8000)
- Start Streamlit UI (http://localhost:8501)

### Option B: Manual Start

**Terminal 1: API Server**
```bash
source venv/bin/activate
python -m uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2: Streamlit UI**
```bash
source venv/bin/activate
streamlit run ui/streamlit_app.py --server.port=8501
```

## Step 3: Access the Application

### Streamlit UI (User-Friendly)
Open browser: http://localhost:8501

1. **Submit Application Tab**
   - Select an applicant (APP001-APP005)
   - Enter loan amount (e.g., $100,000)
   - Enter loan tenure (e.g., 60 months)
   - Click "Submit Application"
   - Copy the Application ID

2. **Check Status Tab**
   - Paste the Application ID
   - Click "Check Status"
   - View decision and details

### API Endpoints
- Health Check: http://localhost:8000/health
- API Docs: http://localhost:8000/docs
- Submit Loan: POST http://localhost:8000/submit-loan
- Check Status: GET http://localhost:8000/loan-status/{application_id}

## Sample Applications

Use these test applicants:

| ID | Name | Status | Expected Decision |
|----|------|--------|-------------------|
| APP001 | John Smith | ✓ Good | APPROVED |
| APP002 | Sarah Johnson | ⚠ Mixed | REQUIRES_REVIEW |
| APP003 | Mike Davis | ✓ Excellent | APPROVED |
| APP004 | Emma Wilson | ✗ Poor | REJECTED |
| APP005 | Robert Brown | ✓ Good | APPROVED |

## Testing with cURL

```bash
# 1. Submit application
curl -X POST "http://localhost:8000/submit-loan" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP001",
    "loan_amount": 100000,
    "tenure_months": 60
  }'

# Copy the application_id from response

# 2. Check status (wait 3-5 seconds for processing)
curl "http://localhost:8000/loan-status/APP_xxxxxxxx"

# 3. List all applications
curl "http://localhost:8000/applications/"
```

## Common Issues

### Error: Cannot connect to API
```
✗ Cannot connect to API. Make sure the server is running on http://localhost:8000
```
**Solution:** Ensure API server is running in Terminal 1

### Error: ANTHROPIC_API_KEY not set
```
✗ Error: ANTHROPIC_API_KEY not set
```
**Solution:** 
1. Get API key from https://console.anthropic.com
2. Add to .env file: `ANTHROPIC_API_KEY=sk-ant-...`

### Port Already in Use
```
Error: Address already in use: ('0.0.0.0', 8000)
```
**Solution:** Kill existing process or use different port:
```bash
# Linux/Mac
lsof -ti:8000 | xargs kill -9

# Or use different ports
python -m uvicorn api.app:app --reload --port 8001
streamlit run ui/streamlit_app.py --server.port=8502
```

## System Architecture

```
┌─────────────────────────────────┐
│   Streamlit UI (localhost:8501) │
│   ├─ Submit Application         │
│   ├─ Check Status               │
│   └─ View All Applications      │
└──────────────┬──────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  FastAPI Server (localhost:8000) │
│  ├─ POST /submit-loan            │
│  ├─ GET /loan-status/{id}        │
│  └─ GET /applications/           │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  Claude Orchestrator Agent       │
│  ├─ Profile Analysis             │
│  ├─ Risk Analysis                │
│  └─ Decision Making              │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  Mock Data & Rules               │
│  ├─ mock_applicants.json         │
│  ├─ mock_risk_rules.json         │
│  └─ decisions.json               │
└──────────────────────────────────┘
```

## Next Steps

1. **Test with all applicants** - Try each APP001-APP005
2. **Review decisions** - Check the decision explanations
3. **Explore API** - Visit http://localhost:8000/docs
4. **Check logs** - Review data/applications/*.json files
5. **Extend system** - Add more applicants or modify rules

## File Structure

```
Capstone_01/
├── api/                           # FastAPI application
│   ├── app.py                    # Main app
│   ├── schemas.py                # Pydantic models
│   └── validators.py             # Input validation
├── agents/                        # Agent logic
│   ├── orchestrator.py           # Main orchestrator
│   └── mcp_servers/              # MCP tool providers
├── ui/                           # Streamlit UI
│   └── streamlit_app.py          # Main UI
├── orchestration/                # State management
│   └── state.py                  # Application state
├── data/                         # Mock data
│   ├── mock_applicants.json      # Test applicants
│   ├── mock_risk_rules.json      # Risk rules
│   ├── decisions.json            # Audit log
│   └── applications/             # Submitted applications
├── scripts/                      # Utility scripts
│   └── start_services.sh         # Startup script
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── README.md                     # Full documentation
└── QUICKSTART.md                 # This file
```

## Performance Tips

- **First request takes longer** - Claude API initialization
- **Subsequent requests faster** - Cached embeddings
- **Adjust timeouts** - If behind proxy or slow network
- **Scale horizontally** - Run multiple API instances

## Support Resources

- **Claude Documentation:** https://docs.anthropic.com
- **FastAPI Documentation:** https://fastapi.tiangolo.com
- **Streamlit Documentation:** https://docs.streamlit.io
- **GitHub Issues:** Report bugs and feature requests

## What's Next?

After running the system:
1. Review the decision logic in `agents/orchestrator.py`
2. Modify risk rules in `data/mock_risk_rules.json`
3. Add more test applicants to `data/mock_applicants.json`
4. Explore Claude's capabilities with custom prompts
5. Integrate with real data sources

---

**Need Help?** Check README.md for detailed documentation or see Troubleshooting section above.
