import React, { useState } from 'react';
import { ArrowRight, Lock, Eye, Terminal } from 'lucide-react';

const REAL_SAMPLE_PRS = [
  {
    label: 'Flask #5918 (Route Refactor)',
    url: 'https://github.com/pallets/flask/pull/5918',
  },
  {
    label: 'FastAPI #11000 (Clean Docs)',
    url: 'https://github.com/fastapi/fastapi/pull/11000',
  },
  {
    label: 'Flask #5660 (Sans-I/O Session)',
    url: 'https://github.com/pallets/flask/pull/5660',
  },
];

export default function HeroInitial({ onAnalyze, isLoading }) {
  const [prUrl, setPrUrl] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!prUrl.trim()) return;
    onAnalyze(prUrl.trim());
  };

  const handleSelectSample = (sampleUrl) => {
    setPrUrl(sampleUrl);
    onAnalyze(sampleUrl);
  };

  return (
    <section className="hero-section" aria-label="MergeShield Initial Screen">
      <div className="hero-pill">
        <span>AI-Assisted Code Review</span>
        <span style={{ opacity: 0.5 }}>&bull;</span>
        <span>AST-Guided</span>
      </div>

      <h1 className="hero-title">
        Know what could break before you merge.
      </h1>

      <p className="hero-description">
        Evidence-backed pull request analysis to help engineering teams catch potential regressions, contract drifts, and subtle async failures before they reach production.
      </p>

      {/* Input Card */}
      <div className="input-card">
        <form onSubmit={handleSubmit} className="input-form">
          <input
            type="url"
            id="pr-url-input"
            className="pr-text-input"
            placeholder="Paste public pull request URL, e.g. https://github.com/owner/repo/pull/123"
            value={prUrl}
            onChange={(e) => setPrUrl(e.target.value)}
            disabled={isLoading}
            required
          />
          <button
            type="submit"
            id="btn-analyze-pr"
            className="btn-primary"
            disabled={isLoading || !prUrl.trim()}
          >
            <span>Analyze PR</span>
            <ArrowRight size={16} />
          </button>
        </form>
      </div>

      {/* Trust Statements */}
      <div className="trust-row">
        <span className="trust-item">
          <span className="trust-dot" />
          <span>Public repositories</span>
        </span>
        <span className="trust-item">
          <Eye size={13} style={{ color: 'var(--emerald)' }} />
          <span>Read-only analysis</span>
        </span>
        <span className="trust-item">
          <Lock size={13} style={{ color: 'var(--emerald)' }} />
          <span>No arbitrary code execution</span>
        </span>
      </div>

      {/* Sample Shortcuts */}
      <div className="sample-row">
        <span>Try verified public PR:</span>
        {REAL_SAMPLE_PRS.map((sample) => (
          <button
            key={sample.url}
            type="button"
            className="sample-button"
            onClick={() => handleSelectSample(sample.url)}
            disabled={isLoading}
          >
            {sample.label}
          </button>
        ))}
      </div>

      {/* Three Understated Steps */}
      <div className="steps-grid">
        <div className="step-card">
          <div className="step-num">Step 01</div>
          <h2 className="step-title">Inspect changes</h2>
          <p className="step-desc">
            Fetches public PR metadata and bounds the raw unified diff to prevent context truncation and rate spikes.
          </p>
        </div>

        <div className="step-card">
          <div className="step-num">Step 02</div>
          <h2 className="step-title">Identify risks</h2>
          <p className="step-desc">
            Evaluates regressions, breaking API contracts, error suppression, and concurrency flaws with open-weight models.
          </p>
        </div>

        <div className="step-card">
          <div className="step-num">Step 03</div>
          <h2 className="step-title">Verify with evidence</h2>
          <p className="step-desc">
            Cross-verifies every cited line against retrieved diff hunks, rejecting or caveat-flagging hallucinated claims.
          </p>
        </div>
      </div>
    </section>
  );
}
