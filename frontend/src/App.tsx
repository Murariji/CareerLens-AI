import { FormEvent, useEffect, useRef, useState } from 'react'
import { AnalysisResult, ServerStatus, UsageStats, analyzeCareerFit, fetchStats, wakeServer } from './api/client'
import { Icon, IconName } from './components/Icon'
import { DASHBOARD_SECTIONS, ResultsDashboard } from './components/ResultsDashboard'
import {
  SavedReport,
  TrackedOpportunity,
  addToHistory,
  clearHistory,
  formatWhen,
  getReport,
  loadHistory,
  loadTracker,
  saveTracker,
} from './lib/history'
import sampleReport from './sampleReport.json'

const SAMPLE = sampleReport as AnalysisResult
const SAMPLE_ID = 'sample'

type ThemeChoice = 'light' | 'dark' | 'system'

const THEME_STORAGE_KEY = 'careerlens-theme'
const SIDEBAR_STORAGE_KEY = 'careerlens-sidebar-collapsed'
const PROGRESS_STEPS = ['Reading your PDF', 'Matching skills to the job', 'Running ATS checks', 'Writing your action plan']

function readStorage(key: string): string | null {
  try {
    return window.localStorage.getItem(key)
  } catch {
    return null
  }
}

function writeStorage(key: string, value: string) {
  try {
    window.localStorage.setItem(key, value)
  } catch {
    // Storage can be unavailable (private mode, quota); the app still works for this visit.
  }
}

function useTheme() {
  const [choice, setChoice] = useState<ThemeChoice>(() => {
    const stored = readStorage(THEME_STORAGE_KEY)
    return stored === 'light' || stored === 'dark' || stored === 'system' ? stored : 'system'
  })

  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const apply = () => {
      const resolved = choice === 'system' ? (media.matches ? 'dark' : 'light') : choice
      document.documentElement.dataset.theme = resolved
    }
    apply()
    writeStorage(THEME_STORAGE_KEY, choice)
    media.addEventListener('change', apply)
    return () => media.removeEventListener('change', apply)
  }, [choice])

  return [choice, setChoice] as const
}

function ThemeSwitch({ choice, onChange }: { choice: ThemeChoice; onChange: (choice: ThemeChoice) => void }) {
  const options: { id: ThemeChoice; label: string; icon: IconName }[] = [
    { id: 'light', label: 'Light', icon: 'sun' },
    { id: 'dark', label: 'Dark', icon: 'moon' },
    { id: 'system', label: 'Auto', icon: 'monitor' },
  ]
  return (
    <div className="theme-switch" role="radiogroup" aria-label="Colour theme">
      {options.map((option) => (
        <button
          key={option.id}
          type="button"
          role="radio"
          aria-checked={choice === option.id}
          className={choice === option.id ? 'active' : ''}
          onClick={() => onChange(option.id)}
          title={option.id === 'system' ? 'Follow your device setting' : `${option.label} theme`}
        >
          <Icon name={option.icon} size={15} />
          <span>{option.label}</span>
        </button>
      ))}
    </div>
  )
}

function ServerPill({ status }: { status: ServerStatus }) {
  if (status.state === 'waking') return <span className="server-pill waking"><i />Waking server…</span>
  if (status.state === 'offline') return <span className="server-pill offline"><i />Server unreachable</span>
  return (
    <span className="server-pill ready">
      <i />{status.aiEnabled ? `AI ready · ${status.aiProvider}` : 'Ready · rule-based'}
    </span>
  )
}

function App() {
  const [themeChoice, setThemeChoice] = useTheme()
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [jobDescription, setJobDescription] = useState('')
  const [targetRole, setTargetRole] = useState('')
  const [location, setLocation] = useState('India')
  const [error, setError] = useState('')
  const startsWithSample = new URLSearchParams(window.location.search).has('sample')
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(startsWithSample ? SAMPLE : null)
  const [reportId, setReportId] = useState<string | null>(startsWithSample ? SAMPLE_ID : null)
  const [history, setHistory] = useState<SavedReport[]>(loadHistory)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const [server, setServer] = useState<ServerStatus>({ state: 'waking' })
  const [usage, setUsage] = useState<UsageStats | null>(null)
  const [trackedOpportunities, setTrackedOpportunities] = useState<TrackedOpportunity[]>(loadTracker)
  const [feedback, setFeedback] = useState('')
  const [activeSection, setActiveSection] = useState('analyse')
  const [menuOpen, setMenuOpen] = useState(false)
  const [collapsed, setCollapsed] = useState(() => readStorage(SIDEBAR_STORAGE_KEY) === '1')
  const resultsRef = useRef<HTMLDivElement>(null)
  const isSample = reportId === SAMPLE_ID

  const navItems: { id: string; label: string; icon: IconName }[] = [
    { id: 'analyse', label: 'Analyse', icon: 'upload' },
    ...(analysis ? DASHBOARD_SECTIONS : []),
    { id: 'tracker', label: 'Tracker', icon: 'bookmark' },
  ]

  useEffect(() => {
    let active = true
    wakeServer().then(async (status) => {
      if (!active) return
      setServer(status)
      if (status.state === 'ready') {
        const stats = await fetchStats()
        if (active) setUsage(stats)
      }
    })
    return () => { active = false }
  }, [])

  useEffect(() => {
    writeStorage(SIDEBAR_STORAGE_KEY, collapsed ? '1' : '0')
  }, [collapsed])

  useEffect(() => {
    if (!feedback) return
    const timer = window.setTimeout(() => setFeedback(''), 4000)
    return () => window.clearTimeout(timer)
  }, [feedback])

  useEffect(() => {
    if (!isAnalyzing) return
    setElapsed(0)
    const timer = window.setInterval(() => setElapsed((seconds) => seconds + 1), 1000)
    return () => window.clearInterval(timer)
  }, [isAnalyzing])

  // Highlight the sidebar item for the section currently on screen.
  useEffect(() => {
    const elements = navItems.map((item) => document.getElementById(item.id)).filter(Boolean) as HTMLElement[]
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)
        if (visible[0]) setActiveSection(visible[0].target.id)
      },
      { rootMargin: '-15% 0px -70% 0px' },
    )
    elements.forEach((element) => observer.observe(element))
    return () => observer.disconnect()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [analysis])

  function goTo(id: string) {
    setMenuOpen(false)
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  function showReport(next: AnalysisResult, id: string) {
    setError('')
    setAnalysis(next)
    setReportId(id)
    setMenuOpen(false)
    window.setTimeout(() => goTo('overview'), 60)
  }

  function openSaved(id: string | undefined) {
    if (id === SAMPLE_ID) return showReport(SAMPLE, SAMPLE_ID)
    const saved = id ? getReport(id) : null
    if (saved) showReport(saved.analysis, saved.id)
    else setFeedback('That report was saved before history existed. Analyse the resume again to keep a copy.')
  }

  function persistTracker(nextItems: TrackedOpportunity[]) {
    setTrackedOpportunities(nextItems)
    saveTracker(nextItems)
  }

  function trackedFor(current: AnalysisResult | null) {
    if (!current) return undefined
    return trackedOpportunities.find((item) => (reportId && item.reportId === reportId)
      || (!item.reportId && item.role === current.target_role && item.location === (current.location ?? '')))
  }

  function saveToTracker(status: TrackedOpportunity['status']) {
    if (!analysis) return
    const existing = trackedFor(analysis)
    const item: TrackedOpportunity = {
      id: existing?.id ?? `t${Date.now().toString(36)}`,
      role: analysis.target_role,
      location: analysis.location ?? '',
      score: analysis.match_score,
      readiness: analysis.application_plan.readiness,
      status,
      reportId: reportId ?? existing?.reportId,
      updatedAt: new Date().toISOString(),
    }
    persistTracker(existing ? trackedOpportunities.map((entry) => (entry.id === item.id ? item : entry)) : [item, ...trackedOpportunities])
    setFeedback(status === 'applied' ? `Marked "${item.role}" as applied. Good luck!` : `Saved "${item.role}" to your tracker.`)
  }

  function removeFromTracker(id: string) {
    persistTracker(trackedOpportunities.filter((item) => item.id !== id))
  }

  function handleClearHistory() {
    clearHistory()
    setHistory([])
    setFeedback('Recent analyses cleared from this browser.')
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setFeedback('')

    if (!resumeFile) return setError('Please choose your resume as a PDF file.')
    if (resumeFile.type !== 'application/pdf' && !resumeFile.name.toLowerCase().endsWith('.pdf')) return setError('Please upload a PDF resume.')
    if (resumeFile.size > 5 * 1024 * 1024) return setError('Please upload a PDF smaller than 5 MB.')
    if (targetRole.trim().length < 2) return setError('Please enter the target role you are seeking.')
    if (jobDescription.trim().length < 30) return setError('Please paste at least 30 characters of the job description.')

    setIsAnalyzing(true)
    try {
      const result = await analyzeCareerFit(resumeFile, jobDescription, targetRole, location)
      const id = addToHistory(result)
      setHistory(loadHistory())
      showReport(result, id)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Something went wrong.')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const stepIndex = Math.min(PROGRESS_STEPS.length - 1, Math.floor(elapsed / 2))

  return (
    <div className={`shell ${collapsed ? 'collapsed' : ''}`}>
      <aside className={`sidebar ${menuOpen ? 'open' : ''} ${collapsed ? 'collapsed' : ''}`} aria-label="Sections">
        <button
          type="button"
          className="brand"
          onClick={() => (menuOpen ? setMenuOpen(false) : setCollapsed((value) => !value))}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-expanded={!collapsed}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <span className="brand-mark">C</span>
          <span className="brand-text">CareerLens <em>AI</em></span>
          <span className="collapse-hint" aria-hidden="true">‹</span>
        </button>

        <nav className="side-nav">
          {navItems.map((item, index) => (
            <a
              key={item.id}
              href={`#${item.id}`}
              title={collapsed ? item.label : undefined}
              className={`${activeSection === item.id ? 'active' : ''} ${index === 1 && analysis ? 'group-start' : ''}`}
              onClick={(event) => { event.preventDefault(); goTo(item.id) }}
            >
              <Icon name={item.icon} size={17} />
              <span className="nav-label">{item.label}</span>
            </a>
          ))}
        </nav>

        {history.length > 0 && (
          <div className="side-history">
            <div className="side-history-head">
              <span>Recent analyses</span>
              <button type="button" className="link-btn" onClick={handleClearHistory}>Clear</button>
            </div>
            <ul>
              {history.map((saved) => (
                <li key={saved.id}>
                  <button
                    type="button"
                    className={reportId === saved.id ? 'active' : ''}
                    onClick={() => openSaved(saved.id)}
                    title={`${saved.analysis.target_role} · ${saved.analysis.match_score}%`}
                  >
                    <span className="history-score">{saved.analysis.match_score}</span>
                    <span className="history-text">
                      <b>{saved.analysis.target_role}</b>
                      <small>{formatWhen(saved.savedAt)}</small>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {!analysis && history.length === 0 && (
          <p className="side-hint">Run an analysis (or open the sample report) to unlock the score, skills map, simulator and more.</p>
        )}
        <div className="side-foot">
          <a href="https://github.com/Murariji/CareerLens-AI" target="_blank" rel="noreferrer" title="Source on GitHub">
            <Icon name="github" size={16} /><span className="nav-label">Source on GitHub</span>
          </a>
          <span className="nav-label">MIT licensed · resumes never stored on our servers</span>
        </div>
      </aside>
      {menuOpen && <button type="button" className="scrim" aria-label="Close menu" onClick={() => setMenuOpen(false)} />}

      <main className="main">
        <div className="topbar">
          <button type="button" className="icon-btn menu-btn" aria-label="Open menu" onClick={() => setMenuOpen(true)}>
            <Icon name="menu" size={18} />
          </button>
          <ServerPill status={server} />
          <ThemeSwitch choice={themeChoice} onChange={setThemeChoice} />
        </div>

        <section id="analyse" className="analyse">
          <header className="hero">
            <p className="eyebrow"><Icon name="sparkles" size={14} />Free · private · no invented claims</p>
            <h1>See exactly how your resume <span>fits the job</span>.</h1>
            <p className="hero-copy">
              Upload your resume and paste a job description. Get a match score, the skills you can prove,
              the gaps that matter, an ATS checklist, a learning plan and interview questions in under a minute.
            </p>
            <div className="hero-actions">
              <button type="button" className="btn ghost" onClick={() => showReport(SAMPLE, SAMPLE_ID)}>
                <Icon name="sparkles" size={16} />View a sample report
              </button>
            </div>
            {usage?.persistent && usage.analyses > 0 && (
              <p className="usage">
                <span><b>{usage.analyses.toLocaleString()}</b> resumes analysed</span>
                <span><b>{usage.unique_visitors.toLocaleString()}</b> visitors</span>
              </p>
            )}
          </header>

          <form className="panel form" onSubmit={handleSubmit}>
            <div className="form-row">
              <label className="field">
                <span>Target role</span>
                <input value={targetRole} onChange={(event) => setTargetRole(event.target.value)} placeholder="e.g. ML/AI Engineer" />
              </label>
              <label className="field">
                <span>Location</span>
                <input value={location} onChange={(event) => setLocation(event.target.value)} placeholder="e.g. Bengaluru or Remote" />
              </label>
            </div>

            <div className="form-row tall">
              <label className={`drop ${resumeFile ? 'has-file' : ''}`}>
                <input
                  className="file-input"
                  type="file"
                  accept="application/pdf,.pdf"
                  onChange={(event) => setResumeFile(event.target.files?.[0] ?? null)}
                />
                <span className="drop-icon"><Icon name={resumeFile ? 'check' : 'upload'} size={22} /></span>
                <b>{resumeFile ? resumeFile.name : 'Upload your resume'}</b>
                <small>{resumeFile ? 'Ready. Click to change.' : 'PDF up to 5 MB · read in memory, never stored'}</small>
              </label>

              <label className="field grow">
                <span>Job description</span>
                <textarea
                  value={jobDescription}
                  onChange={(event) => setJobDescription(event.target.value)}
                  placeholder="Paste the responsibilities, requirements and good-to-have skills…"
                  rows={9}
                />
              </label>
            </div>

            {error && <p className="error" role="alert"><Icon name="alert" size={16} />{error}</p>}

            <div className="form-footer">
              {isAnalyzing ? (
                <ol className="progress" aria-live="polite">
                  {PROGRESS_STEPS.map((step, index) => (
                    <li key={step} className={index < stepIndex ? 'done' : index === stepIndex ? 'active' : ''}>{step}</li>
                  ))}
                  <li className="elapsed">{elapsed}s{elapsed > 12 ? ' · almost there' : ''}</li>
                </ol>
              ) : (
                <p className="muted small">
                  Never stored on our servers. In AI mode the text is sent to Groq (or Gemini as backup) for analysis. <a href="https://github.com/Murariji/CareerLens-AI/blob/main/SECURITY.md" target="_blank" rel="noreferrer">Privacy details</a>
                </p>
              )}
              <button type="submit" className="btn primary big" disabled={isAnalyzing}>
                {isAnalyzing ? 'Analysing…' : 'Analyse my fit'}<span aria-hidden="true">→</span>
              </button>
            </div>
          </form>
        </section>

        <div ref={resultsRef} className="results">
          {isSample && (
            <p className="sample-banner">
              <Icon name="sparkles" size={15} />
              Sample report for a fictional candidate (Priya, ML/AI Engineer), shown in AI mode. Upload your own resume above to get yours.
            </p>
          )}
          {analysis && (
            <ResultsDashboard
              key={reportId ?? 'current'}
              analysis={analysis}
              onTrack={saveToTracker}
              trackedStatus={trackedFor(analysis)?.status ?? null}
            />
          )}
        </div>

        <section id="tracker" className="panel section">
          <header className="section-head">
            <span className="section-icon"><Icon name="bookmark" size={18} /></span>
            <div>
              <h3>Application tracker</h3>
              <p className="muted small">Roles you've saved or applied to. Click one to reopen its full report. Stored only in this browser.</p>
            </div>
          </header>
          {trackedOpportunities.length === 0 ? (
            <p className="muted">Save an analysed role to start tracking it.</p>
          ) : (
            <ul className="tracker-list">
              {trackedOpportunities.map((item) => {
                const openable = item.reportId === SAMPLE_ID || Boolean(item.reportId && getReport(item.reportId))
                return (
                  <li key={item.id} className={openable ? 'openable' : ''}>
                    <button type="button" className="tracker-open" onClick={() => openSaved(item.reportId)} title={openable ? 'Open this report' : 'Report not saved'}>
                      <b>{item.role}</b>
                      <span>
                        {item.location || 'Location not set'} · {item.score}% match
                        {item.updatedAt ? ` · ${formatWhen(item.updatedAt)}` : ''}
                        {openable ? ' · Open report →' : ''}
                      </span>
                    </button>
                    <div className="tracker-right">
                      <em className={item.status}>{item.status === 'applied' ? 'Applied' : 'Saved'}</em>
                      <button type="button" className="link-btn" onClick={() => removeFromTracker(item.id)}>Remove</button>
                    </div>
                  </li>
                )
              })}
            </ul>
          )}
        </section>

        {feedback && (
          <div className="toast" role="status">
            <Icon name="check" size={16} />
            <span>{feedback}</span>
            <button type="button" className="link-btn" onClick={() => { setFeedback(''); goTo('tracker') }}>View tracker</button>
          </div>
        )}

        <footer className="footer">
          <span>© 2026 Murariji Dubey · Built with AI assistance from Claude · MIT License</span>
          <a href="https://github.com/Murariji/CareerLens-AI" target="_blank" rel="noreferrer">GitHub</a>
        </footer>
      </main>
    </div>
  )
}

export default App
