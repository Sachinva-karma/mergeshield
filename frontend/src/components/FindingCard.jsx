import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  FileCode,
  CheckSquare,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

export default function FindingCard({ finding }) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isEvidenceOpen, setIsEvidenceOpen] = useState(true);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [checkedTests, setCheckedTests] = useState({});

  const toggleTest = (idx) => {
    setCheckedTests((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const handleCopySnippet = (snippet, idx) => {
    navigator.clipboard.writeText(snippet);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <article className="finding-card-stitch" id={`finding-${finding.id}`}>
      <div
        className="finding-card-header"
        onClick={() => setIsExpanded(!isExpanded)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && setIsExpanded(!isExpanded)}
        style={{ cursor: 'pointer', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}
        aria-expanded={isExpanded}
      >
        <div style={{ flex: 1 }}>
          <div className="finding-badge-row">
            {finding.priority && (
              <span className={`badge-priority priority-${finding.priority.toLowerCase()}`}>
                {finding.priority} Priority
              </span>
            )}
            <span className={`badge-severity ${finding.severity}`}>
              {finding.severity} Severity
            </span>
            <span className="badge-category">{finding.category}</span>
            {finding.evidence_strength && (
              <span className={`badge-evidence-strength strength-${finding.evidence_strength.includes('Verified') ? 'verified' : finding.evidence_strength.includes('Plausible') ? 'plausible' : 'speculative'}`}>
                {finding.evidence_strength}
              </span>
            )}
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace' }}>
              {finding.id}
            </span>
          </div>
          <h3 className="finding-heading">{finding.summary}</h3>
        </div>

        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            setIsExpanded(!isExpanded);
          }}
          aria-label={isExpanded ? "Collapse finding details" : "Expand finding details"}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            padding: '4px',
          }}
        >
          {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>
      </div>

      {isExpanded && (
        <div className="finding-card-body">
        {finding.priority_reasoning && (
          <div className="priority-reasoning-callout">
            <span className="reasoning-label">Prioritization Rationale:</span>
            <span className="reasoning-text">{finding.priority_reasoning}</span>
          </div>
        )}

        <p className="finding-explanation-text">{finding.explanation}</p>

        {finding.uncertainty && (
          <div className="uncertainty-callout">
            <strong>Context Uncertainty: </strong>
            {finding.uncertainty}
          </div>
        )}

        {/* Supporting Diff Evidence */}
        {finding.evidence && finding.evidence.length > 0 && (
          <div className="evidence-container">
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '0.4rem',
              }}
            >
              <span className="evidence-label">Supporting Diff Evidence</span>
              <button
                type="button"
                onClick={() => setIsEvidenceOpen(!isEvidenceOpen)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.2rem',
                  fontSize: '11px',
                }}
              >
                {isEvidenceOpen ? (
                  <>Hide diff <ChevronUp size={13} /></>
                ) : (
                  <>Show diff <ChevronDown size={13} /></>
                )}
              </button>
            </div>

            {isEvidenceOpen &&
              finding.evidence.map((ev, idx) => (
                <div key={idx} className="evidence-pane">
                  <div className="evidence-pane-bar">
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
                      <FileCode size={13} />
                      <strong>{ev.file_path}</strong>
                      {ev.line_start && (
                        <span>
                          (L{ev.line_start}
                          {ev.line_end ? `-${ev.line_end}` : ''})
                        </span>
                      )}
                    </span>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      {ev.is_changed_line !== undefined && (
                        ev.is_changed_line ? (
                          <span style={{ fontSize: '10px', padding: '1px 5px', borderRadius: '3px', backgroundColor: 'var(--diff-add-bg)', color: 'var(--emerald)', fontWeight: 600 }}>
                            Modified Line
                          </span>
                        ) : (
                          <span style={{ fontSize: '10px', padding: '1px 5px', borderRadius: '3px', backgroundColor: 'var(--surface-secondary)', color: 'var(--text-muted)', fontWeight: 500 }}>
                            Surrounding Context
                          </span>
                        )
                      )}

                      {ev.is_verified_in_diff ? (
                        <span className="evidence-status-pill verified" title="Snippet strictly verified in retrieved diff">
                          <CheckCircle2 size={13} /> Verified in Diff
                        </span>
                      ) : (
                        <span className="evidence-status-pill unverified" title="Snippet could not be verified in retrieved diff">
                          <AlertTriangle size={13} /> Unverified Caveat
                        </span>
                      )}

                      <button
                        type="button"
                        onClick={() => handleCopySnippet(ev.snippet, idx)}
                        title="Copy snippet"
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'var(--text-secondary)',
                          cursor: 'pointer',
                          display: 'inline-flex',
                          alignItems: 'center',
                        }}
                      >
                        {copiedIndex === idx ? (
                          <Check size={13} color="var(--emerald)" />
                        ) : (
                          <Copy size={13} />
                        )}
                      </button>
                    </div>
                  </div>

                  <pre className="evidence-code-block">{ev.snippet}</pre>
                </div>
              ))}
          </div>
        )}

        {/* Smart Verification Planner */}
        {((finding.verification_plan && finding.verification_plan.length > 0) || (finding.suggested_tests && finding.suggested_tests.length > 0)) && (
          <div className="checklist-card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.65rem' }}>
              <h4 className="checklist-title" style={{ marginBottom: 0 }}>
                <CheckSquare size={14} color="var(--primary-violet)" />
                Actionable Verification Plan
              </h4>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                Suggested only • Not executed by auditor
              </span>
            </div>

            {finding.verification_plan && finding.verification_plan.length > 0 ? (
              <div className="verification-actions-list">
                {finding.verification_plan.map((action, idx) => (
                  <div key={idx} className="verification-action-card">
                    <div className="action-card-header">
                      <span className="action-type-badge">{action.action_type.replace('_', ' ')}</span>
                      {action.motivating_file && (
                        <span className="action-file-badge">{action.motivating_file}</span>
                      )}
                    </div>

                    <div className="checklist-row" style={{ marginTop: '0.4rem', marginBottom: '0.4rem' }}>
                      <input
                        type="checkbox"
                        id={`test-${finding.id}-${idx}`}
                        className="checklist-checkbox"
                        checked={!!checkedTests[idx]}
                        onChange={() => toggleTest(idx)}
                      />
                      <label
                        htmlFor={`test-${finding.id}-${idx}`}
                        style={{
                          cursor: 'pointer',
                          textDecoration: checkedTests[idx] ? 'line-through' : 'none',
                          color: checkedTests[idx] ? 'var(--text-muted)' : 'var(--text-primary)',
                          fontWeight: 500,
                          fontSize: '13px',
                        }}
                      >
                        {action.what_to_verify}
                      </label>
                    </div>

                    <div className="action-details-block">
                      <div className="action-detail-row">
                        <span className="action-detail-label">Why it matters:</span>
                        <span className="action-detail-val">{action.why_it_matters}</span>
                      </div>
                      <div className="action-detail-row">
                        <span className="action-detail-label">Expected behavior:</span>
                        <span className="action-detail-val">{action.expected_behavior}</span>
                      </div>
                      {action.suggested_scenario && (
                        <div className="action-detail-row">
                          <span className="action-detail-label">Suggested test:</span>
                          <code className="action-detail-code">{action.suggested_scenario}</code>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <ul className="checklist-items">
                {finding.suggested_tests.map((test, idx) => (
                  <li key={idx} className="checklist-row">
                    <input
                      type="checkbox"
                      id={`test-${finding.id}-${idx}`}
                      className="checklist-checkbox"
                      checked={!!checkedTests[idx]}
                      onChange={() => toggleTest(idx)}
                    />
                    <label
                      htmlFor={`test-${finding.id}-${idx}`}
                      style={{
                        cursor: 'pointer',
                        textDecoration: checkedTests[idx] ? 'line-through' : 'none',
                        color: checkedTests[idx] ? 'var(--text-muted)' : 'var(--text-secondary)',
                      }}
                    >
                      {test}
                    </label>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
      )}
    </article>
  );
}
