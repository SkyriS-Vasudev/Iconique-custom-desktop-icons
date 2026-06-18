import { useState, useEffect } from 'react';
import { SettingsContext } from './SettingsContext.js';

export const SettingsProvider = ({ children }) => {
  const [themeMode, setThemeMode] = useState('dark');
  const [loading, setLoading] = useState(true);

  // Fetch settings from API on load
  useEffect(() => {
    fetch('/api/settings')
      .then((res) => {
        if (res.ok) return res.json();
        throw new Error('Failed to load settings');
      })
      .then((data) => {
        if (data.themeMode) {
          setThemeMode(data.themeMode);
          document.documentElement.setAttribute('data-theme', data.themeMode);
        }
      })
      .catch((err) => {
        console.error('Error loading settings:', err);
        // Fallback default
        document.documentElement.setAttribute('data-theme', 'dark');
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const toggleTheme = (mode) => {
    const newMode = mode || (themeMode === 'dark' ? 'light' : 'dark');
    setThemeMode(newMode);
    document.documentElement.setAttribute('data-theme', newMode);
    
    // Save to backend
    const formData = new FormData();
    formData.append('themeMode', newMode);
    fetch('/api/settings', {
      method: 'POST',
      body: formData,
    }).catch((err) => console.error('Failed to save theme setting:', err));
  };

  return (
    <SettingsContext.Provider value={{ themeMode, toggleTheme, loading }}>
      {children}
    </SettingsContext.Provider>
  );
};
