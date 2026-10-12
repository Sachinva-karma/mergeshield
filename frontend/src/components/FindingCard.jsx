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
      <div className="finding-card-header">
        <div className="finding-badge-row">
          <span className={`badge-severity ${finding.severity}`}>
            {finding.severity} Risk
          </span>
          <span className="badge-category">{finding.category}</span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace' }}>
            {finding.id}
          </span>
        </div>
        <h3 className="finding-heading">{finding.summary}</h3>
      </div>

      <div className="finding-card-body">
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

        {/* Recommended Verification Checklist */}
        {finding.suggested_tests && finding.suggested_tests.length > 0 && (
          <div className="checklist-card">
            <h4 className="checklist-title">
              <CheckSquare size={14} color="var(--primary-violet)" />
              Recommended Verification Checklist
            </h4>
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
          </div>
        )}
      </div>
    </article>
  );
}
