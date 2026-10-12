import pytest
from app.diff_parser import parse_unified_diff
from app.impact_analyzer import (
    classify_file_path,
    detect_interface_changes,
    evaluate_test_coverage_signal,
    infer_potential_impacts,
    build_change_impact_summary,
)
from app.schemas import DiffSummary, FileEvidence, FileImpact, RiskFinding


def test_classify_file_path_all_categories():
    assert classify_file_path("docs/architecture.md") == "Documentation"
    assert classify_file_path("README.md") == "Documentation"
    assert classify_file_path("LICENSE") == "Documentation"

    assert classify_file_path("tests/test_analyzer.py") == "Tests"
    assert classify_file_path("src/components/Header.spec.tsx") == "Tests"
    assert classify_file_path("backend/__tests__/app.test.js") == "Tests"

    assert classify_file_path("app/auth/jwt_handler.py") == "Authentication"
    assert classify_file_path("services/oauth_login.go") == "Authentication"

    assert classify_file_path("models/user_account.py") == "Database / Schema"
    assert classify_file_path("alembic/versions/001_create_users.sql") == "Database / Schema"
    assert classify_file_path("prisma/schema.prisma") == "Database / Schema"

    assert classify_file_path("app/api/v1/endpoints.py") == "API / Contracts"
    assert classify_file_path("controllers/checkout_controller.rb") == "API / Contracts"
    assert classify_file_path("proto/billing_service.proto") == "API / Contracts"

    assert classify_file_path("config/settings.yaml") == "Configuration"
    assert classify_file_path("Dockerfile") == "Configuration"
    assert classify_file_path(".env.example") == "Configuration"
    assert classify_file_path("package.json") == "Configuration"

    assert classify_file_path("src/flask/app.py") == "Application Logic"
    assert classify_file_path("lib/engine.rs") == "Application Logic"


def test_detect_interface_changes_added_and_modified():
    diff_text = """diff --git a/backend/routes.py b/backend/routes.py
--- a/backend/routes.py
+++ b/backend/routes.py
@@ -10,4 +10,7 @@
-def get_user(user_id: int):
+def get_user(user_id: int, include_metadata: bool = False):
+    pass
+@app.post("/users")
+def create_user(payload: dict):
+    pass
"""
    parsed = parse_unified_diff(diff_text)
    file_diff = parsed["backend/routes.py"]
    interfaces = detect_interface_changes(file_diff)

    types = [i.change_type for i in interfaces]
    names = [i.name for i in interfaces]

    assert "modified_function" in types
    assert "get_user" in names

    assert "added_route" in types
    assert any("POST /users" in n for n in names)

    assert "added_function" in types
    assert "create_user" in names


def test_detect_interface_changes_removed_function():
    diff_text = """diff --git a/backend/legacy.py b/backend/legacy.py
--- a/backend/legacy.py
+++ b/backend/legacy.py
@@ -5,5 +5,0 @@
-def deprecated_payment_flow(card_num):
-    process_payment(card_num)
"""
    parsed = parse_unified_diff(diff_text)
    file_diff = parsed["backend/legacy.py"]
    interfaces = detect_interface_changes(file_diff)

    assert len(interfaces) == 1
    assert interfaces[0].change_type == "removed_function"
    assert interfaces[0].name == "deprecated_payment_flow"


def test_detect_no_false_interfaces_on_internal_edits():
    # An edit that only modifies an internal local variable or comment
    diff_text = """diff --git a/backend/utils.py b/backend/utils.py
--- a/backend/utils.py
+++ b/backend/utils.py
@@ -20,3 +20,3 @@
-    x = 10
+    x = 20  # updated timeout value
"""
    parsed = parse_unified_diff(diff_text)
    file_diff = parsed["backend/utils.py"]
    interfaces = detect_interface_changes(file_diff)

    # Must NOT invent fake function or class definitions
    assert len(interfaces) == 0


def test_infer_potential_impacts_labels_inferences_safely():
    from app.schemas import InterfaceChange

    iface = InterfaceChange(
        change_type="removed_function",
        name="delete_account",
        details="Function removed: delete_account()",
        line_number=42,
    )
    impacts = infer_potential_impacts(
        file_path="app/auth/account.py",
        category="Authentication",
        status="modified",
        interfaces=[iface],
    )

    assert len(impacts) >= 2
    # Must explicitly state "Potential Impact (Inferred)"
    assert all("Potential Impact (Inferred)" in imp for imp in impacts)
    # Must explicitly note that external callers were not inspected
    assert any("not inspected" in imp.lower() for imp in impacts)


def test_missing_test_changes_signal():
    # Scenario 1: Logic changed, 0 test files -> signal flagged
    logic_only_files = [
        FileImpact(file_path="app/api.py", category="API / Contracts"),
        FileImpact(file_path="app/service.py", category="Application Logic"),
    ]
    signal_msg, has_missing = evaluate_test_coverage_signal(logic_only_files)
    assert has_missing is True
    assert "Missing Test Changes Signal" in signal_msg
    assert "investigate" in signal_msg.lower()

    # Scenario 2: Logic changed, test files included -> signal NOT flagged
    mixed_files = [
        FileImpact(file_path="app/api.py", category="API / Contracts"),
        FileImpact(file_path="tests/test_api.py", category="Tests"),
    ]
    signal_msg, has_missing = evaluate_test_coverage_signal(mixed_files)
    assert has_missing is False
    assert "Tests Included" in signal_msg

    # Scenario 3: Docs only -> Non-logic
    docs_only = [FileImpact(file_path="README.md", category="Documentation")]
    signal_msg, has_missing = evaluate_test_coverage_signal(docs_only)
    assert has_missing is False
    assert "Non-logic Changes" in signal_msg


def test_build_change_impact_summary_integration():
    diff_text = """diff --git a/app/routes.py b/app/routes.py
--- a/app/routes.py
+++ b/app/routes.py
@@ -10,3 +10,4 @@
+@app.get("/items")
 def list_items():
     return []
"""
    parsed = parse_unified_diff(diff_text)
    findings = [
        RiskFinding(
            id="RISK-1",
            category="API Contract",
            severity="MEDIUM",
            summary="New unauthenticated endpoint exposed",
            explanation="Route is exposed without auth middleware",
            uncertainty="Caller context outside diff not inspected",
            evidence=[
                FileEvidence(
                    file_path="app/routes.py",
                    line_start=10,
                    line_end=11,
                    snippet='@app.get("/items")',
                    is_verified_in_diff=True,
                    is_changed_line=True,
                )
            ],
            suggested_tests=["Test that /items requires authorization headers"],
        )
    ]
    diff_summary = DiffSummary(
        total_files=1,
        files_analyzed=["app/routes.py"],
        total_lines=15,
        truncated=False,
    )

    summary = build_change_impact_summary(parsed, findings, diff_summary)

    assert summary.total_files_analyzed == 1
    assert "API / Contracts" in summary.category_counts
    assert summary.has_missing_tests_signal is True
    assert "context boundary" in summary.context_limitation_note.lower()

    file_impact = summary.files[0]
    assert file_impact.file_path == "app/routes.py"
    assert "RISK-1" in file_impact.associated_finding_ids
    assert len(file_impact.detected_interfaces) > 0
    assert file_impact.detected_interfaces[0].name == "GET /items"


def test_incorrect_impact_claims_prevented():
    """
    Ensures the impact analyzer does NOT claim to know downstream callers outside the diff
    and does NOT claim dependencies that cannot be proven from visible lines.
    """
    diff_text = """diff --git a/backend/logic.py b/backend/logic.py
--- a/backend/logic.py
+++ b/backend/logic.py
@@ -1,3 +1,3 @@
-TOTAL_RETRIES = 3
+TOTAL_RETRIES = 5
"""
    parsed = parse_unified_diff(diff_text)
    diff_summary = DiffSummary(
        total_files=1,
        files_analyzed=["backend/logic.py"],
        total_lines=5,
        truncated=False,
    )
    summary = build_change_impact_summary(parsed, [], diff_summary)

    # 1. No callers outside diff should be claimed
    for f in summary.files:
        for imp in f.potential_downstream_impacts:
            # Any impact statement must qualify that callers outside diff were not inspected
            assert "inferred" in imp.lower() or "not inspected" in imp.lower()

    # 2. Context limitation note must explicitly state callers were not retrieved
    assert "not retrieved" in summary.context_limitation_note.lower()


def test_missing_context_truncation_boundary():
    """
    Verifies that when a PR diff is truncated, the impact summary explicitly discloses
    that additional modified files and context may exist outside the sample.
    """
    diff_text = """diff --git a/backend/app.py b/backend/app.py
--- a/backend/app.py
+++ b/backend/app.py
@@ -1,2 +1,2 @@
-x = 1
+x = 2
"""
    parsed = parse_unified_diff(diff_text)
    diff_summary = DiffSummary(
        total_files=10,
        files_analyzed=["backend/app.py"],
        total_lines=1500,
        truncated=True,
        truncation_reason="Diff exceeded maximum line limit",
    )
    summary = build_change_impact_summary(parsed, [], diff_summary)
    assert "bounded" in summary.context_limitation_note.lower()
    assert "additional modified files may exist" in summary.context_limitation_note.lower()

