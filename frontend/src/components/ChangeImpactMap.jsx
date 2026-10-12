import React, { useState } from 'react';
import {
  Layers,
  FileCode,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Info,
  ExternalLink,
  ShieldAlert,
} from 'lucide-react';

export default function ChangeImpactMap({ impact }) {
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [expandedFiles, setExpandedFiles] = useState({});

  if (!impact || !impact.files || impact.files.length === 0) {
    return null;
  }

  const toggleFile = (filePath) => {
    setExpandedFiles((prev) => ({
      ...prev,
      [filePath]: !prev[filePath],
    }));
  };

  const categories = Object.keys(impact.category_counts || {});
  const filteredFiles =
    selectedCategory === 'ALL'
      ? impact.files
      : impact.files.filter((f) => f.category === selectedCategory);

  return (
    <div className="impact-map-container" aria-label="Change Impact Map">
      {/* Header Row */}
      <div className="impact-map-header">
        <div className="impact-title-group">
          <div className="impact-icon-badge">
            <Layers size={16} color="var(--primary-violet)" />
          </div>
          <div>
            <h3 className="impact-title">Change Impact Map</h3>
            <p className="impact-subtitle">
              Grounded file classification, detected interface modifications, and potential downstream consequences.
            </p>
          </div>
        </div>
        <span className="impact-total-badge">
          {impact.total_files_analyzed} {impact.total_files_analyzed === 1 ? 'file' : 'files'}
        </span>
      </div>

      {/* Test Coverage Signal Banner */}
      <div
        className={`test-signal-banner ${
          impact.has_missing_tests_signal ? 'signal-warning' : 'signal-neutral'
        }`}
      >
        <div className="test-signal-icon">
          {impact.has_missing_tests_signal ? (
            <AlertTriangle size={16} color="var(--amber)" />
          ) : (
            <CheckCircle2 size={16} color="var(--emerald)" />
          )}
        </div>
        <div className="test-signal-body">
          <div className="test-signal-title">
            {impact.has_missing_tests_signal ? 'Test Review Signal' : 'Test Verification Status'}
          </div>
          <p className="test-signal-text">{impact.test_coverage_signal}</p>
          {impact.has_missing_tests_signal && (
            <span className="test-signal-hint">
              Note: This is an advisory signal to investigate test coverage, not proof of a bug.
            </span>
          )}
        </div>
      </div>

      {/* Category Filter Chips */}
      <div className="category-chips-row">
        <button
          type="button"
          className={`category-chip ${selectedCategory === 'ALL' ? 'active' : ''}`}
          onClick={() => setSelectedCategory('ALL')}
        >
          <span>All Categories</span>
          <span className="chip-count">{impact.total_files_analyzed}</span>
        </button>

        {categories.map((cat) => (
          <button
            key={cat}
            type="button"
            className={`category-chip ${selectedCategory === cat ? 'active' : ''}`}
            onClick={() => setSelectedCategory(cat)}
          >
            <span>{cat}</span>
            <span className="chip-count">{impact.category_counts[cat]}</span>
          </button>
        ))}
      </div>

      {/* File Impact List */}
      <div className="impact-files-list">
        {filteredFiles.map((file) => {
          const isExpanded = !!expandedFiles[file.file_path];
          const hasDetails =
            (file.detected_interfaces && file.detected_interfaces.length > 0) ||
            (file.potential_downstream_impacts && file.potential_downstream_impacts.length > 0);

          return (
            <div key={file.file_path} className="impact-file-card">
              <div
                className="impact-file-header"
                onClick={() => hasDetails && toggleFile(file.file_path)}
                role={hasDetails ? 'button' : undefined}
                tabIndex={hasDetails ? 0 : undefined}
                onKeyDown={(e) => hasDetails && e.key === 'Enter' && toggleFile(file.file_path)}
                style={{ cursor: hasDetails ? 'pointer' : 'default' }}
              >
                <div className="file-info-left">
                  <FileCode size={15} color="var(--text-secondary)" />
                  <code className="impact-file-path">{file.file_path}</code>

                  {file.status !== 'modified' && (
                    <span className={`status-badge status-${file.status}`}>
                      {file.status.toUpperCase()}
                    </span>
                  )}

                  <span className="category-pill">{file.category}</span>
                </div>

                <div className="file-info-right">
                  <div className="diff-stats-mini">
                    {file.additions > 0 && <span className="diff-stat-add">+{file.additions}</span>}
                    {file.deletions > 0 && <span className="diff-stat-del">-{file.deletions}</span>}
                  </div>

                  {file.associated_finding_ids && file.associated_finding_ids.length > 0 && (
                    <div className="linked-findings-row">
                      {file.associated_finding_ids.map((fid) => (
                        <span key={fid} className="linked-finding-chip">
                          {fid}
                        </span>
                      ))}
                    </div>
                  )}

                  {hasDetails && (
                    <div className="expand-chevron">
                      {isExpanded ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                    </div>
                  )}
                </div>
              </div>

              {/* Expanded File Insights */}
              {isExpanded && (
                <div className="impact-file-details">
                  {/* Detected Interface Changes */}
                  {file.detected_interfaces && file.detected_interfaces.length > 0 && (
                    <div className="details-subgroup">
                      <div className="details-subtitle">
                        Directly Visible Interface Modifications (Diff Grounded):
                      </div>
                      <div className="interface-items-list">
                        {file.detected_interfaces.map((iface, idx) => (
                          <div key={idx} className="interface-item">
                            <span className="iface-type-badge">{iface.change_type.replace('_', ' ')}</span>
                            <code className="iface-name">{iface.name}</code>
                            {iface.line_number && (
                              <span className="iface-line">Line {iface.line_number}</span>
                            )}
                            {iface.details && (
                              <span className="iface-details">{iface.details}</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Potential Downstream Impacts */}
                  {file.potential_downstream_impacts &&
                    file.potential_downstream_impacts.length > 0 && (
                      <div className="details-subgroup">
                        <div className="details-subtitle">
                          Potential Downstream Consequences:
                        </div>
                        <ul className="downstream-impacts-list">
                          {file.potential_downstream_impacts.map((impactStr, idx) => (
                            <li key={idx} className="downstream-impact-item">
                              <span className="impact-bullet-label">Potential Impact (Inferred):</span>
                              <span className="impact-bullet-text">
                                {impactStr.replace(/^Potential Impact \(Inferred\):\s*/i, '')}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Context Limitation Disclosure */}
      <div className="context-limitation-footer">
        <Info size={13} color="var(--text-muted)" />
        <span>{impact.context_limitation_note}</span>
      </div>
    </div>
  );
}
