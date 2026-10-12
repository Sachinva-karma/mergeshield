import pytest
from unittest.mock import AsyncMock, patch
import httpx
from app.github_client import GitHubClient, GitHubClientError, parse_github_pr_url


def test_parse_valid_pr_urls():
    urls = [
        ("https://github.com/facebook/react/pull/12345", ("facebook", "react", 12345)),
        ("http://github.com/torvalds/linux/pull/1", ("torvalds", "linux", 1)),
        ("https://www.github.com/owner/repo/pull/42/", ("owner", "repo", 42)),
        ("https://github.com/org-name/repo_name.js/pull/99?diff=unified#issuecomment", ("org-name", "repo_name.js", 99)),
    ]
    for url, expected in urls:
        assert parse_github_pr_url(url) == expected


def test_parse_invalid_and_malicious_urls():
    malicious_or_invalid_urls = [
        "",
        # Non-github domain / SSRF attempts
        "https://gitlab.com/owner/repo/merge_requests/1",
        "https://github.com.attacker.com/owner/repo/pull/1",
        "https://127.0.0.1/owner/repo/pull/1",
        "https://169.254.169.254/owner/repo/pull/1",
        # Embedded credentials (user:pass@)
        "https://admin:secret@github.com/owner/repo/pull/1",
        # Custom ports
        "https://github.com:8443/owner/repo/pull/1",
        # Path traversal
        "https://github.com/../../etc/passwd/pull/1",
        # Invalid PR numbers or formats
        "https://github.com/owner/repo",
        "https://github.com/owner/repo/pull/notanumber",
        "https://github.com/owner/repo/pull/-5",
        "random-string",
    ]
    for url in malicious_or_invalid_urls:
        with pytest.raises(GitHubClientError):
            parse_github_pr_url(url)


def test_bound_diff_truncation():
    client = GitHubClient()
    # Mock a large diff
    lines = [f"+line {i}" for i in range(2000)]
    diff_text = "diff --git a/file.py b/file.py\n" + "\n".join(lines)
    bounded, summary = client._bound_diff(diff_text, 1)

    assert summary.truncated is True
    assert summary.total_lines <= client.settings.MAX_DIFF_LINES
    assert "file.py" in summary.files_analyzed


@pytest.mark.asyncio
async def test_github_client_timeout():
    client = GitHubClient()
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Connection timed out")):
        with pytest.raises(GitHubClientError) as exc_info:
            await client.fetch_pr_details("owner", "repo", 1)
        assert exc_info.value.status_code == 504
        assert "timed out" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_github_client_not_found():
    client = GitHubClient()
    mock_resp = AsyncMock(spec=httpx.Response)
    mock_resp.status_code = 404
    mock_resp.text = "Not Found"

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        with pytest.raises(GitHubClientError) as exc_info:
            await client.fetch_pr_details("owner", "repo", 999)
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_github_client_rate_limited():
    client = GitHubClient()
    mock_resp = AsyncMock(spec=httpx.Response)
    mock_resp.status_code = 403
    mock_resp.headers = {"X-RateLimit-Reset": "1700000000"}

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        with pytest.raises(GitHubClientError) as exc_info:
            await client.fetch_pr_details("owner", "repo", 1)
        assert exc_info.value.status_code == 429
        assert "rate limit exceeded" in exc_info.value.message.lower()
