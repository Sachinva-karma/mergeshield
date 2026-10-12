import React from 'react';
import { Sun, Moon, Monitor } from 'lucide-react';

export default function ThemeSelector({ theme, setTheme }) {
  return (
    <div className="theme-toggle-group" role="radiogroup" aria-label="Color theme switcher">
      <button
        type="button"
        className={`theme-btn ${theme === 'light' ? 'active' : ''}`}
        onClick={() => setTheme('light')}
        title="Light theme"
        aria-label="Light theme"
      >
        <Sun size={14} />
      </button>
      <button
        type="button"
        className={`theme-btn ${theme === 'dark' ? 'active' : ''}`}
        onClick={() => setTheme('dark')}
        title="Dark theme"
        aria-label="Dark theme"
      >
        <Moon size={14} />
      </button>
      <button
        type="button"
        className={`theme-btn ${theme === 'system' ? 'active' : ''}`}
        onClick={() => setTheme('system')}
        title="System preference"
        aria-label="System theme"
      >
        <Monitor size={14} />
      </button>
    </div>
  );
}
