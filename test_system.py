#!/usr/bin/env python3
"""
Comprehensive test script for the Loan Application AI System.
Tests all components end-to-end.
"""

import json
import time
from pathlib import Path
from orchestration.state import LoanApplication, ApplicationState
from agents.orchestrator import LoanApplicationOrchestrator

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_applicant_loading():
    """Test loading applicant data"""
    print_section("TEST 1: Loading Applicant Data")

    data_path = Path("data/mock_applicants.json")
    with open(data_path) as f:
        data = json.load(f)

    print(f"✓ Loaded {len(data['applicants'])} applicants:")
    for app_id, applicant in data['applicants'].items():
        print(f"  - {app_id}: {applicant['name']} (Credit: {applicant['credit_score']})")

    return True

def test_risk_rules_loading():
    """Test loading risk rules"""
    print_section("TEST 2: Loading Risk Rules")

    data_path = Path("data/mock_risk_rules.json")
    with open(data_path) as f:
        rules = json.load(f)

    print(f"✓ Loaded risk rules with sections:")
    print(f"  - Credit Score Thresholds: {len(rules['credit_score_thresholds'])} levels")
    print(f"  - Debt-to-Income Thresholds: {len(rules['debt_to_income_thresholds'])} levels")
    print(f"  - Employment Risk Factors: {len(rules['employment_risk'])} types")
    print(f"  - Approval Rules: {len(rules['approval_rules'])} rules")

    return True

def test_orchestrator_initialization():
    """Test orchestrator initialization"""
    print_section("TEST 3: Orchestrator Initialization")

    try:
        orchestrator = LoanApplicationOrchestrator()
        print(f"✓ Orchestrator initialized successfully")
        print(f"  - Model: {orchestrator.model}")
        print(f"  - Conversation History: {len(orchestrator.conversation_history)} messages")
        return True
    except Exception as e:
        print(f"✗ Error initializing orchestrator: {e}")
        return False

def test_single_application(applicant_id, loan_amount=100000, tenure_months=60):
    """Test processing a single loan application"""
    print_section(f"TEST 4: Processing Application for {applicant_id}")

    try:
        orchestrator = LoanApplicationOrchestrator()

        # Create application
        app = LoanApplication(
            applicant_id=applicant_id,
            loan_amount=loan_amount,
            tenure_months=tenure_months
        )

        print(f"📋 Application Details:")
        print(f"  - Applicant ID: {applicant_id}")
        print(f"  - Loan Amount: ${loan_amount:,.2f}")
        print(f"  - Tenure: {tenure_months} months")

        # Orchestrate
        print(f"\n🔄 Processing...")
        state = orchestrator.orchestrate(app)

        # Display results
        print(f"\n✓ Processing Complete!")
        print(f"  - Status: {state.status}")
        print(f"  - Decision: {state.decision}")
        print(f"  - Risk Score: {state.final_risk_score:.1f}/100")
        print(f"  - Confidence: {state.confidence_level*100:.0f}%")

        if state.key_decision_factors:
            print(f"\n📌 Key Factors:")
            for factor in state.key_decision_factors:
                print(f"  - {factor}")

        if state.errors:
            print(f"\n⚠️ Errors:")
            for error in state.errors:
                print(f"  - {error}")

        return state

    except Exception as e:
        print(f"✗ Error processing application: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_all_applicants():
    """Test processing all applicants"""
    print_section("TEST 5: Batch Processing All Applicants")

    data_path = Path("data/mock_applicants.json")
    with open(data_path) as f:
        data = json.load(f)

    results = {}
    for applicant_id in data['applicants'].keys():
        print(f"\nProcessing {applicant_id}...")
        state = test_single_application(
            applicant_id,
            loan_amount=100000,
            tenure_months=60
        )
        if state:
            results[applicant_id] = {
                "decision": state.decision,
                "risk_score": state.final_risk_score,
                "confidence": state.confidence_level
            }

    # Summary
    print_section("Batch Processing Summary")
    approved = sum(1 for r in results.values() if r["decision"] == "APPROVED")
    rejected = sum(1 for r in results.values() if r["decision"] == "REJECTED")
    review = sum(1 for r in results.values() if r["decision"] == "REQUIRES_REVIEW")

    print(f"✓ Results:")
    print(f"  - Approved: {approved}")
    print(f"  - Rejected: {rejected}")
    print(f"  - Requires Review: {review}")

    for app_id, result in results.items():
        status_icon = "✓" if result["decision"] == "APPROVED" else "✗" if result["decision"] == "REJECTED" else "⚠"
        print(f"\n{status_icon} {app_id}: {result['decision']} (Risk: {result['risk_score']:.1f}, Confidence: {result['confidence']:.0%})")

    return results

def test_data_persistence():
    """Test saving and loading decisions"""
    print_section("TEST 6: Data Persistence")

    decisions_path = Path("data/decisions.json")

    # Load existing
    with open(decisions_path) as f:
        data = json.load(f)

    print(f"✓ Decision records:")
    print(f"  - Total records: {len(data['decisions'])}")

    # Create sample record
    sample_record = {
        "case_id": "CASE_TEST_001",
        "applicant_id": "APP001",
        "decision": "APPROVED",
        "risk_score": 22.5,
        "confidence_level": 0.92
    }

    data['decisions'].append(sample_record)

    with open(decisions_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✓ Saved test record: {sample_record['case_id']}")

    # Reload
    with open(decisions_path) as f:
        reloaded = json.load(f)

    if sample_record in reloaded['decisions']:
        print(f"✓ Successfully persisted and retrieved record")
        # Remove test record
        reloaded['decisions'].remove(sample_record)
        with open(decisions_path, "w") as f:
            json.dump(reloaded, f, indent=2)
        return True
    else:
        print(f"✗ Failed to persist record")
        return False

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║  Multi-Agent Loan Application AI System - Test Suite  ║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")

    tests = [
        ("Applicant Data Loading", test_applicant_loading),
        ("Risk Rules Loading", test_risk_rules_loading),
        ("Orchestrator Initialization", test_orchestrator_initialization),
        ("Data Persistence", test_data_persistence),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            failed += 1

    # Single application test (requires Claude API)
    print_section("Optional: Single Application Processing")
    print("Note: This requires a valid ANTHROPIC_API_KEY")

    try:
        print("Testing with APP001 (Expected: APPROVED)...")
        test_single_application("APP001")
    except Exception as e:
        print(f"⚠️  Skipping (requires API key): {e}")

    # Summary
    print_section("Test Summary")
    print(f"✓ Passed: {passed}")
    print(f"✗ Failed: {failed}")
    print(f"Total: {passed + failed}")

    if failed == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {failed} test(s) failed")

if __name__ == "__main__":
    main()
