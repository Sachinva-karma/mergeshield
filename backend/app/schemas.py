from typing import List, Optional
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


class RiskFinding(BaseModel):
    id: str
    category: str = Field(..., description="e.g. Security, Error Handling, Concurrency, Regression, Resource Leak, API Contract")
    severity: str = Field(..., description="HIGH, MEDIUM, or LOW")
    summary: str
    explanation: str
    uncertainty: str = Field(..., description="Explicit statement of what is unknown or requires additional repository context")
    evidence: List[FileEvidence]
    suggested_tests: List[str] = Field(default_factory=list, description="Concrete verification tests to confirm or disprove the risk")


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


class AnalysisResponse(BaseModel):
    pr: PRMetadata
    diff_summary: DiffSummary
    model_info: ModelInfo
    overall_risk_score: str = Field(..., description="LOW, MEDIUM, or HIGH")
    summary_assessment: str
    observed_facts: List[str] = Field(default_factory=list)
    findings: List[RiskFinding] = Field(default_factory=list)
