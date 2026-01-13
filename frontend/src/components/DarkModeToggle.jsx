import { useState, useEffect } from 'react';
import './DarkModeToggle.css';

export default function DarkModeToggle() {
  const [isDark, setIsDark] = useState(() => {
    // Check localStorage or system preference
    const saved = localStorage.getItem('theme');
    if (saved) {
      return saved === 'dark';
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    // Apply theme to document
    if (isDark) {
      document.documentElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.setAttribute('data-theme', 'light');
      localStorage.setItem('theme', 'light');
    }
  }, [isDark]);

  const toggleTheme = () => {
    setIsDark(!isDark);
  };

  return (
    <button
      className={`dark-mode-toggle ${isDark ? 'dark' : 'light'}`}
      onClick={toggleTheme}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
    >
      <div className="toggle-icon-container">
        <span className="toggle-icon sun">☀️</span>
        <span className="toggle-icon moon">🌙</span>
      </div>
    </button>
  );
}

