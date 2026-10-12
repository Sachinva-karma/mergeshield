import pytest
from unittest.mock import AsyncMock, patch

from app.analyzer import PRAnalyzerService
from app.github_client import GitHubClient
from app.model_adapter import ModelAdapter, ModelProviderError
from app.schemas import DiffSummary, PRMetadata


@pytest.mark.asyncio
async def test_analyzer_missing_model_key():
    # If no key is set for Groq, it should raise ModelProviderError
    with patch.dict("os.environ", {"GROQ_API_KEY": ""}, clear=True):
        adapter = ModelAdapter()
        with pytest.raises(ModelProviderError) as exc_info:
            await adapter.analyze_diff("Title", "Desc", [], "diff", False)
        assert exc_info.value.status_code == 503
        assert "GROQ_API_KEY" in exc_info.value.message


@pytest.mark.asyncio
async def test_analyzer_end_to_end_mocked():
    mock_gh = AsyncMock(spec=GitHubClient)
    pr_meta = PRMetadata(
        owner="octocat",
        repo="Hello-World",
        pr_number=42,
        title="Add feature",
        author="octocat",
        state="open",
        created_at="2026-10-12T00:00:00Z",
        html_url="https://github.com/octocat/Hello-World/pull/42",
        body="PR description",
        changed_files_count=1,
        additions=5,
        deletions=1,
        base_branch="main",
        head_branch="feature",
    )
    diff_text = """diff --git a/app.py b/app.py
@@ -1,3 +1,4 @@
 def run():
+    password = "hardcoded_secret"
     return True
"""
    diff_summary = DiffSummary(
        total_files=1,
        files_analyzed=["app.py"],
        total_lines=4,
        truncated=False,
    )
    mock_gh.fetch_pr_details.return_value = (pr_meta, diff_text, diff_summary)

    mock_model = AsyncMock(spec=ModelAdapter)
    mock_model.get_provider_details.return_value = {
        "provider": "Groq",
        "model_name": "llama-3.3-70b-versatile",
        "model_license": "Llama 3.3 Community License (Open Weights)",
    }
    mock_model.analyze_diff.return_value = {
        "overall_risk_score": "HIGH",
        "summary_assessment": "Hardcoded secret detected.",
        "observed_facts": ["1 file modified"],
        "findings": [
            {
                "id": "RISK-1",
                "category": "Security",
                "severity": "HIGH",
                "summary": "Hardcoded credential",
                "explanation": "Secret is exposed in code.",
                "uncertainty": "May be a test credential.",
                "evidence": [
                    {
                        "file_path": "app.py",
                        "snippet": 'password = "hardcoded_secret"',
                        "line_start": 2,
                        "line_end": 2,
                    }
                ],
                "suggested_tests": ["Verify secret rotation"],
            }
        ],
    }

    service = PRAnalyzerService(github_client=mock_gh, model_adapter=mock_model)
    res = await service.analyze_pr_url("https://github.com/octocat/Hello-World/pull/42")

    assert res.overall_risk_score == "HIGH"
    assert len(res.findings) == 1
    assert res.findings[0].evidence[0].is_verified_in_diff is True
    assert res.model_info.model_name == "llama-3.3-70b-versatile"
