import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

export default function ErrorView({ error, onRetry, onReset }) {
  const isRateLimit = error?.toLowerCase().includes('rate limit');
  const isModelUnavailable = error?.toLowerCase().includes('api_key') || error?.toLowerCase().includes('model');
  const isNotFound = error?.toLowerCase().includes('not found');

  let title = "Analysis Failed";
  let guidance = error || "An unexpected error occurred while communicating with the backend.";

  if (isRateLimit) {
    title = "GitHub API Rate Limit Reached";
    guidance = "GitHub's public rate limit (60 requests/hr) was exceeded. You can configure a GITHUB_TOKEN in your backend .env to increase the limit to 5,000/hr.";
  } else if (isModelUnavailable) {
    title = "Model Provider Credentials Missing";
    guidance = "The open-weight model API key is not configured in the backend. Add GROQ_API_KEY to your .env file and retry.";
  } else if (isNotFound) {
    title = "Pull Request Not Found";
    guidance = "The pull request was not found or is private. Verify the URL is public and formatted like: https://github.com/owner/repo/pull/123.";
  }

  return (
    <div className="error-card" role="alert">
      <AlertCircle size={22} className="error-icon" />
      <div style={{ flex: 1 }}>
        <h3 className="error-title">{title}</h3>
        <p className="error-desc">{guidance}</p>
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.85rem' }}>
          {onRetry && (
            <button type="button" className="error-action-btn" onClick={onRetry}>
              <RefreshCw size={12} style={{ display: 'inline', marginRight: '4px' }} />
              Retry Analysis
            </button>
          )}
          {onReset && (
            <button type="button" className="error-action-btn" onClick={onReset}>
              Enter Different URL
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
