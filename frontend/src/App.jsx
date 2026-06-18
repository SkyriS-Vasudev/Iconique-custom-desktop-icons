import { useEffect, useMemo, useRef, useState } from 'react'
import {
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  FolderInput,
  ImagePlus,
  Monitor,
  Moon,
  RefreshCw,
  Search,
  Settings2,
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

function formatTimestamp(value) {
  if (!value) {
    return 'Just now'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleString()
}

function App() {
  const apiBase = useMemo(() => getApiBase(), [])
  const imageInputRef = useRef(null)
  const toastTimerRef = useRef(null)

  const [settings, setSettings] = useState(DEFAULT_SETTINGS)
  const [shortcuts, setShortcuts] = useState([])
  const [themes, setThemes] = useState([])
  const [history, setHistory] = useState([])
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

  async function fetchJson(path, options = {}) {
    const response = await fetch(joinApiPath(apiBase, path), options)
    if (!response.ok) {
      const detail = await response.text()
      throw new Error(detail || response.statusText)
    }
    return response.json()
  }

  function flash(message, kind = 'info') {
    setToast({ message, kind })
    window.clearTimeout(toastTimerRef.current)
    toastTimerRef.current = window.setTimeout(() => setToast(null), 3200)
  }

  async function loadShortcuts() {
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
  }

  async function loadThemes() {
    const data = await fetchJson('/api/themes')
    setThemes(data)
  }

  async function loadHistory() {
    const data = await fetchJson('/api/history')
    setHistory(data)
  }

  async function loadSettings() {
    const data = await fetchJson('/api/settings')
    const next = {
      themeMode: data.themeMode || 'dark',
      backupLocation: data.backupLocation || 'appdata',
      autoScanCommonApps: String(data.autoScanCommonApps).toLowerCase() === 'true',
    }
    setSettings(next)
    document.documentElement.setAttribute('data-theme', next.themeMode)
  }

  async function loadCommonApps() {
    try {
      const data = await fetchJson('/api/apps/common')
      setCommonApps(data.apps || [])
    } catch {
      setCommonApps([])
    }
  }

  async function bootstrap() {
    try {
      setLoading(true)
      await loadSettings()
      await Promise.all([loadShortcuts(), loadThemes(), loadHistory()])
    } catch (error) {
      flash(`Could not load Iconique data: ${error.message}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    bootstrap().catch((error) => flash(error.message, 'error'))
  }, [])

  useEffect(() => {
    return () => window.clearTimeout(toastTimerRef.current)
  }, [])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', settings.themeMode)
  }, [settings.themeMode])

  useEffect(() => {
    if (settings.autoScanCommonApps) {
      loadCommonApps().catch(() => setCommonApps([]))
    } else {
      setCommonApps([])
    }
  }, [settings.autoScanCommonApps])

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
      await Promise.all([loadShortcuts(), loadThemes(), loadHistory()])
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
    if (!selectedShortcut) {
      flash('Select a shortcut before previewing a theme icon.', 'error')
      return
    }

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
    { label: 'Recent actions', value: history.length },
  ]

  const currentPreview = selectedShortcutPreview || ''
  const pendingPreview = preview?.iconUrl || ''

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">
            <Sparkles size={20} />
          </div>
          <div>
            <div className="brand-title">Iconique</div>
            <div className="brand-subtitle">Custom desktop icons, minus the Windows ceremony</div>
          </div>
        </div>

        <div className="sidebar-group">
          <div className="sidebar-heading">Appearance</div>
          <div className="segmented-control">
            <button
              type="button"
              className={settings.themeMode === 'dark' ? 'segmented active' : 'segmented'}
              onClick={() => persistSettings({ themeMode: 'dark' })}
            >
              <Moon size={16} />
              Dark
            </button>
            <button
              type="button"
              className={settings.themeMode === 'light' ? 'segmented active' : 'segmented'}
              onClick={() => persistSettings({ themeMode: 'light' })}
            >
              <SunMedium size={16} />
              Light
            </button>
          </div>
        </div>

        <div className="sidebar-group">
          <div className="sidebar-heading">Backup storage</div>
          <label className="radio-card">
            <input
              type="radio"
              name="backupLocation"
              checked={settings.backupLocation === 'appdata'}
              onChange={() => persistSettings({ backupLocation: 'appdata' })}
            />
            <span>
              <strong>APPDATA</strong>
              <small>Recommended for normal use.</small>
            </span>
          </label>
          <label className="radio-card">
            <input
              type="radio"
              name="backupLocation"
              checked={settings.backupLocation === 'workspace'}
              onChange={() => persistSettings({ backupLocation: 'workspace' })}
            />
            <span>
              <strong>Workspace</strong>
              <small>Good for local testing and demos.</small>
            </span>
          </label>
        </div>

        <div className="sidebar-group">
          <label className="toggle-row">
            <div>
              <strong>Auto-scan common apps</strong>
              <small>Populate the shortcut picker with installed apps.</small>
            </div>
            <input
              type="checkbox"
              checked={settings.autoScanCommonApps}
              onChange={(event) => persistSettings({ autoScanCommonApps: event.target.checked })}
            />
          </label>
        </div>

        <button type="button" className="button button-secondary" onClick={refreshData} disabled={busy}>
          <RefreshCw size={16} className={busy ? 'spin' : ''} />
          Refresh data
        </button>
      </aside>

      <main className="workspace">
        <header className="hero">
          <div>
            <p className="eyebrow">PyWebView + FastAPI + React</p>
            <h1>Iconique</h1>
            <p className="hero-copy">
              Find a shortcut, swap its icon, restore it later if needed, and keep the original path safely backed up
              in one place.
            </p>
          </div>

          <div className="hero-actions">
            {stats.map((stat) => (
              <div className="stat-card" key={stat.label}>
                <span>{stat.label}</span>
                <strong>{stat.value}</strong>
              </div>
            ))}
          </div>
        </header>

        <section className="main-grid">
          <section className="panel shortcuts-panel">
            <div className="panel-header">
              <div>
                <h2>Desktop shortcuts</h2>
                <p>Pick a shortcut, then apply a custom icon or a theme pack.</p>
              </div>
              <label className="search-field">
                <Search size={16} />
                <input
                  type="search"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search shortcuts"
                />
              </label>
            </div>

            <div className="shortcut-grid">
              {filteredShortcuts.map((shortcut) => (
                <button
                  type="button"
                  key={shortcut.path}
                  className={shortcut.path === selectedShortcutPath ? 'shortcut-card active' : 'shortcut-card'}
                  onClick={() => selectShortcut(shortcut.path)}
                >
                  <div className="shortcut-icon-wrap">
                    {shortcut.iconSrc ? (
                      <img src={shortcut.iconSrc} alt="" />
                    ) : (
                      <span>{iconForShortcut(shortcut)}</span>
                    )}
                  </div>
                  <div className="shortcut-copy">
                    <strong>{shortcut.name}</strong>
                    <span>{shortcut.targetPath || shortcut.path}</span>
                    <small>{shortcut.backupExists ? 'Backup saved' : 'No backup yet'}</small>
                  </div>
                </button>
              ))}

              {!filteredShortcuts.length && (
                <div className="empty-state">
                  <CircleAlert size={24} />
                  <span>No shortcuts match that search.</span>
                </div>
              )}
            </div>
          </section>

          <aside className="panel action-panel">
            <div className="panel-header">
              <div>
                <h2>Selected shortcut</h2>
                <p>{selectedShortcut ? selectedShortcut.name : 'Choose one shortcut from the list.'}</p>
              </div>
            </div>

            <div className="preview-card">
              <div className="preview-box">
                <span className="preview-label">Current</span>
                <div className="preview-icon">
                  {currentPreview ? <img src={currentPreview} alt="" /> : <span>{iconForShortcut(selectedShortcut)}</span>}
                </div>
              </div>
              <ChevronRight className="preview-arrow" size={24} />
              <div className="preview-box">
                <span className="preview-label">New</span>
                <div className="preview-icon preview-draft">
                  {pendingPreview ? <img src={pendingPreview} alt="" /> : <span>?</span>}
                </div>
              </div>
            </div>

            <div className="action-row">
              <button type="button" className="button button-primary" onClick={() => imageInputRef.current?.click()}>
                <Upload size={16} />
                Upload image
              </button>
              <button type="button" className="button button-secondary" onClick={restoreSelectedShortcut}>
                <Undo2 size={16} />
                Restore
              </button>
            </div>

            <input
              ref={imageInputRef}
              type="file"
              accept="image/*"
              className="hidden-input"
              onChange={handlePickImage}
            />

            <div className="composer">
              <div className="composer-title">
                <FolderInput size={16} />
                Create a shortcut for an EXE
              </div>
              <div className="field-group">
                <label>Executable path</label>
                <div className="inline-fields">
                  <input
                    type="text"
                    value={shortcutForm.exePath}
                    onChange={(event) => setShortcutForm((current) => ({ ...current, exePath: event.target.value }))}
                    placeholder="Paste the full path or use Browse"
                  />
                  <button type="button" className="button button-secondary" onClick={handlePickExecutable}>
                    Browse
                  </button>
                </div>
              </div>

              <div className="field-group">
                <label>Application name</label>
                <input
                  type="text"
                  value={shortcutForm.appName}
                  onChange={(event) => setShortcutForm((current) => ({ ...current, appName: event.target.value }))}
                  placeholder="Example App"
                />
              </div>

              <div className="field-group">
                <label>Custom icon</label>
                <div className="inline-fields">
                  <input
                    type="text"
                    value={shortcutForm.iconLabel}
                    readOnly
                    placeholder="Upload an image to convert to ICO"
                  />
                  <button
                    type="button"
                    className="button button-secondary"
                    onClick={() => imageInputRef.current?.click()}
                  >
                    <ImagePlus size={16} />
                    Choose
                  </button>
                </div>
              </div>

              <button type="button" className="button button-primary full-width" onClick={createShortcut}>
                <Sparkles size={16} />
                Create desktop shortcut
              </button>
            </div>

            {commonApps.length > 0 && (
              <div className="common-apps">
                <div className="panel-subtitle">Common apps found on this machine</div>
                <div className="chip-grid">
                  {commonApps.map((app) => (
                    <button
                      key={app.path}
                      type="button"
                      className="chip"
                      onClick={() =>
                        setShortcutForm((current) => ({
                          ...current,
                          exePath: app.path,
                          appName: app.name,
                        }))
                      }
                    >
                      <Monitor size={14} />
                      {app.name}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </aside>
        </section>

        <section className="panel themes-panel">
          <div className="panel-header">
            <div>
              <h2>Theme packs</h2>
              <p>Apply a curated look to the selected shortcut when the theme includes that app.</p>
            </div>
          </div>

          <div className="theme-grid">
            {themes.map((theme) => {
              const match = selectedShortcut ? theme.icons?.[selectedShortcut.name] : null
              const previewItems = (theme.iconEntries || []).slice(0, 4)

              return (
                <article className="theme-card" key={theme.id}>
                  <div className="theme-top">
                    <div>
                      <strong>{theme.name}</strong>
                      <span>{theme.author}</span>
                    </div>
                    <small>{theme.category}</small>
                  </div>
                  <p>{theme.description}</p>

                  <div className="theme-preview-row">
                    {previewItems.map((icon) => (
                      <button
                        type="button"
                        className="theme-preview-icon theme-preview-button"
                        key={`${theme.id}-${icon.filename}`}
                        title={icon.label}
                        onClick={() => previewThemeEntry(theme, icon)}
                      >
                        {icon?.url ? <img src={icon.url} alt="" /> : <span>{iconForShortcut({ name: icon.label })}</span>}
                      </button>
                    ))}
                  </div>

                  {!!theme.iconEntries?.length && (
                    <div className="theme-icon-list">
                      {theme.iconEntries.map((icon) => (
                        <button
                          type="button"
                          key={`${theme.id}-pick-${icon.filename}`}
                          className="chip"
                          onClick={() => previewThemeEntry(theme, icon)}
                        >
                          {icon.label}
                        </button>
                      ))}
                    </div>
                  )}

                  <button
                    type="button"
                    className="button button-secondary full-width"
                    onClick={() => applyThemeToSelected(theme)}
                    disabled={!match}
                  >
                    <Sparkles size={16} />
                    {match ? 'Preview selected shortcut' : 'Theme has no match'}
                  </button>
                </article>
              )
            })}
          </div>
        </section>

        <section className="panel history-panel">
          <div className="panel-header">
            <div>
              <h2>Recent activity</h2>
              <p>What changed most recently.</p>
            </div>
          </div>

          <div className="history-list">
            {history.map((entry) => (
              <div className="history-item" key={`${entry.id || entry.timestamp}-${entry.shortcut_path}`}>
                <div className="history-left">
                  <CheckCircle2 size={16} />
                  <div>
                    <strong>{entry.shortcut_name}</strong>
                    <span>{entry.action}</span>
                  </div>
                </div>
                <small>{formatTimestamp(entry.timestamp)}</small>
              </div>
            ))}

            {!history.length && (
              <div className="empty-state compact">
                <CheckCircle2 size={20} />
                <span>No icon changes yet.</span>
              </div>
            )}
          </div>
        </section>
      </main>

      {preview && selectedShortcut && (
        <div className="modal-overlay" onClick={() => setPreview(null)} role="presentation">
          <div className="modal-card" onClick={(event) => event.stopPropagation()} role="dialog" aria-modal="true">
            <div className="modal-header">
              <div>
                <strong>Preview changes</strong>
                <p>{preview.title}</p>
              </div>
              <button type="button" className="icon-button" onClick={() => setPreview(null)} aria-label="Close preview">
                <X size={18} />
              </button>
            </div>

            <div className="preview-stage">
              <div className="preview-box">
                <span className="preview-label">Current icon</span>
                <div className="preview-icon large">
                  {currentPreview ? <img src={currentPreview} alt="" /> : <span>{iconForShortcut(selectedShortcut)}</span>}
                </div>
              </div>
              <ChevronRight className="preview-arrow" size={24} />
              <div className="preview-box">
                <span className="preview-label">New icon</span>
                <div className="preview-icon large preview-draft">
                  {pendingPreview ? <img src={pendingPreview} alt="" /> : <span>?</span>}
                </div>
              </div>
            </div>

            <div className="modal-actions">
              <button type="button" className="button button-secondary" onClick={() => setPreview(null)}>
                Cancel
              </button>
              <button type="button" className="button button-primary" onClick={applyPreview}>
                Apply now
              </button>
            </div>
          </div>
        </div>
      )}

      {toast && (
        <div className={`toast toast-${toast.kind}`}>
          <span>{toast.message}</span>
        </div>
      )}

      {loading && (
        <div className="loading-overlay">
          <RefreshCw size={18} className="spin" />
          <span>Loading Iconique...</span>
        </div>
      )}
    </div>
  )
}

export default App
