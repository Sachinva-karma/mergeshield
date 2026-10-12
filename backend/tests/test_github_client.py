import pytest
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


def test_parse_invalid_pr_urls():
    invalid_urls = [
        "",
        "https://gitlab.com/owner/repo/merge_requests/1",
        "https://github.com/owner/repo",
        "https://github.com/owner/repo/pull/notanumber",
        "random-string",
    ]
    for url in invalid_urls:
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
