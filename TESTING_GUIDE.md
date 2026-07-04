# Testing Guide

Complete guide for testing the Multi-Agent Loan Application AI System.

## Quick Test (2 minutes)

### Step 1: Verify Installation
```bash
cd /home/ubuntu/Desktop/Capstone_01
python3 -c "import fastapi, streamlit, anthropic; print('✅ All dependencies installed')"
```

### Step 2: Run Unit Tests
```bash
python test_system.py
```

Expected output:
```
==============================================================
  Multi-Agent Agentic AI Loan Application System - Test Suite
==============================================================

✓ Passed: 4
✗ Failed: 0
Total: 4

🎉 All tests passed!
```

### Step 3: Start Services
```bash
# Terminal 1
python -m uvicorn api.app:app --reload

# Terminal 2
streamlit run ui/streamlit_app.py
```

---

## Comprehensive Testing

### Test 1: Health Check

**Test:** Verify API is running
```bash
curl http://localhost:8000/health | jq '.'
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00..."
}
```

**Status:** ✅ PASS if status = "healthy"

---

### Test 2: Submit Application (APP001 - Expected APPROVED)

**Test:** Submit loan application for good applicant
```bash
curl -X POST "http://localhost:8000/submit-loan" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP001",
    "loan_amount": 100000,
    "tenure_months": 60
  }' | jq '.'
```

**Expected Response:**
```json
{
  "application_id": "APP_xxxxxxxx",
  "applicant_id": "APP001",
  "status": "PROCESSING",
  "decision": null,
  "risk_score": null,
  "confidence_level": null,
  "explanation": "Application submitted for processing",
  "timestamp": "2024-01-15T10:30:00..."
}
```

**Status:** ✅ PASS if status = "PROCESSING" and application_id is generated

---

### Test 3: Check Status (Wait for Processing)

**Test:** Poll for decision
```bash
# Save the application_id from Test 2
APP_ID="APP_xxxxxxxx"

# Wait 5 seconds for processing
sleep 5

# Check status
curl http://localhost:8000/loan-status/$APP_ID | jq '.'
```

**Expected Response (APPROVED):**
```json
{
  "application_id": "APP_xxxxxxxx",
  "applicant_id": "APP001",
  "status": "COMPLETED",
  "decision": "APPROVED",
  "risk_score": 22.5,
  "confidence_level": 0.92,
  "key_factors": [
    "Excellent credit score (750+)",
    "Good debt-to-income ratio",
    "Stable full-time employment (5 years)"
  ],
  "created_at": "2024-01-15T10:30:00...",
  "updated_at": "2024-01-15T10:35:00..."
}
```

**Status:** ✅ PASS if decision = "APPROVED", risk_score < 30, confidence_level > 0.8

---

### Test 4: Batch Test All Applicants

**Test Script:**
```bash
#!/bin/bash

APPLICANTS=("APP001" "APP002" "APP003" "APP004" "APP005")
EXPECTED=("APPROVED" "REQUIRES_REVIEW" "APPROVED" "REJECTED" "APPROVED")

echo "Testing all applicants..."
echo "=========================="

for i in "${!APPLICANTS[@]}"; do
    APPLICANT=${APPLICANTS[$i]}
    EXPECTED_DECISION=${EXPECTED[$i]}
    
    echo ""
    echo "Testing $APPLICANT (Expected: $EXPECTED_DECISION)..."
    
    # Submit application
    RESPONSE=$(curl -s -X POST "http://localhost:8000/submit-loan" \
      -H "Content-Type: application/json" \
      -d "{
        \"applicant_id\": \"$APPLICANT\",
        \"loan_amount\": 100000,
        \"tenure_months\": 60
      }")
    
    APP_ID=$(echo $RESPONSE | jq -r '.application_id')
    echo "  Application ID: $APP_ID"
    
    # Wait for processing
    sleep 3
    
    # Check status
    STATUS=$(curl -s http://localhost:8000/loan-status/$APP_ID)
    DECISION=$(echo $STATUS | jq -r '.decision')
    RISK=$(echo $STATUS | jq -r '.risk_score')
    
    echo "  Decision: $DECISION (Risk: $RISK)"
    
    if [ "$DECISION" = "$EXPECTED_DECISION" ]; then
        echo "  ✅ PASS"
    else
        echo "  ⚠️  Different than expected"
    fi
done
```

**Expected Results:**
| Applicant | Expected | Risk Score | Status |
|-----------|----------|-----------|--------|
| APP001 | APPROVED | < 30 | ✅ |
| APP002 | REQUIRES_REVIEW | 40-70 | ✅ |
| APP003 | APPROVED | < 25 | ✅ |
| APP004 | REJECTED | > 75 | ✅ |
| APP005 | APPROVED | 20-40 | ✅ |

---

### Test 5: Error Handling

#### Test 5a: Invalid Applicant
```bash
curl -X POST "http://localhost:8000/submit-loan" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "INVALID",
    "loan_amount": 100000,
    "tenure_months": 60
  }'
```

**Expected:** 404 error with "not found" message

#### Test 5b: Invalid Tenure
```bash
curl -X POST "http://localhost:8000/submit-loan" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP001",
    "loan_amount": 100000,
    "tenure_months": 3
  }'
```

**Expected:** 422 validation error

#### Test 5c: Missing Field
```bash
curl -X POST "http://localhost:8000/submit-loan" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP001",
    "tenure_months": 60
  }'
```

**Expected:** 422 error with "field required" message

---

### Test 6: List All Applications

**Test:** Get all submitted applications
```bash
curl http://localhost:8000/applications/ | jq '.'
```

**Expected Response:**
```json
{
  "total": 5,
  "applications": [
    {
      "application_id": "APP_xxxxxxxx",
      "applicant_id": "APP001",
      "status": "COMPLETED",
      "decision": "APPROVED",
      "created_at": "2024-01-15T10:30:00..."
    },
    ...
  ]
}
```

**Status:** ✅ PASS if total > 0 and all fields present

---

### Test 7: UI Testing

**Test:** Submit application via Streamlit UI

1. Open http://localhost:8501
2. Navigate to "Submit Application" tab
3. Select "APP001 - John Smith"
4. Enter Loan Amount: 100000
5. Enter Tenure: 60 months
6. Click "Submit Application"
7. Copy Application ID
8. Navigate to "Check Status" tab
9. Paste Application ID
10. Click "Check Status"

**Expected:** 
- ✅ Application submitted message
- ✅ Application ID displayed
- ✅ After 5 seconds, decision shows "APPROVED"
- ✅ Risk score displays < 30
- ✅ Key factors listed

---

### Test 8: Concurrent Applications

**Test:** Submit multiple applications simultaneously
```bash
# Submit 5 applications concurrently
for i in {1..5}; do
  APP="APP00$((i))"
  curl -s -X POST "http://localhost:8000/submit-loan" \
    -H "Content-Type: application/json" \
    -d "{
      \"applicant_id\": \"$APP\",
      \"loan_amount\": 100000,
      \"tenure_months\": 60
    }" &
done

# Wait for all to complete
wait

# List all
curl http://localhost:8000/applications/ | jq '.total'
```

**Expected:** All 5 applications processed successfully

---

### Test 9: Different Loan Amounts

**Test:** Verify DTI ratio calculation with different amounts
```bash
# Small loan
curl -X POST "http://localhost:8000/submit-loan" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP002",
    "loan_amount": 25000,
    "tenure_months": 36
  }' | jq '.application_id'

# Large loan
curl -X POST "http://localhost:8000/submit-loan" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP002",
    "loan_amount": 200000,
    "tenure_months": 120
  }' | jq '.application_id'

# After completion, compare risk scores
# Small loan should have lower risk score than large loan
```

---

### Test 10: Different Tenure Periods

**Test:** Verify tenure impact on DTI
```bash
# Short tenure (high monthly payment)
curl -X POST "http://localhost:8000/submit-loan" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP005",
    "loan_amount": 100000,
    "tenure_months": 12
  }'

# Long tenure (low monthly payment)
curl -X POST "http://localhost:8000/submit-loan" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP005",
    "loan_amount": 100000,
    "tenure_months": 240
  }'
```

**Expected:** Longer tenure results in lower risk score (lower monthly payment)

---

## Performance Testing

### Test 11: Response Time

**Test:** Measure API response time
```bash
time curl -X POST "http://localhost:8000/submit-loan" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP001",
    "loan_amount": 100000,
    "tenure_months": 60
  }' > /dev/null 2>&1
```

**Expected:** < 1 second

### Test 12: Processing Time

**Test:** Measure complete processing time
```bash
echo "Submitting application..."
START=$(date +%s)

RESPONSE=$(curl -s -X POST "http://localhost:8000/submit-loan" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP001",
    "loan_amount": 100000,
    "tenure_months": 60
  }')

APP_ID=$(echo $RESPONSE | jq -r '.application_id')

echo "Waiting for processing..."
while true; do
  STATUS=$(curl -s http://localhost:8000/loan-status/$APP_ID | jq -r '.status')
  if [ "$STATUS" = "COMPLETED" ]; then
    END=$(date +%s)
    DURATION=$((END - START))
    echo "Processing completed in $DURATION seconds"
    break
  fi
  sleep 1
done
```

**Expected:** 3-10 seconds total

---

## Test Results Summary

### Create Test Report

```bash
#!/bin/bash

echo "LOAN APPLICATION AI SYSTEM - TEST RESULTS" > test_report.txt
echo "=========================================" >> test_report.txt
echo "Date: $(date)" >> test_report.txt
echo "" >> test_report.txt

# Test 1: Health
echo "Test 1: Health Check" >> test_report.txt
curl -s http://localhost:8000/health >> test_report.txt 2>&1
echo "" >> test_report.txt

# Test 2: Submit APP001
echo "Test 2: Submit APP001" >> test_report.txt
APP_ID=$(curl -s -X POST "http://localhost:8000/submit-loan" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP001",
    "loan_amount": 100000,
    "tenure_months": 60
  }' | jq -r '.application_id')
echo "Application ID: $APP_ID" >> test_report.txt

# Test 3: Check Status
sleep 5
echo "Test 3: Status Check" >> test_report.txt
curl -s http://localhost:8000/loan-status/$APP_ID >> test_report.txt 2>&1
echo "" >> test_report.txt

# Test 4: List All
echo "Test 4: List Applications" >> test_report.txt
curl -s http://localhost:8000/applications/ >> test_report.txt 2>&1

echo "✅ Test report saved to test_report.txt"
```

---

## Troubleshooting Tests

### API Not Responding
```bash
# Check if API is running
curl http://localhost:8000/health

# If not, start it
python -m uvicorn api.app:app --reload
```

### Claude API Error
```bash
# Check if ANTHROPIC_API_KEY is set
echo $ANTHROPIC_API_KEY

# If not, set it
export ANTHROPIC_API_KEY="your-api-key"
```

### Port Already in Use
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9

# Or use different port
python -m uvicorn api.app:app --reload --port 8001
```

### JSON Parse Errors
```bash
# Install jq if needed
apt-get install jq

# Test JSON parsing
curl http://localhost:8000/health | jq '.'
```

---

## Automated Testing Script

Save as `run_tests.sh`:

```bash
#!/bin/bash

echo "🧪 LOAN APPLICATION AI SYSTEM - AUTOMATED TESTS"
echo "=============================================="
echo ""

# Check API
echo "1️⃣  Health Check..."
if curl -s http://localhost:8000/health | jq -e '.status' > /dev/null; then
    echo "   ✅ PASS"
else
    echo "   ❌ FAIL: API not responding"
    exit 1
fi

# Submit application
echo "2️⃣  Submit Application..."
RESPONSE=$(curl -s -X POST "http://localhost:8000/submit-loan" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP001",
    "loan_amount": 100000,
    "tenure_months": 60
  }')

APP_ID=$(echo $RESPONSE | jq -r '.application_id')
if [ -n "$APP_ID" ] && [ "$APP_ID" != "null" ]; then
    echo "   ✅ PASS (ID: $APP_ID)"
else
    echo "   ❌ FAIL: Could not submit application"
    exit 1
fi

# Wait and check status
echo "3️⃣  Check Status..."
sleep 5
STATUS=$(curl -s http://localhost:8000/loan-status/$APP_ID)
DECISION=$(echo $STATUS | jq -r '.decision')

if [ "$DECISION" = "APPROVED" ]; then
    echo "   ✅ PASS (Decision: APPROVED)"
else
    echo "   ⚠️  Different decision: $DECISION"
fi

# List applications
echo "4️⃣  List Applications..."
TOTAL=$(curl -s http://localhost:8000/applications/ | jq '.total')
if [ "$TOTAL" -gt 0 ]; then
    echo "   ✅ PASS (Total: $TOTAL)"
else
    echo "   ❌ FAIL: No applications"
fi

echo ""
echo "=============================================="
echo "✅ TEST SUITE COMPLETED"
echo "=============================================="
```

**Run tests:**
```bash
chmod +x run_tests.sh
./run_tests.sh
```

---

## Expected Test Results

### All Tests Passing
```
✅ TEST SUITE COMPLETED
- Health Check: PASS
- Submit Application: PASS
- Check Status: PASS
- List Applications: PASS
- Error Handling: PASS
- Concurrent Apps: PASS
- Different Amounts: PASS
- Performance: PASS
```

### Result Interpretation

| Test | Expected | Pass Criteria |
|------|----------|--------------|
| Health | 200 OK | status = "healthy" |
| Submit | 200 OK | application_id generated |
| Status | 200 OK | decision ∈ {APPROVED, REJECTED, REQUIRES_REVIEW} |
| List | 200 OK | total ≥ applications count |
| Errors | 404/422 | appropriate error codes |
| Performance | Complete | < 10 seconds total |

---

## Continuous Testing

For production, implement:
- [ ] Automated test suite (pytest)
- [ ] CI/CD pipeline integration
- [ ] Load testing (JMeter, Locust)
- [ ] Smoke tests every hour
- [ ] End-to-end tests daily
- [ ] Regression test suite
- [ ] Performance benchmarks

---

For questions about testing, refer to:
- [README.md](README.md) - System overview
- [API_REFERENCE.md](API_REFERENCE.md) - API documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick setup
