import { useContext, useState } from 'react';
import { SettingsContext } from '../context/SettingsContext.js';

const Settings = () => {
  const { settings, setSettings } = useContext(SettingsContext);
  const [backupLocation, setBackupLocation] = useState(settings.backupLocation || 'appdata');
  const [autoScan, setAutoScan] = useState(settings.autoScan || false);

  const handleSave = () => {
    setSettings(prev => ({
      ...prev,
      backupLocation,
      autoScan,
    }));
    // Persist to backend (optional)
    fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        backupLocation,
        autoScan: autoScan ? 'true' : 'false',
      })
    }).catch(console.error);
  };

  return (
    <section className="settings">
      <h2>Preferences</h2>
      <div className="setting-item">
        <label>Backup Storage Location:</label>
        <select value={backupLocation} onChange={e => setBackupLocation(e.target.value)}>
          <option value="appdata">%APPDATA%/Iconique/backups (recommended)</option>
          <option value="workspace">Project workspace (backend/backups)</option>
        </select>
      </div>
      <div className="setting-item">
        <label>
          <input type="checkbox" checked={autoScan} onChange={e => setAutoScan(e.target.checked)} />
          Auto‑scan Program Files for common apps
        </label>
      </div>
      <button className="save-button" onClick={handleSave}>Save Preferences</button>
    </section>
  );
};

export default Settings;
