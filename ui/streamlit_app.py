import streamlit as st
import requests
import json
import time
from datetime import datetime, date
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Loan Application AI",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling
st.markdown("""
<style>
    .main {
        padding: 20px;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .approved {
        color: #00cc00;
        font-weight: bold;
    }
    .rejected {
        color: #ff0000;
        font-weight: bold;
    }
    .review {
        color: #ff9900;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

API_URL = "http://localhost:8000"

# Sidebar
st.sidebar.title("🏦 Loan Application System")
page = st.sidebar.radio("Navigation", ["Submit Application", "Check Status", "View All Applications"])

def format_decision(decision, risk_score, confidence):
    if decision == "APPROVED":
        return f"<span class='approved'>✓ {decision}</span>"
    elif decision == "REJECTED":
        return f"<span class='rejected'>✗ {decision}</span>"
    elif decision == "REQUIRES_REVIEW":
        return f"<span class='review'>⚠ {decision}</span>"
    return decision


def poll_for_result(application_id: str, max_wait: int = 120) -> dict | None:
    """Poll /loan-status until COMPLETED or FAILED, or timeout."""
    deadline = time.time() + max_wait
    while time.time() < deadline:
        try:
            r = requests.get(f"{API_URL}/loan-status/{application_id}", timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get("status") in ("COMPLETED", "FAILED"):
                    return data
        except Exception:
            pass
        time.sleep(3)
    return None


def render_decision_result(app_status: dict):
    """Render the full decision output block."""
    status = app_status.get("status", "")
    st.divider()

    if status == "FAILED":
        st.error("❌ Processing failed. Please retry.")
        return
    if status != "COMPLETED" or not app_status.get("decision"):
        st.warning("⏳ Still processing — please check again shortly.")
        return

    decision = app_status["decision"]

    # ── Classification ────────────────────────────────────────────────
    st.subheader("1. Classification")
    if decision == "APPROVED":
        st.success("✅  APPROVED")
    elif decision == "REJECTED":
        st.error("❌  REJECTED")
    else:
        st.warning("⚠️  REQUIRES REVIEW")

    st.divider()

    # ── Risk Score & Confidence ───────────────────────────────────────
    st.subheader("2 & 3. Risk Score & Confidence Level")
    col1, col2 = st.columns(2)
    with col1:
        rs = app_status.get("risk_score")
        if rs is not None:
            color = "🟢" if rs < 30 else "🟡" if rs < 60 else "🔴"
            st.metric("Risk Score", f"{rs:.1f} / 100", delta=color)
    with col2:
        cl = app_status.get("confidence_level")
        if cl is not None:
            st.metric("Confidence Level", f"{cl * 100:.1f}%")

    st.divider()

    # ── Key Decision Factors ──────────────────────────────────────────
    st.subheader("4. Key Decision Factors")
    for f in (app_status.get("key_factors") or []):
        st.write(f"• {f}")

    st.divider()

    # ── Explanation ───────────────────────────────────────────────────
    st.subheader("5. Explanation")
    st.info(app_status.get("explanation") or "No explanation available.")

    st.divider()

    with st.expander("Application Details"):
        st.write(f"**Application ID:** {app_status['application_id']}")
        st.write(f"**Applicant ID:** {app_status['applicant_id']}")
        st.write(f"**Created:** {app_status.get('created_at', '')}")
        st.write(f"**Updated:** {app_status.get('updated_at', '')}")

    if st.checkbox("Show Raw JSON", key="raw_json_submit"):
        st.json(app_status)

# Page: Submit Application
if page == "Submit Application":
    st.title("📝 Submit Loan Application")

    with st.form("loan_application_form"):

        # ── Section 1: Applicant Identification ──────────────────────────
        st.subheader("1. Applicant Identification")
        col1, col2 = st.columns(2)
        with col1:
            applicant_id = st.text_input(
                "Applicant ID *",
                placeholder="e.g. APP001",
                help="Unique identifier for this applicant"
            )
        with col2:
            name = st.text_input(
                "Full Name *",
                placeholder="e.g. John Smith"
            )

        st.divider()

        # ── Section 2: Applicant Profile ─────────────────────────────────
        st.subheader("2. Applicant Profile")
        col1, col2, col3 = st.columns(3)
        with col1:
            age = st.number_input("Age *", min_value=18, max_value=100, value=30, step=1)
        with col2:
            income = st.number_input(
                "Annual Income ($) *",
                min_value=0,
                max_value=10_000_000,
                value=60000,
                step=1000,
                help="Gross annual income in USD"
            )
        with col3:
            employment_type = st.selectbox(
                "Employment Type *",
                options=["Full-time", "Contract", "Self-employed", "Part-time", "Unemployed"]
            )

        col1, col2 = st.columns(2)
        with col1:
            employment_years = st.number_input(
                "Years in Current Employment *",
                min_value=0.0,
                max_value=50.0,
                value=2.0,
                step=0.5
            )
        with col2:
            location = st.text_input(
                "Location *",
                placeholder="e.g. New York",
                help="City or region of residence"
            )

        st.divider()

        # ── Section 3: Credit Information ────────────────────────────────
        st.subheader("3. Credit Information")
        col1, col2 = st.columns(2)
        with col1:
            credit_score = st.number_input(
                "Credit Score *",
                min_value=300,
                max_value=850,
                value=700,
                step=1,
                help="FICO credit score (300–850)"
            )
        with col2:
            existing_liabilities = st.number_input(
                "Existing Liabilities ($) *",
                min_value=0,
                max_value=10_000_000,
                value=10000,
                step=500,
                help="Total outstanding debt (loans, credit cards, etc.)"
            )

        st.divider()

        # ── Section 4: Loan Details ───────────────────────────────────────
        st.subheader("4. Loan Details")
        col1, col2 = st.columns(2)
        with col1:
            loan_amount = st.number_input(
                "Loan Amount ($) *",
                min_value=1000,
                max_value=10_000_000,
                value=100000,
                step=1000
            )
        with col2:
            tenure_months = st.number_input(
                "Loan Tenure (months) *",
                min_value=6,
                max_value=360,
                value=60,
                step=6
            )

        st.divider()

        # ── Section 5: Application Timestamp ─────────────────────────────
        st.subheader("5. Application Timestamp")
        col1, col2 = st.columns(2)
        with col1:
            app_date = st.date_input("Application Date *", value=date.today())
        with col2:
            app_time = st.time_input("Application Time *", value=datetime.now().time())

        st.divider()

        submit_button = st.form_submit_button("🚀 Submit Application", use_container_width=True)

    if submit_button:
        # Basic validation
        missing = []
        if not applicant_id.strip():
            missing.append("Applicant ID")
        if not name.strip():
            missing.append("Full Name")
        if not location.strip():
            missing.append("Location")

        if missing:
            st.error(f"❌ Please fill in required fields: {', '.join(missing)}")
        else:
            app_timestamp = datetime.combine(app_date, app_time).isoformat()
            payload = {
                "applicant_id": applicant_id.strip().upper(),
                "name": name.strip(),
                "age": int(age),
                "income": float(income),
                "employment_type": employment_type,
                "employment_years": float(employment_years),
                "credit_score": int(credit_score),
                "existing_liabilities": float(existing_liabilities),
                "location": location.strip(),
                "loan_amount": float(loan_amount),
                "tenure_months": int(tenure_months),
                "application_timestamp": app_timestamp,
            }

            try:
                with st.spinner("📤 Submitting application..."):
                    response = requests.post(
                        f"{API_URL}/submit-loan",
                        json=payload,
                        timeout=30
                    )

                if response.status_code == 200:
                    result = response.json()
                    application_id = result["application_id"]
                    st.session_state.last_application_id = application_id
                    st.success(f"✅ Application submitted — ID: `{application_id}`")

                    # Poll for result on the same page
                    with st.spinner("⏳ Processing application through AI agents… (this may take 15–60 seconds)"):
                        final = poll_for_result(application_id, max_wait=120)

                    if final:
                        render_decision_result(final)
                    else:
                        st.warning(f"Processing is taking longer than expected. Use the **Check Status** page with ID `{application_id}` to retrieve the result.")
                else:
                    st.error(f"❌ Error submitting application: {response.text}")

            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to API. Make sure the server is running on http://localhost:8000")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# Page: Check Status
elif page == "Check Status":
    st.title("📊 Application Status")

    col1, col2 = st.columns([3, 1])

    with col1:
        application_id = st.text_input(
            "Enter Application ID",
            value=st.session_state.get("last_application_id", ""),
            placeholder="APP_xxxxxxxx"
        )

    with col2:
        check_button = st.button("🔍 Check Status", use_container_width=True)

    if check_button and application_id:
        try:
            with st.spinner("Fetching application status..."):
                response = requests.get(f"{API_URL}/loan-status/{application_id}", timeout=30)

            if response.status_code == 200:
                app_status = response.json()
                status = app_status.get("status", "")
                if status == "PROCESSING":
                    st.warning("⏳ Still processing — please check again in a moment.")
                else:
                    render_decision_result(app_status)
            elif response.status_code == 404:
                st.error(f"❌ Application not found: {application_id}")
            else:
                st.error(f"❌ Error: {response.text}")

        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to API. Make sure the server is running on http://localhost:8000")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Page: View All Applications
elif page == "View All Applications":
    st.title("📋 All Applications")

    try:
        with st.spinner("Loading applications..."):
            response = requests.get(f"{API_URL}/applications/", timeout=30)

        if response.status_code == 200:
            data = response.json()
            applications = data.get("applications", [])

            st.metric("Total Applications", data.get("total", 0))

            if applications:
                st.divider()

                # Create dataframe for display
                import pandas as pd
                df_data = []
                for app in applications:
                    df_data.append({
                        "Application ID": app["application_id"],
                        "Applicant ID": app["applicant_id"],
                        "Status": app["status"],
                        "Decision": app["decision"] or "Pending",
                        "Created": app["created_at"]
                    })

                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)

                # Allow quick status check
                st.divider()
                selected_app = st.selectbox("Select application to view details", [app["application_id"] for app in applications])
                if selected_app:
                    st.session_state.last_application_id = selected_app
                    if st.button("View Details"):
                        st.rerun()

            else:
                st.info("No applications submitted yet.")

        else:
            st.error(f"❌ Error loading applications: {response.text}")

    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API. Make sure the server is running on http://localhost:8000")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Footer
st.divider()
st.markdown("""
---
**Loan Application AI System** | Multi-Agent Agentic AI for Loan Decisions
Built with Streamlit, FastAPI, and Claude AI
""")
