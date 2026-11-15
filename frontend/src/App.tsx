import { FormEvent, useEffect, useRef, useState } from 'react'
import { AnalysisResult, ServerStatus, analyzeCareerFit, wakeServer } from './api/client'
import { ResultsDashboard } from './components/ResultsDashboard'
import sampleReport from './sampleReport.json'

const SAMPLE = sampleReport as AnalysisResult

type TrackedOpportunity = {
  id: string
  role: string
  location: string
  score: number
  readiness: AnalysisResult['application_plan']['readiness']
  status: 'saved' | 'applied'
}

const TRACKER_STORAGE_KEY = 'careerlens-tracked-opportunities'
const PROGRESS_STEPS = ['Reading your PDF', 'Matching skills to the job', 'Running ATS checks', 'Writing your action plan']

function loadTrackedOpportunities(): TrackedOpportunity[] {
  try {
    const stored = window.localStorage.getItem(TRACKER_STORAGE_KEY)
    return stored ? JSON.parse(stored) as TrackedOpportunity[] : []
  } catch {
    return []
  }
}

function ServerPill({ status }: { status: ServerStatus }) {
  if (status.state === 'waking') return <span className="server-pill waking"><i />Waking server…</span>
  if (status.state === 'offline') return <span className="server-pill offline"><i />Server unreachable</span>
  return (
    <span className="server-pill ready">
      <i />Ready · {status.aiEnabled ? `AI on (${status.aiProvider})` : 'rule-based mode'}
    </span>
  )
}

function App() {
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [jobDescription, setJobDescription] = useState('')
  const [targetRole, setTargetRole] = useState('')
  const [location, setLocation] = useState('India')
  const [error, setError] = useState('')
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(() =>
    new URLSearchParams(window.location.search).has('sample') ? SAMPLE : null,
  )
  const isSample = analysis === SAMPLE
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const [server, setServer] = useState<ServerStatus>({ state: 'waking' })
  const [trackedOpportunities, setTrackedOpportunities] = useState<TrackedOpportunity[]>(loadTrackedOpportunities)
  const [feedback, setFeedback] = useState('')
  const resultsRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let active = true
    wakeServer().then((status) => { if (active) setServer(status) })
    return () => { active = false }
  }, [])

  useEffect(() => {
    if (!isAnalyzing) return
    setElapsed(0)
    const timer = window.setInterval(() => setElapsed((seconds) => seconds + 1), 1000)
    return () => window.clearInterval(timer)
  }, [isAnalyzing])

  useEffect(() => {
    if (analysis) resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [analysis])

  function persistTracker(nextItems: TrackedOpportunity[]) {
    setTrackedOpportunities(nextItems)
    try {
      window.localStorage.setItem(TRACKER_STORAGE_KEY, JSON.stringify(nextItems))
    } catch {
      // Storage can be unavailable (private mode, quota); the in-memory tracker still works.
    }
  }

  function saveToTracker(status: TrackedOpportunity['status']) {
    if (!analysis) return

    const alreadyTracked = trackedOpportunities.find((item) => item.role === analysis.target_role && item.location === (analysis.location ?? ''))
    const item: TrackedOpportunity = {
      id: alreadyTracked?.id ?? `${analysis.target_role}-${Date.now()}`,
      role: analysis.target_role,
      location: analysis.location ?? '',
      score: analysis.match_score,
      readiness: analysis.application_plan.readiness,
      status,
    }
    persistTracker(
      alreadyTracked
        ? trackedOpportunities.map((entry) => (entry.id === item.id ? item : entry))
        : [...trackedOpportunities, item],
    )
    setFeedback(status === 'applied' ? 'Marked as applied. Track the outcome when you hear back.' : 'Saved to your tracker below.')
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
      setAnalysis(result)
      setServer((current) => (current.state === 'ready' ? current : { state: 'ready', aiEnabled: result.analysis_source === 'ai', aiProvider: result.ai_analysis?.provider ?? null }))
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Something went wrong.')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const stepIndex = Math.min(PROGRESS_STEPS.length - 1, Math.floor(elapsed / 2))

  return (
    <main className="page">
      <div className="glow glow-a" aria-hidden="true" />
      <div className="glow glow-b" aria-hidden="true" />

      <nav className="topbar" aria-label="Main navigation">
        <a className="brand" href="#top" aria-label="CareerLens AI home">
          <span className="brand-mark">C</span>
          <span>CareerLens <em>AI</em></span>
        </a>
        <ServerPill status={server} />
      </nav>

      <header className="hero" id="top">
        <p className="eyebrow">Free · private · no invented claims</p>
        <h1>See exactly how your resume <span>fits the job</span>.</h1>
        <p className="hero-copy">
          Upload your resume and paste a job description. Get a match score, the skills you can prove,
          the gaps that matter, an ATS checklist, and concrete fixes in under a minute.
        </p>
        <ul className="hero-points" aria-label="What you get">
          <li>Match score</li><li>Skill evidence</li><li>ATS checklist</li><li>Interview prep</li>
        </ul>
        <button type="button" className="btn ghost sample-btn" onClick={() => { setError(''); setAnalysis(SAMPLE) }}>
          No resume handy? View a sample report →
        </button>
      </header>

      <form className="card form" onSubmit={handleSubmit}>
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
            <span className="drop-icon" aria-hidden="true">{resumeFile ? '✓' : '↑'}</span>
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

        {error && <p className="error" role="alert">{error}</p>}

        <div className="form-footer">
          {isAnalyzing ? (
            <ol className="progress" aria-live="polite">
              {PROGRESS_STEPS.map((step, index) => (
                <li key={step} className={index < stepIndex ? 'done' : index === stepIndex ? 'active' : ''}>{step}</li>
              ))}
              <li className="elapsed">{elapsed}s{elapsed > 12 ? ' · waking the free server, almost there' : ''}</li>
            </ol>
          ) : (
            <p className="muted small">Your resume is analysed in memory and never stored.</p>
          )}
          <button type="submit" className="btn primary big" disabled={isAnalyzing}>
            {isAnalyzing ? 'Analysing…' : 'Analyse my fit →'}
          </button>
        </div>
      </form>

      <div ref={resultsRef}>
        {isSample && (
          <p className="sample-banner">
            Sample report for a fictional candidate (Priya, ML/AI Engineer), shown in AI mode. Upload your own resume above to get yours.
          </p>
        )}
        {analysis && <ResultsDashboard analysis={analysis} onTrack={saveToTracker} />}
        {feedback && <p className="feedback" role="status">{feedback}</p>}
      </div>

      <section className="card tracker" aria-label="Application tracker">
        <p className="kicker">Your tracker</p>
        <h2>Opportunities you're acting on</h2>
        {trackedOpportunities.length === 0 ? (
          <p className="muted">Save an analysed role to start tracking it. The tracker stays in this browser.</p>
        ) : (
          <ul>
            {trackedOpportunities.map((item) => (
              <li key={item.id}>
                <div><b>{item.role}</b><span>{item.location || 'Location not set'} · {item.score}% match</span></div>
                <em className={item.status}>{item.status === 'applied' ? 'Applied' : 'Saved'}</em>
              </li>
            ))}
          </ul>
        )}
      </section>

      <footer className="footer">
        <span>CareerLens AI · open source</span>
        <a href="https://github.com/Murariji/CareerLens-AI" target="_blank" rel="noreferrer">GitHub</a>
      </footer>
    </main>
  )
}

export default App
