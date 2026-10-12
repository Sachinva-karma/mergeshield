import React, { useEffect, useState } from 'react';
import Header from './components/Header';
import HeroInitial from './components/HeroInitial';
import LoadingView from './components/LoadingView';
import ErrorView from './components/ErrorView';
import AnalysisView from './components/AnalysisView';
import { fetchHealth, analyzePR } from './api';

export default function App() {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('mergeshield-theme') || 'system';
  });

  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUrl, setLastUrl] = useState('');
  const [analysis, setAnalysis] = useState(null);

  // Theme resolution & persistence
  useEffect(() => {
    localStorage.setItem('mergeshield-theme', theme);

    const applyTheme = (isDark) => {
      const root = document.documentElement;
      if (isDark) {
        root.setAttribute('data-theme', 'dark');
        root.classList.add('dark');
        root.classList.remove('light');
      } else {
        root.setAttribute('data-theme', 'light');
        root.classList.add('light');
        root.classList.remove('dark');
      }
    };

    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      applyTheme(mediaQuery.matches);

      const handler = (e) => applyTheme(e.matches);
      mediaQuery.addEventListener('change', handler);
      return () => mediaQuery.removeEventListener('change', handler);
    } else {
      applyTheme(theme === 'dark');
    }
  }, [theme]);

  // Health probe on load
  useEffect(() => {
    fetchHealth().then((data) => {
      if (data) setHealth(data);
    });
  }, []);

  const handleAnalyze = async (prUrl) => {
    if (loading) return; // Prevent duplicate concurrent submissions
    setLastUrl(prUrl);
    setLoading(true);
    setError(null);
    try {
      const result = await analyzePR(prUrl);
      setAnalysis(result);
    } catch (err) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setAnalysis(null);
    setError(null);
    setLoading(false);
  };

  return (
    <div className="app-shell">
      <Header
        health={health}
        theme={theme}
        setTheme={setTheme}
        onReset={handleReset}
      />

      <main className="workspace-container" style={{ flex: 1 }}>
        {loading && <LoadingView message="Inspecting pull request changes..." />}

        {error && (
          <ErrorView
            error={error}
            onRetry={lastUrl ? () => handleAnalyze(lastUrl) : null}
            onReset={handleReset}
          />
        )}

        {!loading && !error && !analysis && (
          <HeroInitial onAnalyze={handleAnalyze} isLoading={loading} />
        )}

        {!loading && !error && analysis && (
          <AnalysisView
            analysis={analysis}
            onNewAnalysis={handleReset}
          />
        )}
      </main>

      <footer className="site-footer">
        <div className="workspace-container">
          <div className="footer-inner">
            <div>
              <span>MergeShield &bull; Evidence-Backed PR Risk Intelligence</span>
            </div>
            <div>
              <span>Powered by Apache 2.0 Open Weights &bull; MIT License</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
