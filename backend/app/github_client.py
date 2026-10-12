import re
from typing import Dict, List, Optional, Tuple
import httpx

from app.config import get_settings
from app.schemas import DiffSummary, PRMetadata


GITHUB_PR_REGEX = re.compile(
    r"^https?://(?:www\.)?github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)/pull/(\d+)(?:[/?#].*)?$"
)


class GitHubClientError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def parse_github_pr_url(url: str) -> Tuple[str, str, int]:
    """
    Validates and parses a public GitHub PR URL.
    Returns: (owner, repo, pr_number)
    """
    if not url or not isinstance(url, str):
        raise GitHubClientError("PR URL must be a non-empty string.")

    cleaned_url = url.strip()
    match = GITHUB_PR_REGEX.match(cleaned_url)
    if not match:
        raise GitHubClientError(
            "Invalid GitHub PR URL. Expected format: https://github.com/owner/repo/pull/123"
        )

    owner, repo, pr_number_str = match.groups()
    try:
        pr_number = int(pr_number_str)
    except ValueError:
        raise GitHubClientError("Invalid PR number in URL.")

    return owner, repo, pr_number


class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.settings = get_settings()
        self.token = token or self.settings.get_github_token()
        self.base_url = "https://api.github.com"

    def _get_headers(self, custom_accept: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "User-Agent": "MergeShield-PR-Auditor/1.0",
            "Accept": custom_accept or "application/vnd.github.v3+json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def fetch_pr_details(
        self, owner: str, repo: str, pr_number: int
    ) -> Tuple[PRMetadata, str, DiffSummary]:
        """
        Fetches PR metadata, changed files, and bounded diff.
        """
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            # 1. Fetch PR metadata
            pr_url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
            resp = await client.get(pr_url, headers=self._get_headers())

            if resp.status_code == 404:
                raise GitHubClientError(
                    f"Pull request #{pr_number} on {owner}/{repo} not found. Ensure it is public and exists.",
                    status_code=404,
                )
            if resp.status_code == 403 or resp.status_code == 429:
                rate_limit_reset = resp.headers.get("X-RateLimit-Reset")
                raise GitHubClientError(
                    "GitHub API rate limit exceeded. Provide a GITHUB_TOKEN in your environment to increase limits.",
                    status_code=429,
                )
            if resp.status_code != 200:
                raise GitHubClientError(
                    f"GitHub API error ({resp.status_code}): {resp.text[:200]}",
                    status_code=resp.status_code,
                )

            data = resp.json()
            pr_metadata = PRMetadata(
                owner=owner,
                repo=repo,
                pr_number=pr_number,
                title=data.get("title", ""),
                author=data.get("user", {}).get("login", "unknown"),
                state=data.get("state", "open"),
                created_at=data.get("created_at", ""),
                html_url=data.get("html_url", f"https://github.com/{owner}/{repo}/pull/{pr_number}"),
                body=data.get("body") or "",
                changed_files_count=data.get("changed_files", 0),
                additions=data.get("additions", 0),
                deletions=data.get("deletions", 0),
                base_branch=data.get("base", {}).get("ref", "main"),
                head_branch=data.get("head", {}).get("ref", "unknown"),
            )

            # 2. Fetch raw diff
            diff_resp = await client.get(
                pr_url, headers=self._get_headers(custom_accept="application/vnd.github.v3.diff")
            )
            if diff_resp.status_code != 200:
                raise GitHubClientError(
                    f"Failed to fetch PR diff ({diff_resp.status_code}).",
                    status_code=diff_resp.status_code,
                )

            raw_diff = diff_resp.text
            bounded_diff, diff_summary = self._bound_diff(raw_diff, pr_metadata.changed_files_count)

            return pr_metadata, bounded_diff, diff_summary

    def _bound_diff(self, raw_diff: str, reported_file_count: int) -> Tuple[str, DiffSummary]:
        """
        Enforces strict limits on diff length to prevent token blowout and model latency issues.
        """
        if not raw_diff or not raw_diff.strip():
            return "", DiffSummary(
                total_files=reported_file_count,
                files_analyzed=[],
                total_lines=0,
                truncated=False,
                truncation_reason=None,
            )

        lines = raw_diff.splitlines()
        total_lines = len(lines)
        max_lines = self.settings.MAX_DIFF_LINES
        max_bytes = self.settings.MAX_DIFF_BYTES

        truncated = False
        truncation_reason = None

        # Check line limit
        if total_lines > max_lines:
            lines = lines[:max_lines]
            truncated = True
            truncation_reason = f"Diff exceeded maximum line limit ({max_lines} of {total_lines} lines shown)."

        truncated_diff = "\n".join(lines)

        # Check byte limit
        encoded = truncated_diff.encode("utf-8")
        if len(encoded) > max_bytes:
            encoded = encoded[:max_bytes]
            truncated_diff = encoded.decode("utf-8", errors="ignore")
            truncated = True
            truncation_reason = f"Diff exceeded maximum size limit ({max_bytes // 1024} KB limit applied)."

        # Extract file paths present in the diff
        files_found: List[str] = []
        for line in truncated_diff.splitlines():
            if line.startswith("diff --git "):
                parts = line.split(" ")
                if len(parts) >= 4:
                    b_file = parts[3]
                    if b_file.startswith("b/"):
                        b_file = b_file[2:]
                    if b_file not in files_found:
                        files_found.append(b_file)

        diff_summary = DiffSummary(
            total_files=reported_file_count or len(files_found),
            files_analyzed=files_found,
            total_lines=len(truncated_diff.splitlines()),
            truncated=truncated,
            truncation_reason=truncation_reason,
        )

        return truncated_diff, diff_summary
