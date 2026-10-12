import React from 'react';
import { ShieldCheck, Cpu, KeyRound } from 'lucide-react';

export default function Header({ health }) {
  const isModelConfigured = health?.is_model_configured;
  const isGithubConfigured = health?.is_github_token_configured;
  const modelProvider = health?.model_provider || 'Groq';
  const modelName = health?.model_name || 'Llama 3.3 70B';

  return (
    <header className="app-header">
      <div className="brand-section">
        <div className="brand-logo" aria-hidden="true">
          <ShieldCheck size={26} color="#ffffff" />
        </div>
        <div>
          <h1 className="brand-title">MergeShield</h1>
          <p className="brand-subtitle">Evidence-Backed PR Risk Intelligence & Diff Grounding</p>
        </div>
      </div>

      <div className="health-status-bar">
        <div className="status-badge" title={`Model: ${modelName}`}>
          <Cpu size={14} />
          <span>{modelProvider}</span>
          <span className={`status-dot ${isModelConfigured ? 'active' : 'inactive'}`} />
        </div>

        <div className="status-badge" title={isGithubConfigured ? 'GitHub Token Active' : 'Public Anonymous Rate Limits (60 req/hr)'}>
          <KeyRound size={14} />
          <span>{isGithubConfigured ? 'GitHub Auth' : 'GitHub Public'}</span>
          <span className={`status-dot ${isGithubConfigured ? 'active' : 'inactive'}`} />
        </div>
      </div>
    </header>
  );
}
