from typing import List
from app.diff_parser import parse_unified_diff, verify_evidence_in_diff
from app.github_client import GitHubClient, parse_github_pr_url
from app.impact_analyzer import build_change_impact_summary
from app.model_adapter import ModelAdapter
from app.schemas import (
    AnalysisResponse,
    FileEvidence,
    ModelInfo,
    RiskFinding,
)


class PRAnalyzerService:
    def __init__(
        self,
        github_client: GitHubClient | None = None,
        model_adapter: ModelAdapter | None = None,
    ):
        self.github_client = github_client or GitHubClient()
        self.model_adapter = model_adapter or ModelAdapter()

    async def analyze_pr_url(self, pr_url: str) -> AnalysisResponse:
        # 1. Parse URL
        owner, repo, pr_number = parse_github_pr_url(pr_url)

        # 2. Fetch metadata & bounded diff
        pr_metadata, bounded_diff, diff_summary = await self.github_client.fetch_pr_details(
            owner, repo, pr_number
        )

        # 3. Parse diff structure for grounding checks
        parsed_files = parse_unified_diff(bounded_diff)

        # 4. Analyze via model adapter
        raw_analysis = await self.model_adapter.analyze_diff(
            pr_title=pr_metadata.title,
            pr_description=pr_metadata.body or "",
            files_touched=diff_summary.files_analyzed,
            diff_text=bounded_diff,
            is_truncated=diff_summary.truncated,
        )

        # 5. Extract and verify findings against ground truth diff
        raw_findings = raw_analysis.get("findings", [])
        verified_findings: List[RiskFinding] = []

        for idx, f in enumerate(raw_findings):
            raw_evidence = f.get("evidence", [])
            evidence_list: List[FileEvidence] = []

            has_unverified_citation = False
            for ev in raw_evidence:
                file_path = ev.get("file_path", "")
                snippet = ev.get("snippet", "")
                line_start = ev.get("line_start")
                line_end = ev.get("line_end")

                is_verified, is_changed, verified_snippet = verify_evidence_in_diff(
                    file_path=file_path,
                    snippet=snippet,
                    line_start=line_start,
                    line_end=line_end,
                    parsed_files=parsed_files,
                )

                if not is_verified:
                    has_unverified_citation = True

                evidence_list.append(
                    FileEvidence(
                        file_path=file_path,
                        line_start=line_start,
                        line_end=line_end,
                        snippet=verified_snippet or snippet,
                        is_verified_in_diff=is_verified,
                        is_changed_line=is_changed,
                    )
                )

            uncertainty = f.get("uncertainty", "Context outside this diff was not inspected.")
            if has_unverified_citation:
                uncertainty = f"{uncertainty} [CAVEAT: One or more cited code snippets were not grounded in the retrieved diff]."

            verified_findings.append(
                RiskFinding(
                    id=f.get("id") or f"RISK-{idx + 1}",
                    category=f.get("category", "General"),
                    severity=f.get("severity", "MEDIUM").upper(),
                    summary=f.get("summary", "Potential issue identified"),
                    explanation=f.get("explanation", ""),
                    uncertainty=uncertainty,
                    evidence=evidence_list,
                    suggested_tests=f.get("suggested_tests", []),
                )
            )

        provider_info = self.model_adapter.get_provider_details()
        model_info = ModelInfo(
            provider=provider_info["provider"],
            model_name=provider_info["model_name"],
            model_license=provider_info["model_license"],
            grounding_enforced=True,
        )

        # 6. Build Change Impact Map
        change_impact = build_change_impact_summary(
            parsed_files=parsed_files,
            findings=verified_findings,
            diff_summary=diff_summary,
        )

        return AnalysisResponse(
            pr=pr_metadata,
            diff_summary=diff_summary,
            model_info=model_info,
            overall_risk_score=raw_analysis.get("overall_risk_score", "MEDIUM").upper(),
            summary_assessment=raw_analysis.get("summary_assessment", "Analysis completed."),
            observed_facts=raw_analysis.get("observed_facts", [
                f"PR #{pr_number} in {owner}/{repo}",
                f"{pr_metadata.changed_files_count} file(s) modified (+{pr_metadata.additions}/-{pr_metadata.deletions})",
                f"Target branch: {pr_metadata.base_branch} <- {pr_metadata.head_branch}",
            ]),
            findings=verified_findings,
            change_impact=change_impact,
        )
