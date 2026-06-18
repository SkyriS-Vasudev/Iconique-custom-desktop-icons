import { useEffect, useMemo, useRef, useState, useCallback } from 'react'
import {
  ChevronRight,
  CircleAlert,
  FolderInput,
  ImagePlus,
  Monitor,
  Moon,
  RefreshCw,
  Search,
  Sparkles,
  SunMedium,
  Undo2,
  Upload,
  X,
} from 'lucide-react'
import './App.css'

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
  const [commonApps, setCommonApps] = useState([])
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

  const selectedShortcut = shortcuts.find((item) => item.path === selectedShortcutPath) || shortcuts[0] || null

  const filteredShortcuts = shortcuts.filter((shortcut) => {
    const haystack = `${shortcut.name} ${shortcut.targetPath || ''} ${shortcut.path || ''}`.toLowerCase()
    return haystack.includes(search.toLowerCase())
  })

  const selectedShortcutPreview = selectedShortcut?.iconCacheUrl
    ? joinApiPath(apiBase, selectedShortcut.iconCacheUrl)
    : ''

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
      await Promise.all([loadShortcuts(), loadThemes()])
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

  async function handlePickExecutable() {
    try {
      if (window.pywebview?.api?.pick_executable) {
        const pickedPath = await window.pywebview.api.pick_executable()
        if (pickedPath) {
          const fileName = pickedPath.split(/[\\/]/).pop() || 'Application'
          const appName = fileName.replace(/\.exe$/i, '')
          setShortcutForm((current) => ({
            ...current,
            exePath: pickedPath,
            appName: current.appName || appName,
          }))
          flash(`Picked ${fileName}`, 'success')
          return
        }
      }

      flash('Desktop file picker is unavailable here. Paste the EXE path below.', 'info')
    } catch (error) {
      flash(error.message, 'error')
    }
  }

  async function createShortcut() {
    if (!shortcutForm.exePath || !shortcutForm.appName || !shortcutForm.iconPath) {
      flash('Pick an EXE, choose a name, and upload an icon first.', 'error')
      return
    }

    const formData = new FormData()
    formData.append('exe_path', shortcutForm.exePath)
    formData.append('app_name', shortcutForm.appName)
    formData.append('ico_path', shortcutForm.iconPath)

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

  async function applyThemeToSelected(theme) {
    if (!selectedShortcut) {
      flash('Select a shortcut before applying a theme icon.', 'error')
      return
    }

    const themeIcon = theme.icons?.[selectedShortcut.name]
    if (!themeIcon?.path) {
      flash(`That theme does not include ${selectedShortcut.name}.`, 'error')
      return
    }

    setPreview({
      title: `${theme.name} · ${selectedShortcut.name}`,
      icoPath: themeIcon.path,
      iconUrl: themeIcon.url,
      source: 'theme',
    })
  }

  function previewThemeEntry(theme, entry) {
    setPreview({
      title: `${theme.name} · ${entry.label}`,
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

  const currentPreview = selectedShortcutPreview || ''
  const pendingPreview = preview?.iconUrl || ''
  return (
    <div className="app-shell no-sidebar">
      {/* Sleek Top Navbar */}
      <header className="navbar">
        <div className="brand-block">
          <div className="brand-mark">
            <svg width="20" height="20" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M16 2L30 9V23L16 30L2 23V9L16 2Z" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M16 8V24" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round"/>
              <path d="M11 11H21" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"/>
              <path d="M11 21H21" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"/>
            </svg>
          </div>
          <div>
            <div className="brand-title">Iconique</div>
            <div className="brand-subtitle">Desktop personalization dashboard</div>
          </div>
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

      <main className="workspace-fluid">
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
                <span>Click any icon below to select it as the new icon</span>
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
                    <span className="theme-category-tag">{theme.category}</span>
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
