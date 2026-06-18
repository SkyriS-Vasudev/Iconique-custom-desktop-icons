import { useEffect, useMemo, useRef, useState, useCallback } from 'react'
import {
  ChevronRight,
  CircleAlert,
  Moon,
  RefreshCw,
  Search,
  Sparkles,
  SunMedium,
  Undo2,
  Upload,
} from 'lucide-react'
import './App.css'
import heroIcon from './assets/hero.png'

const DEFAULT_SETTINGS = {
  themeMode: 'dark',
  backupLocation: 'appdata',
  autoScanCommonApps: false,
}

function getApiBase() {
  const params = new URLSearchParams(window.location.search)
  const api = params.get('api')
  if (api) {
    return api.replace(/\/$/, '')
  }

  return window.location.origin
}

function joinApiPath(apiBase, path) {
  if (!path) {
    return ''
  }

  if (/^https?:\/\//i.test(path)) {
    return path
  }

  return `${apiBase}${path.startsWith('/') ? path : `/${path}`}`
}

function iconForShortcut(shortcut) {
  const label = shortcut?.name || 'App'
  return label
    .split(' ')
    .filter(Boolean)
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

function App() {
  const apiBase = useMemo(() => getApiBase(), [])
  const imageInputRef = useRef(null)
  const toastTimerRef = useRef(null)

  const [settings, setSettings] = useState(DEFAULT_SETTINGS)
  const [shortcuts, setShortcuts] = useState([])
  const [themes, setThemes] = useState([])
  const [, setCommonApps] = useState([])
  const [selectedShortcutPath, setSelectedShortcutPath] = useState('')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [toast, setToast] = useState(null)
  const [preview, setPreview] = useState(null)
  const [shortcutForm, setShortcutForm] = useState({
    exePath: '',
    appName: '',
    iconPath: '',
    iconPreview: '',
    iconLabel: '',
  })
  const [installedApps, setInstalledApps] = useState([])

  const selectedShortcut = shortcuts.find((item) => item.path === selectedShortcutPath) || shortcuts[0] || null

  const filteredShortcuts = shortcuts.filter((shortcut) => {
    const haystack = `${shortcut.name} ${shortcut.targetPath || ''} ${shortcut.path || ''}`.toLowerCase()
    return haystack.includes(search.toLowerCase())
  })

  const fetchJson = useCallback(async (path, options = {}) => {
    const response = await fetch(joinApiPath(apiBase, path), options)
    if (!response.ok) {
      const detail = await response.text()
      throw new Error(detail || response.statusText)
    }
    return response.json()
  }, [apiBase])

  const flash = useCallback((message, kind = 'info') => {
    setToast({ message, kind })
    window.clearTimeout(toastTimerRef.current)
    toastTimerRef.current = window.setTimeout(() => setToast(null), 3200)
  }, [])

  const loadShortcuts = useCallback(async () => {
    const data = await fetchJson('/api/shortcuts')
    setShortcuts(
      data.map((shortcut) => ({
        ...shortcut,
        iconSrc: shortcut.iconCacheUrl ? joinApiPath(apiBase, shortcut.iconCacheUrl) : '',
      })),
    )

    if (!selectedShortcutPath && data.length > 0) {
      setSelectedShortcutPath(data[0].path)
    }
  }, [fetchJson, apiBase, selectedShortcutPath])

  const loadThemes = useCallback(async () => {
    const data = await fetchJson('/api/themes')
    setThemes(data)
  }, [fetchJson])

  const loadCommonApps = useCallback(async () => {
    try {
      const data = await fetchJson('/api/apps/common')
      setCommonApps(data.apps || [])
    } catch {
      setCommonApps([])
    }
  }, [fetchJson])

  const loadInstalledApps = useCallback(async () => {
    try {
      const data = await fetchJson('/api/apps/installed')
      setInstalledApps(data || [])
    } catch {
      setInstalledApps([])
    }
  }, [fetchJson])

  useEffect(() => {
    let active = true
    const bootstrap = async () => {
      await Promise.resolve()
      if (!active) return
      try {
        setLoading(true)
        const data = await fetchJson('/api/settings')
        const next = {
          themeMode: data.themeMode || 'dark',
          backupLocation: data.backupLocation || 'appdata',
          autoScanCommonApps: String(data.autoScanCommonApps).toLowerCase() === 'true',
        }
        if (active) {
          setSettings(next)
          document.documentElement.setAttribute('data-theme', next.themeMode)
        }
        
        const shortcutsData = await fetchJson('/api/shortcuts')
        if (active) {
          setShortcuts(
            shortcutsData.map((shortcut) => ({
              ...shortcut,
              iconSrc: shortcut.iconCacheUrl ? joinApiPath(apiBase, shortcut.iconCacheUrl) : '',
            })),
          )
          if (shortcutsData.length > 0) {
            setSelectedShortcutPath(shortcutsData[0].path)
          }
        }

        const themesData = await fetchJson('/api/themes')
        if (active) {
          setThemes(themesData)
        }

        const appsData = await fetchJson('/api/apps/installed')
        if (active) {
          setInstalledApps(appsData || [])
        }
      } catch (error) {
        if (active) flash(`Could not load Iconique data: ${error.message}`, 'error')
      } finally {
        if (active) setLoading(false)
      }
    }
    bootstrap()
    return () => {
      active = false
    }
  }, [apiBase, fetchJson, flash])

  useEffect(() => {
    return () => window.clearTimeout(toastTimerRef.current)
  }, [])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', settings.themeMode)
  }, [settings.themeMode])

  useEffect(() => {
    let active = true
    const scan = async () => {
      await Promise.resolve()
      if (!active) return
      if (settings.autoScanCommonApps) {
        try {
          const data = await fetchJson('/api/apps/common')
          if (active) setCommonApps(data.apps || [])
        } catch {
          if (active) setCommonApps([])
        }
      } else {
        if (active) setCommonApps([])
      }
    }
    scan()
    return () => {
      active = false
    }
  }, [settings.autoScanCommonApps, fetchJson])

  async function persistSettings(partial) {
    const next = { ...settings, ...partial }
    setSettings(next)

    const formData = new FormData()
    Object.entries(partial).forEach(([key, value]) => {
      formData.append(key, String(value))
    })

    await fetchJson('/api/settings', {
      method: 'POST',
      body: formData,
    })

    if (Object.prototype.hasOwnProperty.call(partial, 'autoScanCommonApps') && partial.autoScanCommonApps) {
      await loadCommonApps()
    }
  }

  function selectShortcut(path) {
    setSelectedShortcutPath(path)
    setPreview(null)
  }

  async function refreshData() {
    setBusy(true)
    try {
      await Promise.all([loadShortcuts(), loadThemes(), loadInstalledApps()])
      if (settings.autoScanCommonApps) {
        await loadCommonApps()
      }
      flash('Workspace refreshed', 'success')
    } catch (error) {
      flash(error.message, 'error')
    } finally {
      setBusy(false)
    }
  }

  async function handleCustomIconUpload(file) {
    if (!selectedShortcut) {
      flash('Select a shortcut first.', 'error')
      return
    }

    if (!file) {
      return
    }

    const formData = new FormData()
    formData.append('file', file)

    setBusy(true)
    try {
      const result = await fetchJson('/api/upload', {
        method: 'POST',
        body: formData,
      })

      setPreview({
        title: file.name,
        icoPath: result.icoPath,
        iconUrl: joinApiPath(apiBase, result.previewPath),
        source: 'custom',
      })
      setShortcutForm((current) => ({
        ...current,
        iconPath: result.icoPath,
        iconPreview: joinApiPath(apiBase, result.previewPath),
        iconLabel: file.name,
      }))
      flash('Custom icon loaded. Preview it before applying.', 'success')
    } catch (error) {
      flash(error.message, 'error')
    } finally {
      setBusy(false)
    }
  }

  async function handlePickImage(event) {
    const file = event.target.files?.[0]
    event.target.value = ''
    await handleCustomIconUpload(file)
  }

  async function createShortcut() {
    if (!shortcutForm.exePath || !shortcutForm.appName) {
      flash('Pick an application first.', 'error')
      return
    }

    const activeIconPath = preview?.icoPath || shortcutForm.iconPath || ''

    const formData = new FormData()
    formData.append('exe_path', shortcutForm.exePath)
    formData.append('app_name', shortcutForm.appName)
    if (activeIconPath) {
      formData.append('ico_path', activeIconPath)
    }

    setBusy(true)
    try {
      const result = await fetchJson('/api/shortcuts/create-shortcut', {
        method: 'POST',
        body: formData,
      })

      flash(result.message || 'Shortcut created.', 'success')
      setShortcutForm({
        exePath: '',
        appName: '',
        iconPath: '',
        iconPreview: '',
        iconLabel: '',
      })
      await refreshData()
      if (result.shortcutPath) {
        setSelectedShortcutPath(result.shortcutPath)
      }
    } catch (error) {
      flash(error.message, 'error')
    } finally {
      setBusy(false)
    }
  }

  async function applyPreview() {
    if (!selectedShortcut || !preview) {
      return
    }

    const formData = new FormData()
    formData.append('shortcut_path', selectedShortcut.path)
    formData.append('ico_path', preview.icoPath)

    setBusy(true)
    try {
      const result = await fetchJson('/api/shortcuts/apply', {
        method: 'POST',
        body: formData,
      })

      flash(result.message || 'Icon applied.', 'success')
      setPreview(null)
      await refreshData()
    } catch (error) {
      flash(error.message, 'error')
    } finally {
      setBusy(false)
    }
  }

  async function restoreSelectedShortcut() {
    if (!selectedShortcut) {
      return
    }

    const formData = new FormData()
    formData.append('shortcut_path', selectedShortcut.path)

    setBusy(true)
    try {
      const result = await fetchJson('/api/shortcuts/restore', {
        method: 'POST',
        body: formData,
      })

      flash(result.message || 'Shortcut restored.', 'success')
      await refreshData()
    } catch (error) {
      flash(error.message, 'error')
    } finally {
      setBusy(false)
    }
  }

  function previewThemeEntry(theme, entry) {
    setPreview({
      title: `${theme.name} - ${entry.label}`,
      icoPath: entry.path,
      iconUrl: entry.url,
      source: 'theme',
    })
  }

  const stats = [
    { label: 'Shortcuts', value: shortcuts.length },
    { label: 'Customized', value: shortcuts.filter((item) => item.backupExists).length },
    { label: 'Themes', value: themes.length },
  ]

  return (
    <div className="app-shell">
      {/* Sidebar on the Left */}
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">
            <img src={heroIcon} alt="Iconique" className="navbar-brand-icon" />
          </div>
          <div>
            <div className="brand-title">Iconique</div>
            <div className="brand-subtitle">Desktop personalization</div>
          </div>
        </div>

        <div className="sidebar-group">
          <span className="sidebar-heading">Appearance</span>
          <div className="segmented-control">
            <button
              type="button"
              className={settings.themeMode === 'light' ? 'segmented active' : 'segmented'}
              onClick={() => persistSettings({ themeMode: 'light' })}
            >
              <SunMedium size={14} />
              Light
            </button>
            <button
              type="button"
              className={settings.themeMode === 'dark' ? 'segmented active' : 'segmented'}
              onClick={() => persistSettings({ themeMode: 'dark' })}
            >
              <Moon size={14} />
              Dark
            </button>
          </div>
        </div>

        <div className="sidebar-group stats-sidebar-group">
          <span className="sidebar-heading">Statistics</span>
          <div className="sidebar-stats-grid">
            {stats.map((stat) => (
              <div className="sidebar-stat-card" key={stat.label}>
                <strong>{stat.value}</strong>
                <small>{stat.label}</small>
              </div>
            ))}
          </div>
        </div>
      </aside>

      <main className="workspace">
        {/* Sleek Top Navbar */}
        <header className="navbar">
          <div className="navbar-welcome">
            <h3>Personalization Dashboard</h3>
          </div>

          <div className="navbar-controls">
            <label className="toggle-row-compact">
              <span>Auto-scan apps</span>
              <input
                type="checkbox"
                checked={settings.autoScanCommonApps}
                onChange={(event) => persistSettings({ autoScanCommonApps: event.target.checked })}
              />
            </label>

            <button type="button" className="button button-secondary button-compact" onClick={refreshData} disabled={busy}>
              <RefreshCw size={14} className={busy ? 'spin' : ''} />
              Refresh
            </button>
          </div>
        </header>

        {/* Upper Split Grid: Selected Shortcut on the Left, Themes on the Right */}
        <div className="upper-split-grid">
          {/* Left Column: Active Selection & Preview */}
          <section className="pane-card active-shortcut-panel">
            <div className="section-meta">
              <span className="section-eyebrow">Active Selection</span>
              <h3>{selectedShortcut ? selectedShortcut.name : 'No shortcut selected'}</h3>
              {selectedShortcut && (
                <p className="shortcut-path-text" title={selectedShortcut.targetPath || selectedShortcut.path}>
                  {selectedShortcut.targetPath || selectedShortcut.path}
                </p>
              )}
            </div>

            <div className="preview-container-vertical">
              <div className="preview-item">
                <span className="preview-tag">Current</span>
                <div className="icon-frame">
                  {selectedShortcut?.iconSrc ? (
                    <img src={selectedShortcut.iconSrc} alt="Current" />
                  ) : (
                    <span>{selectedShortcut ? iconForShortcut(selectedShortcut) : '?'}</span>
                  )}
                </div>
              </div>
              <ChevronRight className="preview-arrow-compact" size={18} />
              <div className="preview-item">
                <span className="preview-tag">New</span>
                <div className="icon-frame preview-draft">
                  {preview?.iconUrl ? (
                    <img src={preview.iconUrl} alt="New" />
                  ) : (
                    <span>?</span>
                  )}
                </div>
              </div>
            </div>

            <div className="action-buttons-vertical">
              {preview && (
                <span className="pending-source-label" title={preview.title}>
                  Selected: {preview.title}
                </span>
              )}
              <div className="btn-group-vertical">
                <button 
                  type="button" 
                  className="button button-primary" 
                  onClick={applyPreview}
                  disabled={!selectedShortcut || !preview || busy}
                >
                  <Sparkles size={14} />
                  Apply new icon
                </button>
                <button 
                  type="button" 
                  className="button button-secondary" 
                  onClick={() => imageInputRef.current?.click()}
                  disabled={!selectedShortcut || busy}
                >
                  <Upload size={14} />
                  Upload Custom Image
                </button>
                <button 
                  type="button" 
                  className="button button-secondary" 
                  onClick={restoreSelectedShortcut} 
                  disabled={!selectedShortcut || !selectedShortcut.backupExists || busy}
                >
                  <Undo2 size={14} />
                  Restore default icon
                </button>
              </div>
            </div>
          </section>

          {/* Right Column: Theme Packs Browsing */}
          <section className="pane-card themes-pane">
            <div className="pane-header-compact">
              <div className="pane-title-group">
                <h4>Theme packs</h4>
                <span>{themes.length} packs available</span>
              </div>
            </div>

            <div className="themes-list-scrollable">
              {themes.map((theme) => (
                <article className="theme-section-card" key={theme.id}>
                  <div className="theme-card-header">
                    <div>
                      <h5>{theme.name}</h5>
                      <span className="theme-author-name">by {theme.author}</span>
                    </div>
                    <span className="theme-category-tag">{(theme.iconEntries || []).length} icons</span>
                  </div>
                  <p className="theme-card-desc">{theme.description}</p>

                  <div className="theme-icons-grid-scroll">
                    {(theme.iconEntries || []).map((icon) => {
                      const isSelected = preview?.icoPath === icon.path
                      return (
                        <button
                          type="button"
                          className={isSelected ? 'theme-icon-btn active' : 'theme-icon-btn'}
                          key={`${theme.id}-${icon.filename}`}
                          title={icon.label}
                          onClick={() => previewThemeEntry(theme, icon)}
                        >
                          {icon?.url ? (
                            <img src={icon.url} alt={icon.label} />
                          ) : (
                            <span>{iconForShortcut({ name: icon.label })}</span>
                          )}
                          <span className="theme-icon-btn-label">{icon.label}</span>
                        </button>
                      )
                    })}
                  </div>
                </article>
              ))}

              {!themes.length && (
                <div className="empty-state-compact">
                  <CircleAlert size={20} />
                  <span>No theme packs loaded.</span>
                </div>
              )}
            </div>
          </section>
        </div>

        {/* Lower Horizontal Row: Desktop Shortcuts List */}
        <section className="pane-card horizontal-shortcuts-pane">
          <div className="pane-header-horizontal">
            <div className="pane-title-group">
              <h4>Desktop shortcuts</h4>
              <span>Choose a shortcut to customize</span>
            </div>
            <label className="search-field-compact">
              <Search size={14} />
              <input
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search shortcuts..."
              />
            </label>
          </div>

          <div className="shortcuts-list-horizontal">
            {filteredShortcuts.map((shortcut) => (
              <button
                type="button"
                key={shortcut.path}
                className={shortcut.path === selectedShortcutPath ? 'shortcut-card-horizontal active' : 'shortcut-card-horizontal'}
                onClick={() => selectShortcut(shortcut.path)}
              >
                <div className="shortcut-card-icon">
                  {shortcut.iconSrc ? (
                    <img src={shortcut.iconSrc} alt="" />
                  ) : (
                    <span>{iconForShortcut(shortcut)}</span>
                  )}
                </div>
                <div className="shortcut-card-meta">
                  <strong>{shortcut.name}</strong>
                  <small className={shortcut.backupExists ? "shortcut-status-text customized" : "shortcut-status-text"}>
                    {shortcut.backupExists ? 'Backup saved' : 'No change in icon'}
                  </small>
                </div>
              </button>
            ))}

            {!filteredShortcuts.length && (
              <div className="empty-state-compact">
                <CircleAlert size={20} />
                <span>No shortcuts found.</span>
              </div>
            )}
          </div>
        </section>

        {/* Create Desktop Shortcut pane at the bottom */}
        <section className="pane-card create-shortcut-pane">
          <div className="pane-header-compact">
            <div className="pane-title-group">
              <h4>Create desktop shortcut</h4>
              <span>Application, name, and selected icon</span>
            </div>
          </div>

          <form className="create-shortcut-form" onSubmit={(e) => { e.preventDefault(); createShortcut(); }}>
            <div className="form-grid-horizontal">
              <div className="form-group">
                <label>Select Application</label>
                <select
                  value={shortcutForm.exePath}
                  onChange={(e) => {
                    const selectedPath = e.target.value
                    const app = installedApps.find((a) => a.path === selectedPath)
                    setShortcutForm((prev) => ({
                      ...prev,
                      exePath: selectedPath,
                      appName: app ? app.name : '',
                    }))
                  }}
                  required
                >
                  <option value="">-- Choose Application --</option>
                  {installedApps.map((app) => (
                    <option key={app.path} value={app.path}>
                      {app.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Shortcut Name</label>
                <input
                  type="text"
                  placeholder="App Name"
                  value={shortcutForm.appName}
                  onChange={(e) => setShortcutForm((prev) => ({ ...prev, appName: e.target.value }))}
                  required
                />
              </div>

              <div className="form-group">
                <label>Selected Theme Icon</label>
                <div className="selected-icon-preview-box">
                  {preview?.iconUrl ? (
                    <div className="mini-icon-frame">
                      <img src={preview.iconUrl} alt="Selected" />
                      <span>{preview.title}</span>
                    </div>
                  ) : (
                    <span className="no-icon-selected-text">Choose any theme icon above first</span>
                  )}
                </div>
              </div>

              <button
                type="submit"
                className="button button-primary create-btn"
                disabled={busy || !shortcutForm.exePath || !shortcutForm.appName}
              >
                <Sparkles size={14} />
                Create Shortcut
              </button>
            </div>
          </form>
        </section>
      </main>

      <input
        ref={imageInputRef}
        type="file"
        accept="image/*,.ico"
        className="hidden-input"
        onChange={handlePickImage}
      />

      {toast && (
        <div className={`toast toast-${toast.kind}`}>
          <span>{toast.message}</span>
        </div>
      )}

      {loading && (
        <div className="loading-overlay">
          <RefreshCw size={24} className="spin" />
          <span>Loading Iconique...</span>
        </div>
      )}
    </div>
  )
}

export default App
