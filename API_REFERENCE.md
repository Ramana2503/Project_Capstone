# API Reference

Complete REST API documentation for the Loan Application AI System.

## Base URL

```
http://localhost:8000
```

## API Documentation

### Interactive API Docs
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

**Description:** Check API server health and version

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

**Status Codes:**
- `200` - Server is healthy

---

### 2. Submit Loan Application

**Endpoint:** `POST /submit-loan`

**Description:** Submit a new loan application for processing

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "applicant_id": "string",
  "loan_amount": number,
  "tenure_months": integer
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `applicant_id` | string | Yes | Applicant identifier (APP001-APP005) |
| `loan_amount` | number | Yes | Loan amount in dollars (> 0) |
| `tenure_months` | integer | Yes | Loan tenure in months (6-360) |

**Examples:**

**cURL:**
```bash
curl -X POST "http://localhost:8000/submit-loan" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP001",
    "loan_amount": 100000,
    "tenure_months": 60
  }'
```

**Python (requests):**
```python
import requests

payload = {
    "applicant_id": "APP001",
    "loan_amount": 100000,
    "tenure_months": 60
}

response = requests.post(
    "http://localhost:8000/submit-loan",
    json=payload
)
print(response.json())
```

**JavaScript (fetch):**
```javascript
const payload = {
    applicant_id: "APP001",
    loan_amount: 100000,
    tenure_months: 60
};

fetch("http://localhost:8000/submit-loan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
})
.then(response => response.json())
.then(data => console.log(data));
```

**Response:** `200 OK`
```json
{
  "application_id": "APP_a1b2c3d4",
  "applicant_id": "APP001",
  "status": "PROCESSING",
  "decision": null,
  "risk_score": null,
  "confidence_level": null,
  "explanation": "Application submitted for processing",
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `application_id` | string | Unique application identifier for status tracking |
| `applicant_id` | string | The applicant ID submitted |
| `status` | string | Current processing status: "PROCESSING" |
| `decision` | string\|null | Final decision (set after processing) |
| `risk_score` | number\|null | Risk score 0-100 (set after processing) |
| `confidence_level` | number\|null | Confidence 0-1 (set after processing) |
| `explanation` | string | Human-readable message |
| `timestamp` | string | ISO 8601 timestamp |

**Status Codes:**
- `200` - Application submitted successfully
- `404` - Applicant not found
- `422` - Validation error (invalid parameters)
- `500` - Server error

**Error Examples:**

**Invalid Applicant:**
```json
{
  "detail": "Applicant APP999 not found"
}
```

**Invalid Tenure:**
```json
{
  "detail": [
    {
      "loc": ["body", "tenure_months"],
      "msg": "ensure this value is greater than or equal to 6",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

---

### 3. Check Application Status

**Endpoint:** `GET /loan-status/{application_id}`

**Description:** Retrieve the current status and decision of a submitted application

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `application_id` | string | Yes | Application ID from submission |

**Request:**
```bash
curl http://localhost:8000/loan-status/APP_a1b2c3d4
```

**Response:** `200 OK`
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
    "Stable full-time employment (5 years)"
  ],
  "created_at": "2024-01-15T10:30:00.123456",
  "updated_at": "2024-01-15T10:35:00.654321"
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `application_id` | string | The application ID |
| `applicant_id` | string | Associated applicant |
| `status` | string | Status: "PROCESSING", "COMPLETED", "FAILED" |
| `decision` | string\|null | APPROVED, REJECTED, REQUIRES_REVIEW, or null |
| `risk_score` | number\|null | Risk score 0-100 |
| `confidence_level` | number\|null | Confidence 0-1 |
| `key_factors` | array | List of key decision factors |
| `created_at` | string | ISO 8601 creation timestamp |
| `updated_at` | string | ISO 8601 last update timestamp |

**Status Codes:**
- `200` - Status retrieved successfully
- `404` - Application not found
- `500` - Server error

**Status Values:**
| Status | Description |
|--------|-------------|
| `PROCESSING` | Application is being analyzed |
| `COMPLETED` | Processing finished, decision available |
| `FAILED` | Processing encountered an error |

**Decision Values:**
| Decision | Meaning | Risk Score |
|----------|---------|------------|
| `APPROVED` | Loan approved automatically | < 50 |
| `REJECTED` | Loan rejected automatically | > 75 |
| `REQUIRES_REVIEW` | Needs manual review | 50-75 |
| `null` | Still processing | - |

**Examples:**

**Processing Still Running:**
```json
{
  "application_id": "APP_a1b2c3d4",
  "applicant_id": "APP001",
  "status": "PROCESSING",
  "decision": null,
  "risk_score": null,
  "confidence_level": null,
  "key_factors": null,
  "created_at": "2024-01-15T10:30:00.123456",
  "updated_at": "2024-01-15T10:30:05.000000"
}
```

**Rejected Application:**
```json
{
  "application_id": "APP_x2y3z4w5",
  "applicant_id": "APP004",
  "status": "COMPLETED",
  "decision": "REJECTED",
  "risk_score": 82.3,
  "confidence_level": 0.89,
  "key_factors": [
    "Critical credit score (<600)",
    "Applicant has defaulted accounts",
    "High debt-to-income ratio"
  ],
  "created_at": "2024-01-15T10:40:00.123456",
  "updated_at": "2024-01-15T10:42:30.654321"
}
```

---

### 4. List All Applications

**Endpoint:** `GET /applications/`

**Description:** Retrieve list of all submitted applications

**Query Parameters:** None

**Request:**
```bash
curl http://localhost:8000/applications/
```

**Response:** `200 OK`
```json
{
  "total": 3,
  "applications": [
    {
      "application_id": "APP_a1b2c3d4",
      "applicant_id": "APP001",
      "status": "COMPLETED",
      "decision": "APPROVED",
      "created_at": "2024-01-15T10:30:00.123456"
    },
    {
      "application_id": "APP_x2y3z4w5",
      "applicant_id": "APP004",
      "status": "COMPLETED",
      "decision": "REJECTED",
      "created_at": "2024-01-15T10:40:00.123456"
    },
    {
      "application_id": "APP_p5q6r7s8",
      "applicant_id": "APP002",
      "status": "PROCESSING",
      "decision": null,
      "created_at": "2024-01-15T10:50:00.123456"
    }
  ]
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `total` | integer | Total number of applications |
| `applications` | array | List of application summaries |

**Application Summary Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `application_id` | string | Application ID |
| `applicant_id` | string | Associated applicant |
| `status` | string | Current status |
| `decision` | string\|null | Current decision |
| `created_at` | string | ISO 8601 timestamp |

**Status Codes:**
- `200` - List retrieved successfully
- `500` - Server error

---

## Response Formats

### Success Response (2xx)
```json
{
  "application_id": "string",
  "status": "string",
  "decision": "string or null",
  "risk_score": "number or null",
  "confidence_level": "number or null",
  ...
}
```

### Error Response (4xx)
```json
{
  "detail": "Error message describing what went wrong"
}
```

### Validation Error Response (422)
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Validation error message",
      "type": "error_type"
    }
  ]
}
```

---

## Data Types

### Applicant ID (string)
Valid values: `APP001`, `APP002`, `APP003`, `APP004`, `APP005`

### Loan Amount (number)
- Minimum: 5000
- Maximum: 500000
- Step: Any value

### Tenure Months (integer)
- Minimum: 6 months
- Maximum: 360 months (30 years)
- Step: 1 month (or 6 for UI)

### Risk Score (number)
- Range: 0-100
- Interpretation:
  - 0-25: Very Low Risk
  - 25-50: Low Risk
  - 50-75: Medium Risk
  - 75-100: High Risk

### Confidence Level (number)
- Range: 0-1
- Interpretation:
  - 0.0-0.3: Low confidence
  - 0.3-0.7: Medium confidence
  - 0.7-1.0: High confidence

### Decision (string)
- `APPROVED` - Loan approved
- `REJECTED` - Loan rejected
- `REQUIRES_REVIEW` - Manual review needed
- `null` - Not yet determined

### Status (string)
- `PROCESSING` - Currently being analyzed
- `COMPLETED` - Processing finished
- `FAILED` - Processing encountered error

---

## Usage Examples

### Complete Workflow Example

```bash
# 1. Submit application
RESPONSE=$(curl -X POST "http://localhost:8000/submit-loan" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP001",
    "loan_amount": 150000,
    "tenure_months": 72
  }')

APP_ID=$(echo $RESPONSE | jq -r '.application_id')
echo "Application ID: $APP_ID"

# 2. Check status immediately (still processing)
curl http://localhost:8000/loan-status/$APP_ID | jq '.'

# 3. Wait a few seconds
sleep 5

# 4. Check status again (should be completed)
curl http://localhost:8000/loan-status/$APP_ID | jq '.'

# 5. List all applications
curl http://localhost:8000/applications/ | jq '.'
```

### Check All Applicants

```bash
for APPLICANT in APP001 APP002 APP003 APP004 APP005; do
  echo "Submitting application for $APPLICANT..."
  
  RESPONSE=$(curl -X POST "http://localhost:8000/submit-loan" \
    -H "Content-Type: application/json" \
    -d "{
      \"applicant_id\": \"$APPLICANT\",
      \"loan_amount\": 100000,
      \"tenure_months\": 60
    }")
  
  APP_ID=$(echo $RESPONSE | jq -r '.application_id')
  echo "Application ID: $APP_ID"
  
  sleep 1
done

# List all applications
curl http://localhost:8000/applications/ | jq '.applications[] | {app_id: .application_id, decision: .decision}'
```

### Parse JSON Responses

```bash
# Get only the decision from status check
curl http://localhost:8000/loan-status/APP_a1b2c3d4 | jq '.decision'

# Get all key factors
curl http://localhost:8000/loan-status/APP_a1b2c3d4 | jq '.key_factors[]'

# Get applications with high risk scores
curl http://localhost:8000/applications/ | \
  jq '.applications[] | select(.risk_score > 50)'
```

---

## Rate Limiting

Currently no rate limiting is implemented. Production deployment should add:
- Per-IP rate limiting (e.g., 100 requests/minute)
- Per-API-key rate limiting for authenticated users
- Endpoint-specific limits

---

## Authentication

Currently no authentication is required. Production deployment should implement:
- JWT token authentication
- OAuth 2.0 integration
- API key management

---

## Error Handling

### Common Errors

**Applicant Not Found (404)**
```bash
curl -X POST "http://localhost:8000/submit-loan" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "INVALID",
    "loan_amount": 100000,
    "tenure_months": 60
  }'
```
Response:
```json
{
  "detail": "Applicant INVALID not found"
}
```

**Invalid Tenure (422)**
```bash
curl -X POST "http://localhost:8000/submit-loan" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP001",
    "loan_amount": 100000,
    "tenure_months": 5
  }'
```
Response:
```json
{
  "detail": [
    {
      "loc": ["body", "tenure_months"],
      "msg": "ensure this value is greater than or equal to 6",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

**Missing Required Field (422)**
```bash
curl -X POST "http://localhost:8000/submit-loan" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP001",
    "tenure_months": 60
  }'
```
Response:
```json
{
  "detail": [
    {
      "loc": ["body", "loan_amount"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Versioning

Current API Version: `1.0.0`

Future versions will be indicated in:
- Response headers: `X-API-Version: 1.0.0`
- Base URL: `/api/v1/submit-loan` (planned)

---

## Support

For API issues or questions:
1. Check this documentation
2. Review API docs at http://localhost:8000/docs
3. Check test cases in `test_system.py`
4. Review ARCHITECTURE.md for system design details
