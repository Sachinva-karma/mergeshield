import React, { useState } from 'react';
import { CheckCircle2, AlertTriangle, FileCode, CheckSquare } from 'lucide-react';

export default function RiskCard({ finding }) {
  const [checkedTests, setCheckedTests] = useState({});

  const toggleTest = (idx) => {
    setCheckedTests((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  return (
    <article className="finding-card" id={`finding-${finding.id}`}>
      <div className="finding-header">
        <div>
          <div className="finding-badges">
            <span className={`severity-pill ${finding.severity}`}>
              {finding.severity} Risk
            </span>
            <span className="category-pill">{finding.category}</span>
          </div>
          <h4 className="finding-title">{finding.summary}</h4>
        </div>
      </div>

      <div className="finding-body">
        <p className="finding-explanation">{finding.explanation}</p>

        {finding.uncertainty && (
          <div className="uncertainty-box">
            <strong>Context Uncertainty: </strong>
            {finding.uncertainty}
          </div>
        )}

        {/* Verbatim Grounded Evidence */}
        {finding.evidence && finding.evidence.length > 0 && (
          <div className="evidence-section">
            <div className="evidence-header">Supporting Diff Evidence</div>
            {finding.evidence.map((ev, idx) => (
              <div key={idx} className="evidence-block">
                <div className="evidence-file-tag">
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                    <FileCode size={13} />
                    <strong>{ev.file_path}</strong>
                    {ev.line_start && <span>(Lines {ev.line_start}{ev.line_end ? `-${ev.line_end}` : ''})</span>}
                  </span>

                  {ev.is_verified_in_diff ? (
                    <span className="evidence-verified" title="Verified against retrieved PR diff lines">
                      <CheckCircle2 size={13} /> Verified in Diff
                    </span>
                  ) : (
                    <span className="evidence-unverified" title="Snippet could not be verified in the retrieved diff">
                      <AlertTriangle size={13} /> Unverified Caveat
                    </span>
                  )}
                </div>
                <pre className="evidence-code">{ev.snippet}</pre>
              </div>
            ))}
          </div>
        )}

        {/* Verification Tests */}
        {finding.suggested_tests && finding.suggested_tests.length > 0 && (
          <div className="tests-section">
            <div className="tests-header">Suggested Verification Tests</div>
            <ul className="tests-list">
              {finding.suggested_tests.map((test, idx) => (
                <li key={idx} className="test-item">
                  <input
                    type="checkbox"
                    id={`test-${finding.id}-${idx}`}
                    className="test-checkbox"
                    checked={!!checkedTests[idx]}
                    onChange={() => toggleTest(idx)}
                  />
                  <label htmlFor={`test-${finding.id}-${idx}`} style={{ cursor: 'pointer', textDecoration: checkedTests[idx] ? 'line-through' : 'none' }}>
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
