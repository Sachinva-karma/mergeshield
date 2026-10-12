import React, { useEffect, useState } from 'react';
import { fetchHealth, analyzePR } from './api';
import Header from './components/Header';
import PRInput from './components/PRInput';
import RiskCard from './components/RiskCard';
import {
  GitPullRequest,
  GitCommit,
  GitBranch,
  Shield,
  FileCheck,
  AlertCircle,
  ExternalLink,
  Info,
} from 'lucide-react';

export default function App() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [analysis, setAnalysis] = useState(null);

  useEffect(() => {
    fetchHealth().then((data) => {
      if (data) setHealth(data);
    });
  }, []);

  const handleAnalyze = async (prUrl) => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyzePR(prUrl);
      setAnalysis(result);
    } catch (err) {
      setError(err.message || 'An unexpected error occurred while analyzing the PR.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <Header health={health} />

      <main>
        <PRInput onAnalyze={handleAnalyze} isLoading={loading} />

        {error && (
          <div className="alert-card" role="alert">
            <AlertCircle size={22} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <strong>Analysis Notice:</strong>
              <p style={{ marginTop: '0.25rem', fontSize: '0.9rem' }}>{error}</p>
              {!health?.is_model_configured && (
                <p style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#fecaca' }}>
                  Tip: Add your <code>GROQ_API_KEY</code> (or preferred provider key) to the <code>.env</code> file in your backend and restart.
                </p>
              )}
            </div>
          </div>
        )}

        {analysis && (
          <section className="results-container" aria-label="PR Analysis Results">
            {/* PR Overview Card */}
            <div className="results-overview">
              <div className="pr-headline">
                <div>
                  <h2>{analysis.pr.title}</h2>
                  <div className="pr-meta-row" style={{ marginTop: '0.5rem' }}>
                    <span className="pr-badge">
                      <GitPullRequest size={14} /> #{analysis.pr.pr_number} by {analysis.pr.author}
                    </span>
                    <span className="pr-badge">
                      <GitBranch size={14} /> {analysis.pr.base_branch} &larr; {analysis.pr.head_branch}
                    </span>
                    <span className="pr-badge">
                      <GitCommit size={14} /> {analysis.pr.changed_files_count} files (+{analysis.pr.additions} / -{analysis.pr.deletions})
                    </span>
                  </div>
                </div>

                <a
                  href={analysis.pr.html_url}
                  target="_blank"
                  rel="noreferrer"
                  className="pr-badge"
                  style={{ textDecoration: 'none', color: 'var(--primary)' }}
                >
                  View on GitHub <ExternalLink size={12} style={{ marginLeft: '4px' }} />
                </a>
              </div>

              {/* Overall Risk Banner */}
              <div className={`risk-level-banner ${analysis.overall_risk_score}`}>
                <div className="risk-title-group">
                  <h3>Overall Risk: {analysis.overall_risk_score}</h3>
                  <p className="risk-summary-text">{analysis.summary_assessment}</p>
                </div>
                <Shield size={36} opacity={0.8} />
              </div>

              {/* Bounded Diff Notice */}
              {analysis.diff_summary.truncated && (
                <div className="uncertainty-box" style={{ marginTop: '1rem', borderLeftColor: '#f59e0b' }}>
                  <strong>Diff Bounded: </strong>
                  {analysis.diff_summary.truncation_reason} (Analyzed {analysis.diff_summary.total_lines} lines across {analysis.diff_summary.files_analyzed.length} files to stay within safe model context bounds).
                </div>
              )}
            </div>

            {/* Observed Facts */}
            {analysis.observed_facts && analysis.observed_facts.length > 0 && (
              <div className="facts-card">
                <h3>
                  <FileCheck size={18} color="#3b82f6" />
                  Observed Facts (Retrieved Context)
                </h3>
                <ul className="facts-list">
                  {analysis.observed_facts.map((fact, idx) => (
                    <li key={idx} className="fact-item">{fact}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Potential Risks */}
            <div className="findings-section">
              <div className="findings-section-header">
                <h3 style={{ fontSize: '1.2rem', fontWeight: 600 }}>
                  Potential Code Risks & Diff Evidence
                </h3>
                <span className="findings-count">
                  {analysis.findings.length} Finding{analysis.findings.length === 1 ? '' : 's'}
                </span>
              </div>

              {analysis.findings.length === 0 ? (
                <div className="hero-input-card" style={{ textAlign: 'center', padding: '3rem' }}>
                  <Shield size={44} color="#10b981" style={{ margin: '0 auto 1rem' }} />
                  <h4 style={{ fontSize: '1.15rem', color: '#34d399', marginBottom: '0.5rem' }}>
                    No Elevated Code Risks Detected
                  </h4>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                    The analyzed diff contains clean changes with no critical regressions or vulnerabilities identified.
                  </p>
                </div>
              ) : (
                analysis.findings.map((finding) => (
                  <RiskCard key={finding.id} finding={finding} />
                ))
              )}
            </div>
          </section>
        )}
      </main>

      {/* Model Provenance & Licensing Footer */}
      <footer className="provenance-footer">
        <div>
          <strong>Model:</strong> {analysis?.model_info?.model_name || health?.model_name || 'Llama 3.3 70B'}
          {' '}&bull;{' '}
          <strong>Provider:</strong> {analysis?.model_info?.provider || health?.model_provider || 'Groq'}
          {' '}&bull;{' '}
          <strong>Model License:</strong> {analysis?.model_info?.model_license || 'Llama 3.3 Community License'}
        </div>
        <div>
          MergeShield &copy; 2026 &bull; Open Source (MIT License) &bull; Grounded Diff Analysis
        </div>
      </footer>
    </div>
  );
}
