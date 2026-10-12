import pytest
from unittest.mock import AsyncMock, patch
import httpx

from app.analyzer import PRAnalyzerService
from app.config import Settings
from app.github_client import GitHubClient
from app.model_adapter import ModelAdapter, ModelProviderError
from app.schemas import DiffSummary, PRMetadata


@pytest.mark.asyncio
async def test_analyzer_missing_model_key():
    mock_settings = Settings(_env_file=None, GROQ_API_KEY="")
    adapter = ModelAdapter(settings=mock_settings)
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
        "model_name": "qwen/qwen3.8-27b",
        "model_license": "Apache 2.0 (Open Weights)",
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
    assert res.findings[0].evidence[0].is_changed_line is True
    assert res.model_info.model_name == "qwen/qwen3.8-27b"


def test_model_license_resolution():
    s = Settings(_env_file=None, MODEL_PROVIDER="groq", MODEL_NAME="qwen/qwen3.8-27b")
    adapter = ModelAdapter(settings=s)
    details = adapter.get_provider_details()
    assert details["model_name"] == "qwen/qwen3.8-27b"
    assert "Apache 2.0" in details["model_license"]
    assert "Llama" not in details["model_license"]


@pytest.mark.asyncio
async def test_model_adapter_rate_limit_429():
    mock_settings = Settings(_env_file=None, GROQ_API_KEY="test_key", MODEL_PROVIDER="groq")
    adapter = ModelAdapter(settings=mock_settings)

    mock_resp = AsyncMock(spec=httpx.Response)
    mock_resp.status_code = 429
    mock_resp.text = "Rate limit reached"

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        with pytest.raises(ModelProviderError) as exc_info:
            await adapter.analyze_diff("Title", "Desc", ["f.py"], "diff", False)
        assert exc_info.value.status_code == 429
        assert "rate limit" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_model_adapter_empty_response():
    mock_settings = Settings(_env_file=None, GROQ_API_KEY="test_key", MODEL_PROVIDER="groq")
    adapter = ModelAdapter(settings=mock_settings)

    mock_resp = AsyncMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "   "}}]
    }

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        with pytest.raises(ModelProviderError) as exc_info:
            await adapter.analyze_diff("Title", "Desc", ["f.py"], "diff", False)
        assert exc_info.value.status_code == 502
        assert "empty response" in exc_info.value.message.lower()


def test_model_adapter_extract_json_markdown():
    adapter = ModelAdapter(settings=Settings(_env_file=None))
    markdown_wrapped = """Here is the analysis:
```json
{
  "overall_risk_score": "LOW",
  "summary_assessment": "Clean documentation changes",
  "observed_facts": ["Docs updated"],
  "findings": []
}
```
Hope this helps!"""
    res = adapter._extract_json(markdown_wrapped)
    validated = adapter._validate_model_structure(res)
    assert validated["overall_risk_score"] == "LOW"
    assert len(validated["findings"]) == 0


@pytest.mark.asyncio
async def test_analyzer_unverified_evidence_caveat_added():
    mock_gh = AsyncMock(spec=GitHubClient)
    pr_meta = PRMetadata(
        owner="org",
        repo="repo",
        pr_number=1,
        title="PR",
        author="user",
        state="open",
        created_at="2026-10-12T00:00:00Z",
        html_url="https://github.com/org/repo/pull/1",
        body="",
        changed_files_count=1,
        additions=1,
        deletions=0,
        base_branch="main",
        head_branch="patch",
    )
    diff_text = """diff --git a/safe.py b/safe.py
@@ -1,1 +1,2 @@
+x = 1
"""
    diff_summary = DiffSummary(total_files=1, files_analyzed=["safe.py"], total_lines=2, truncated=False)
    mock_gh.fetch_pr_details.return_value = (pr_meta, diff_text, diff_summary)

    mock_model = AsyncMock(spec=ModelAdapter)
    mock_model.get_provider_details.return_value = {
        "provider": "Groq",
        "model_name": "qwen/qwen3.8-27b",
        "model_license": "Apache 2.0 (Open Weights)",
    }
    # Model hallucinates code in "auth.py" which does not exist in the diff
    mock_model.analyze_diff.return_value = {
        "overall_risk_score": "HIGH",
        "summary_assessment": "Hallucinated issue.",
        "findings": [
            {
                "id": "RISK-1",
                "category": "Security",
                "severity": "HIGH",
                "summary": "Fake vulnerability",
                "explanation": "No evidence.",
                "uncertainty": "Uncertain context.",
                "evidence": [
                    {
                        "file_path": "auth.py",
                        "snippet": "os.system(user_input)",
                        "line_start": 50,
                    }
                ],
                "suggested_tests": [],
            }
        ],
    }

    service = PRAnalyzerService(github_client=mock_gh, model_adapter=mock_model)
    res = await service.analyze_pr_url("https://github.com/org/repo/pull/1")

    assert len(res.findings) == 1
    # Evidence must be flagged unverified
    assert res.findings[0].evidence[0].is_verified_in_diff is False
    # Caveat must be appended to uncertainty
    assert "CAVEAT" in res.findings[0].uncertainty
