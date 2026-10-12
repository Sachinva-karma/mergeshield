from app.diff_parser import parse_unified_diff, verify_evidence_in_diff

SAMPLE_DIFF = """diff --git a/backend/auth.py b/backend/auth.py
index 1234567..89abcdef 100644
--- a/backend/auth.py
+++ b/backend/auth.py
@@ -10,6 +10,8 @@ def authenticate_user(token: str):
     if not token:
         raise ValueError("Token is required")
+    # Skip token verification for development
+    if token == "dev-admin-override": return True
     return verify_jwt(token)
"""

def test_parse_unified_diff():
    parsed = parse_unified_diff(SAMPLE_DIFF)
    assert "backend/auth.py" in parsed
    file_diff = parsed["backend/auth.py"]
    assert len(file_diff.hunks) == 1
    assert any("dev-admin-override" in c for _, c in file_diff.added_lines)


def test_verify_evidence_found():
    parsed = parse_unified_diff(SAMPLE_DIFF)
    is_verified, snippet = verify_evidence_in_diff(
        file_path="backend/auth.py",
        snippet='if token == "dev-admin-override": return True',
        line_start=12,
        line_end=12,
        parsed_files=parsed,
    )
    assert is_verified is True
    assert "dev-admin-override" in snippet


def test_verify_evidence_hallucination_flagged():
    parsed = parse_unified_diff(SAMPLE_DIFF)
    # File not in diff
    is_verified, _ = verify_evidence_in_diff(
        file_path="backend/payments.py",
        snippet="charge_credit_card()",
        line_start=1,
        line_end=1,
        parsed_files=parsed,
    )
    assert is_verified is False

    # Snippet not in diff
    is_verified, _ = verify_evidence_in_diff(
        file_path="backend/auth.py",
        snippet="eval(user_input)",
        line_start=15,
        line_end=15,
        parsed_files=parsed,
    )
    assert is_verified is False
