import React, { useState } from 'react';
import {
  ExternalLink,
  ArrowLeft,
  GitPullRequest,
  GitBranch,
  FileText,
  AlertTriangle,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Info,
  Download,
} from 'lucide-react';
import FindingCard from './FindingCard';
import CleanResult from './CleanResult';
import ChangeImpactMap from './ChangeImpactMap';
import { downloadMarkdownReport } from '../utils/reportExporter';

export default function AnalysisView({ analysis, onNewAnalysis }) {
  const [isTransparencyOpen, setIsTransparencyOpen] = useState(false);
  const pr = analysis?.pr;
  const findings = analysis?.findings || [];
  const diffSummary = analysis?.diff_summary;
  const modelInfo = analysis?.model_info;

  return (
    <section className="analysis-view" aria-label="PR Analysis Report">
      {/* Top action row */}
      <div className="nav-back-row">
        <button type="button" className="btn-secondary" onClick={onNewAnalysis}>
          <ArrowLeft size={14} />
          <span>New URL</span>
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <button
            type="button"
            className="btn-primary"
            onClick={() => downloadMarkdownReport(analysis)}
            style={{ padding: '0.45rem 0.9rem', fontSize: '13px', display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
            title="Download evidence-grounded Markdown audit report"
          >
            <Download size={14} />
            <span>Export Report (.md)</span>
          </button>

          <a
            href={pr.html_url}
            target="_blank"
            rel="noreferrer"
            className="btn-secondary"
            style={{ textDecoration: 'none' }}
          >
            <span>View on GitHub</span>
            <ExternalLink size={13} />
          </a>
        </div>
      </div>

      {/* PR Metadata Card */}
      <div className="pr-header-card">
        <div className="pr-header-top">
          <h2 className="pr-title-text">{pr.title}</h2>
        </div>

        <div className="pr-meta-chips">
          <span className="meta-chip">
            <GitPullRequest size={13} color="var(--primary-violet)" />
            <span>{pr.owner}/{pr.repo}#{pr.pr_number}</span>
          </span>
          <span className="meta-chip">
            <span>by <strong>@{pr.author}</strong></span>
          </span>
          <span className="meta-chip">
            <GitBranch size={13} />
            <code>{pr.base_branch}</code> &larr; <code>{pr.head_branch}</code>
          </span>
          <span className="meta-chip">
            <FileText size={13} />
            <span>{pr.changed_files_count} files (+{pr.additions} / -{pr.deletions})</span>
          </span>
        </div>

        {/* Overall Risk Banner */}
        <div className={`risk-banner ${analysis.overall_risk_score}`}>
          <div>
            <div className="risk-banner-title">
              {analysis.overall_risk_score === 'HIGH' && <AlertTriangle size={18} />}
              {analysis.overall_risk_score === 'MEDIUM' && <AlertTriangle size={18} />}
              {analysis.overall_risk_score === 'LOW' && <ShieldCheck size={18} />}
              <span>Overall Risk: {analysis.overall_risk_score}</span>
            </div>
            <p className="risk-banner-desc">{analysis.summary_assessment}</p>
          </div>
        </div>

        {/* Truncated Diff Notice if applicable */}
        {diffSummary?.truncated && (
          <div className="uncertainty-callout" style={{ marginTop: '1rem', borderLeftColor: 'var(--amber)' }}>
            <strong>Diff Bounded: </strong>
            {diffSummary.truncation_reason} ({diffSummary.total_lines} lines analyzed to maintain deterministic context limits).
          </div>
        )}
      </div>

      {/* Observed Facts (Clearly separated from inferred risks) */}
      {analysis.observed_facts && analysis.observed_facts.length > 0 && (
        <div className="facts-container">
          <div className="facts-title">
            <Info size={14} color="var(--primary-violet)" />
            <span>Observed Facts (Retrieved Context)</span>
          </div>
          <ul className="facts-list-grid">
            {analysis.observed_facts.map((fact, idx) => (
              <li key={idx} className="facts-item">{fact}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Change Impact Map */}
      {analysis.change_impact && (
        <ChangeImpactMap impact={analysis.change_impact} />
      )}

      {/* Findings Section */}
      <div className="section-headline-row">
        <h3 className="section-title">Review findings</h3>
        <span className="section-count-badge">
          {findings.length} {findings.length === 1 ? 'Finding' : 'Findings'}
        </span>
      </div>

      {findings.length === 0 ? (
        <CleanResult analysis={analysis} />
      ) : (
        <div className="findings-stack">
          {findings.map((f) => (
            <FindingCard key={f.id} finding={f} />
          ))}
        </div>
      )}

      {/* Expandable Transparency Section */}
      <div className="transparency-section">
        <div
          className="transparency-summary"
          onClick={() => setIsTransparencyOpen(!isTransparencyOpen)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && setIsTransparencyOpen(!isTransparencyOpen)}
        >
          <span>How this assessment was produced</span>
          {isTransparencyOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>

        {isTransparencyOpen && (
          <div className="transparency-content">
            <p>
              This audit was produced by inspecting raw unified diffs retrieved directly via the official GitHub REST API. Every proposed finding has been cross-checked against verbatim hunk additions/deletions.
            </p>
            <div className="transparency-grid">
              <div className="transparency-stat-box">
                <div className="transparency-stat-label">Model</div>
                <div className="transparency-stat-val">{modelInfo?.model_name || 'qwen/qwen3.8-27b'}</div>
              </div>
              <div className="transparency-stat-box">
                <div className="transparency-stat-label">Model License</div>
                <div className="transparency-stat-val">{modelInfo?.model_license || 'Apache 2.0 (Open Weights)'}</div>
              </div>
              <div className="transparency-stat-box">
                <div className="transparency-stat-label">Provider</div>
                <div className="transparency-stat-val">{modelInfo?.provider || 'Groq Cloud'}</div>
              </div>
              <div className="transparency-stat-box">
                <div className="transparency-stat-label">Grounding Verification</div>
                <div className="transparency-stat-val" style={{ color: 'var(--emerald)' }}>
                  Enforced (Diff Hunk Matching)
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
