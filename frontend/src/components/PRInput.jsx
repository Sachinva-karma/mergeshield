import React, { useState } from 'react';
import { Search, ArrowRight } from 'lucide-react';

const SAMPLE_PRS = [
  {
    label: 'FastAPI #11000 (Docs)',
    url: 'https://github.com/fastapi/fastapi/pull/11000',
  },
  {
    label: 'Flask #5918 (Routing Refactor)',
    url: 'https://github.com/pallets/flask/pull/5918',
  },
  {
    label: 'Flask #5660 (Session / sansio)',
    url: 'https://github.com/pallets/flask/pull/5660',
  },
];

export default function PRInput({ onAnalyze, isLoading }) {
  const [url, setUrl] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!url.trim()) return;
    onAnalyze(url.trim());
  };

  const handleSelectSample = (sampleUrl) => {
    setUrl(sampleUrl);
    onAnalyze(sampleUrl);
  };

  return (
    <div className="hero-input-card">
      <label htmlFor="pr-url-input" className="input-label">
        Inspect Public Pull Request
      </label>
      <form onSubmit={handleSubmit} className="input-row">
        <input
          id="pr-url-input"
          type="url"
          className="pr-input"
          placeholder="https://github.com/owner/repository/pull/123"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={isLoading}
          required
        />
        <button
          type="submit"
          id="btn-analyze-pr"
          className="btn-analyze"
          disabled={isLoading || !url.trim()}
        >
          {isLoading ? (
            <>
              <div className="spinner" />
              <span>Auditing PR...</span>
            </>
          ) : (
            <>
              <span>Analyze Diff</span>
              <ArrowRight size={18} />
            </>
          )}
        </button>
      </form>

      <div className="quick-samples">
        <span>Try sample public PR:</span>
        {SAMPLE_PRS.map((sample) => (
          <button
            key={sample.url}
            type="button"
            className="sample-pill"
            onClick={() => handleSelectSample(sample.url)}
            disabled={isLoading}
          >
            {sample.label}
          </button>
        ))}
      </div>
    </div>
  );
}
