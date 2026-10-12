from typing import List, Tuple
from app.schemas import FileEvidence, RiskFinding, VerificationAction


PRIORITY_WEIGHTS = {
    "Urgent": 4,
    "High": 3,
    "Normal": 2,
    "Low": 1,
}


def assess_evidence_strength(evidence: List[FileEvidence]) -> str:
    """
    Evaluates evidence strength deterministically based on diff grounding:
    - 'Verified in Diff': cited snippet matches modified (+/-) code lines in diff.
    - 'Plausible (Context Only)': cited snippet exists in diff context lines but not modified lines.
    - 'Speculative (Ungrounded)': citation could not be confirmed in retrieved diff.
    """
    if not evidence:
        return "Speculative (Ungrounded)"

    has_unverified = any(not ev.is_verified_in_diff for ev in evidence)
    if has_unverified:
        return "Speculative (Ungrounded)"

    has_changed_line = any(ev.is_changed_line for ev in evidence)
    if has_changed_line:
        return "Verified in Diff"

    return "Plausible (Context Only)"


def determine_priority(
    severity: str,
    evidence_strength: str,
    category: str,
    evidence: List[FileEvidence],
) -> Tuple[str, str]:
    """
    Calculates explainable priority based on:
    - Potential severity (High, Medium, Low)
    - Grounding evidence strength (Verified, Context, Speculative)
    - Security/architecture boundary sensitivity
    Returns: (priority: str, priority_reasoning: str)
    """
    sev = severity.upper()
    cat_lower = category.lower()

    is_critical_boundary = any(
        k in cat_lower for k in ("security", "auth", "error handling", "concurrency")
    )
    is_directly_modified = any(ev.is_changed_line for ev in evidence) if evidence else False

    if sev == "HIGH":
        if evidence_strength == "Verified in Diff" and is_directly_modified:
            return (
                "Urgent",
                f"Urgent priority: High-severity {category} risk verified directly on modified code lines. Should be investigated before merging.",
            )
        elif evidence_strength == "Verified in Diff":
            return (
                "High",
                f"High priority: High-severity potential impact identified in modified file context.",
            )
        else:
            return (
                "Normal",
                f"Adjusted to Normal priority: High potential severity, but cited lines could not be verified in the retrieved diff.",
            )

    if sev == "MEDIUM":
        if evidence_strength == "Verified in Diff" and is_critical_boundary:
            return (
                "High",
                f"High priority: Medium-severity {category} issue with direct diff evidence on core application logic.",
            )
        elif evidence_strength == "Verified in Diff":
            return (
                "Normal",
                f"Normal priority: Plausible code quality or logic concern grounded in diff modifications.",
            )
        else:
            return (
                "Low",
                f"Adjusted to Low priority: Medium concern with speculative or ungrounded evidence.",
            )

    # LOW severity
    return (
        "Low",
        f"Low priority: Minor maintenance, contract, or non-blocking suggestion.",
    )


def build_verification_action(
    category: str,
    summary: str,
    explanation: str,
    test_str: str,
    motivating_file: str,
) -> VerificationAction:
    """
    Constructs a structured VerificationAction explaining what to verify, why,
    and the expected behavior. Explicitly sets is_executed=False.
    """
    cat_lower = category.lower()

    # Determine action type
    if any(k in cat_lower for k in ("security", "auth", "permission", "rbac")):
        action_type = "auth_permission"
        expected = "Unauthorized or malformed credentials must be rejected with 401/403 without data exposure."
    elif any(k in cat_lower for k in ("api contract", "contract", "schema")):
        action_type = "api_contract"
        expected = "Response schema and HTTP status codes must match agreed client contract specifications."
    elif any(k in cat_lower for k in ("error handling", "validation", "exception")):
        action_type = "input_validation"
        expected = "Edge cases, invalid inputs, or raised exceptions must be safely caught and logged or handled."
    elif any(k in cat_lower for k in ("concurrency", "race condition", "deadlock")):
        action_type = "integration_test"
        expected = "Concurrent requests or asynchronous tasks must execute without race conditions or resource corruption."
    elif any(k in cat_lower for k in ("regression", "compatibility")):
        action_type = "regression"
        expected = "Existing functionality and caller contracts must remain backward compatible."
    else:
        action_type = "unit_test"
        expected = "Component logic produces expected output under target boundary conditions."

    # If test string looks like manual review
    if any(k in test_str.lower() for k in ("manually", "review", "inspect docs", "consult")):
        action_type = "manual_review"
        expected = "Reviewer inspects external configuration or operational documentation."

    return VerificationAction(
        action_type=action_type,
        what_to_verify=test_str or f"Verify handling of: {summary}",
        why_it_matters=f"Addresses potential risk in {category}: {summary}",
        expected_behavior=expected,
        suggested_scenario=test_str,
        motivating_file=motivating_file or "PR diff",
        is_executed=False,  # Never falsely claim execution
    )


def plan_verifications_for_finding(
    category: str,
    summary: str,
    explanation: str,
    raw_suggested_tests: List[str],
    evidence: List[FileEvidence],
) -> List[VerificationAction]:
    """
    Generates structured verification actions for a finding.
    If no tests were provided by the model, provides a grounded manual review fallback.
    """
    motivating_file = evidence[0].file_path if evidence else "Modified files"
    plan: List[VerificationAction] = []

    if raw_suggested_tests:
        for t in raw_suggested_tests:
            if t.strip():
                plan.append(
                    build_verification_action(
                        category=category,
                        summary=summary,
                        explanation=explanation,
                        test_str=t.strip(),
                        motivating_file=motivating_file,
                    )
                )

    if not plan:
        plan.append(
            VerificationAction(
                action_type="manual_review",
                what_to_verify=f"Manually review {category} logic in {motivating_file}",
                why_it_matters=f"Insufficient automated test context in diff for: {summary}",
                expected_behavior="Confirm implementation matches design expectations.",
                suggested_scenario=f"Inspect changed lines in {motivating_file} for unexpected side-effects.",
                motivating_file=motivating_file,
                is_executed=False,
            )
        )

    return plan[:3]  # Bounded to top 3 actions per finding


def sort_findings_by_priority(findings: List[RiskFinding]) -> List[RiskFinding]:
    """
    Sorts findings so Urgent and High priority items appear first.
    """
    return sorted(
        findings,
        key=lambda f: PRIORITY_WEIGHTS.get(f.priority, 1),
        reverse=True,
    )
