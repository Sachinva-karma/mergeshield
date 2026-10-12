import pytest
from app.schemas import FileEvidence, RiskFinding, VerificationAction
from app.verification_planner import (
    assess_evidence_strength,
    determine_priority,
    plan_verifications_for_finding,
    sort_findings_by_priority,
)


def test_assess_evidence_strength():
    # 1. Verified on modified line
    ev_verified = [
        FileEvidence(
            file_path="app/auth.py",
            snippet="token = request.headers.get('Authorization')",
            is_verified_in_diff=True,
            is_changed_line=True,
        )
    ]
    assert assess_evidence_strength(ev_verified) == "Verified in Diff"

    # 2. Plausible on surrounding context line only
    ev_context = [
        FileEvidence(
            file_path="app/auth.py",
            snippet="return verify_jwt(token)",
            is_verified_in_diff=True,
            is_changed_line=False,
        )
    ]
    assert assess_evidence_strength(ev_context) == "Plausible (Context Only)"

    # 3. Speculative with ungrounded citation
    ev_ungrounded = [
        FileEvidence(
            file_path="app/billing.py",
            snippet="charge_card()",
            is_verified_in_diff=False,
            is_changed_line=False,
        )
    ]
    assert assess_evidence_strength(ev_ungrounded) == "Speculative (Ungrounded)"


def test_determine_priority_explainable_reasoning():
    ev_changed = [
        FileEvidence(
            file_path="app/auth.py",
            snippet="bypass = True",
            is_verified_in_diff=True,
            is_changed_line=True,
        )
    ]
    # High severity + verified changed line -> Urgent
    p, reason = determine_priority("HIGH", "Verified in Diff", "Security", ev_changed)
    assert p == "Urgent"
    assert "urgent priority" in reason.lower()
    assert "security" in reason.lower()

    # Medium severity + Error Handling -> High priority
    p, reason = determine_priority("MEDIUM", "Verified in Diff", "Error Handling", ev_changed)
    assert p == "High"
    assert "error handling" in reason.lower()

    # High severity with ungrounded evidence -> downgraded to Normal
    p, reason = determine_priority("HIGH", "Speculative (Ungrounded)", "Logic", [])
    assert p == "Normal"
    assert "could not be verified" in reason.lower()

    # Low severity -> Low
    p, reason = determine_priority("LOW", "Verified in Diff", "Style", ev_changed)
    assert p == "Low"


def test_smart_verification_planner_distinguishes_execution():
    ev = [
        FileEvidence(
            file_path="app/api.py",
            snippet="url_map.add(route)",
            is_verified_in_diff=True,
            is_changed_line=True,
        )
    ]
    plan = plan_verifications_for_finding(
        category="Error Handling",
        summary="Broad exception handling in route registration",
        explanation="Catches Exception silently",
        raw_suggested_tests=["Pass malformed URL rule and assert error is raised"],
        evidence=ev,
    )

    assert len(plan) == 1
    action = plan[0]
    # Explicitly check that test was NOT marked as executed
    assert action.is_executed is False
    assert action.action_type in ("input_validation", "unit_test")
    assert "malformed" in action.what_to_verify.lower()
    assert action.motivating_file == "app/api.py"


def test_verification_planner_fallback_to_manual_review():
    plan = plan_verifications_for_finding(
        category="Architecture",
        summary="Module re-export refactoring",
        explanation="Files moved between packages",
        raw_suggested_tests=[],
        evidence=[],
    )

    assert len(plan) == 1
    action = plan[0]
    assert action.action_type == "manual_review"
    assert action.is_executed is False
    assert "manually review" in action.what_to_verify.lower()


def test_sort_findings_by_priority():
    f_low = RiskFinding(
        id="RISK-3",
        category="Style",
        severity="LOW",
        summary="Minor comment typo",
        explanation="",
        uncertainty="",
        evidence=[],
        priority="Low",
    )
    f_urgent = RiskFinding(
        id="RISK-1",
        category="Security",
        severity="HIGH",
        summary="Auth bypass vulnerability",
        explanation="",
        uncertainty="",
        evidence=[],
        priority="Urgent",
    )
    f_high = RiskFinding(
        id="RISK-2",
        category="Error Handling",
        severity="MEDIUM",
        summary="Uncaught exception",
        explanation="",
        uncertainty="",
        evidence=[],
        priority="High",
    )

    sorted_list = sort_findings_by_priority([f_low, f_urgent, f_high])
    assert [f.id for f in sorted_list] == ["RISK-1", "RISK-2", "RISK-3"]
