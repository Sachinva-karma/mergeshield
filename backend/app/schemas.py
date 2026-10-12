from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class PRAnalyzeRequest(BaseModel):
    pr_url: str = Field(..., description="Public GitHub Pull Request URL, e.g. https://github.com/owner/repo/pull/123")


class PRMetadata(BaseModel):
    owner: str
    repo: str
    pr_number: int
    title: str
    author: str
    state: str
    created_at: str
    html_url: str
    body: Optional[str] = None
    changed_files_count: int
    additions: int
    deletions: int
    base_branch: str
    head_branch: str


class FileEvidence(BaseModel):
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    snippet: str = Field(..., description="Verbatim code snippet from the diff")
    is_verified_in_diff: bool = Field(True, description="True if snippet was verified against actual diff content")
    is_changed_line: bool = Field(True, description="True if snippet resides within modified lines (+/-), False if surrounding context")


class VerificationAction(BaseModel):
    action_type: str = Field(..., description="unit_test | integration_test | api_contract | auth_permission | input_validation | regression | manual_review")
    what_to_verify: str
    why_it_matters: str
    expected_behavior: str
    suggested_scenario: Optional[str] = None
    motivating_file: Optional[str] = None
    is_executed: bool = Field(False, description="Explicitly False: suggested for developer verification, not executed by auditor")


class RiskFinding(BaseModel):
    id: str
    category: str = Field(..., description="e.g. Security, Error Handling, Concurrency, Regression, Resource Leak, API Contract")
    severity: str = Field(..., description="HIGH, MEDIUM, or LOW")
    summary: str
    explanation: str
    uncertainty: str = Field(..., description="Explicit statement of what is unknown or requires additional repository context")
    evidence: List[FileEvidence]
    suggested_tests: List[str] = Field(default_factory=list, description="Concrete verification tests to confirm or disprove the risk")
    priority: str = Field("Normal", description="Urgent, High, Normal, or Low")
    priority_reasoning: Optional[str] = None
    evidence_strength: str = Field("Verified in Diff", description="Verified in Diff, Plausible (Context Only), or Speculative (Ungrounded)")
    verification_plan: List[VerificationAction] = Field(default_factory=list)


class DiffSummary(BaseModel):
    total_files: int
    files_analyzed: List[str]
    total_lines: int
    truncated: bool
    truncation_reason: Optional[str] = None


class ModelInfo(BaseModel):
    provider: str
    model_name: str
    model_license: str
    grounding_enforced: bool = True


class InterfaceChange(BaseModel):
    change_type: str = Field(..., description="e.g. added_function, modified_function, removed_function, added_class, added_route, modified_config")
    name: str = Field(..., description="Name of the function, class, route, or interface")
    details: Optional[str] = None
    line_number: Optional[int] = None


class FileImpact(BaseModel):
    file_path: str
    status: str = Field("modified", description="modified, added, deleted, or renamed")
    old_path: Optional[str] = None
    category: str = Field(..., description="API / Contracts, Authentication, Database / Schema, Configuration, Tests, Application Logic, Documentation, or Other")
    additions: int = 0
    deletions: int = 0
    detected_interfaces: List[InterfaceChange] = Field(default_factory=list)
    associated_finding_ids: List[str] = Field(default_factory=list)
    potential_downstream_impacts: List[str] = Field(default_factory=list)


class ChangeImpactSummary(BaseModel):
    total_files_analyzed: int
    category_counts: Dict[str, int] = Field(default_factory=dict)
    test_coverage_signal: str = Field(..., description="Signal regarding presence or absence of test updates")
    has_missing_tests_signal: bool = False
    context_limitation_note: str = Field(
        default="Context boundary: Downstream callers and repository-wide usages outside this pull request diff were not retrieved. Impact is strictly limited to directly visible diff changes."
    )
    files: List[FileImpact] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    pr: PRMetadata
    diff_summary: DiffSummary
    model_info: ModelInfo
    overall_risk_score: str = Field(..., description="LOW, MEDIUM, or HIGH")
    summary_assessment: str
    observed_facts: List[str] = Field(default_factory=list)
    findings: List[RiskFinding] = Field(default_factory=list)
    change_impact: Optional[ChangeImpactSummary] = None
