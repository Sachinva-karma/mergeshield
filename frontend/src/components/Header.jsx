import React from 'react';
import { ShieldCheck, Cpu } from 'lucide-react';
import ThemeSelector from './ThemeSelector';

function GithubIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
      <path d="M9 18c-4.51 2-5-2-7-2" />
    </svg>
  );
}

export default function Header({ health, theme, setTheme, onReset }) {
  const isModelConfigured = health?.is_model_configured;
  const modelName = health?.model_name || 'qwen/qwen3.8-27b';

  return (
    <header className="site-header">
      <div className="workspace-container">
        <div className="header-inner">
          <div className="brand-anchor" onClick={onReset} role="button" tabIndex={0} onKeyDown={(e) => e.key === 'Enter' && onReset()}>
            <div className="brand-icon-wrapper" aria-hidden="true">
              <ShieldCheck size={20} />
            </div>
            <span>MergeShield</span>
            <span className="brand-badge">Audit</span>
          </div>

          <div className="header-actions">
            <div className="nav-link" style={{ fontSize: '12px' }} title={`Active Model: ${modelName}`}>
              <Cpu size={14} />
              <span style={{ fontFamily: 'JetBrains Mono, monospace' }}>{modelName.split('/').pop()}</span>
              <span
                style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  backgroundColor: isModelConfigured ? 'var(--emerald)' : 'var(--error)',
                }}
              />
            </div>

            <a
              href="https://github.com/Sachinva-karma/mergeshield"
              target="_blank"
              rel="noreferrer"
              className="nav-link"
              title="View on GitHub"
            >
              <GithubIcon size={16} />
              <span>GitHub</span>
            </a>

            <ThemeSelector theme={theme} setTheme={setTheme} />
          </div>
        </div>
      </div>
    </header>
  );
}
