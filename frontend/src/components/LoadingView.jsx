import React from 'react';

export default function LoadingView({ message = "Inspecting pull request changes..." }) {
  return (
    <div className="loading-box" role="status" aria-live="polite">
      <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>
        {message}
      </div>
      <div className="progress-bar-container">
        <div className="progress-bar-fill" />
      </div>
      <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
        Retrieving bounded diff, parsing unified hunks, and validating ground truth evidence...
      </div>
    </div>
  );
}
