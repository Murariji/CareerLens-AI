import { FormEvent, useState } from 'react'
import { AnalysisResult, analyzeCareerFit } from './api/client'

type TrackedOpportunity = {
  id: string
  role: string
  location: string
  score: number
  readiness: AnalysisResult['application_plan']['readiness']
  status: 'saved' | 'applied'
}

const TRACKER_STORAGE_KEY = 'careerlens-tracked-opportunities'

function loadTrackedOpportunities(): TrackedOpportunity[] {
  try {
    const stored = window.localStorage.getItem(TRACKER_STORAGE_KEY)
    return stored ? JSON.parse(stored) as TrackedOpportunity[] : []
  } catch {
    return []
  }
}

function App() {
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [jobDescription, setJobDescription] = useState('')
  const [targetRole, setTargetRole] = useState('')
  const [location, setLocation] = useState('India')
  const [error, setError] = useState('')
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [trackedOpportunities, setTrackedOpportunities] = useState<TrackedOpportunity[]>(loadTrackedOpportunities)
  const [feedback, setFeedback] = useState('')

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
    setFeedback(status === 'applied' ? 'Marked as applied. Nice—track the outcome when you hear back.' : 'Saved to your local application tracker.')
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setAnalysis(null)

    if (!resumeFile) {
      setError('Please choose your resume as a PDF file.')
      return
    }

    if (resumeFile.type !== 'application/pdf' && !resumeFile.name.toLowerCase().endsWith('.pdf')) {
      setError('Please upload a PDF resume.')
      return
    }

    if (resumeFile.size > 5 * 1024 * 1024) {
      setError('Please upload a PDF smaller than 5 MB.')
      return
    }

    if (jobDescription.trim().length < 30) {
      setError('Please enter at least 30 characters in the job description.')
      return
    }

    if (targetRole.trim().length < 2) {
      setError('Please enter the target role you are seeking.')
      return
    }

    setIsAnalyzing(true)

    try {
      const result = await analyzeCareerFit(resumeFile, jobDescription, targetRole, location)
      setAnalysis(result)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Something went wrong.')
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <main className="page-shell">
      <nav className="topbar" aria-label="Main navigation">
        <a className="brand" href="#top" aria-label="CareerLens AI home">
          <span className="brand-mark">C</span>
          <span>CareerLens <em>AI</em></span>
        </a>
        <span className="beta-pill">Early access</span>
      </nav>

      <section className="hero" id="top">
        <div className="hero-copy-block">
          <p className="eyebrow"><span className="pulse-dot" />Evidence-grounded career guidance</p>
          <h1>Know your fit.<br /><span>Own your next move.</span></h1>
          <p className="hero-copy">
            Turn a resume and job description into clear, truthful career guidance—without guessing or inventing experience.
          </p>
          <div className="hero-points" aria-label="CareerLens benefits">
            <span>PDF-first</span><span>Private by design</span><span>Built for action</span>
          </div>
        </div>
        <aside className="trust-card">
          <p className="trust-title">What you’ll get</p>
          <div><b>01</b><span>Role-fit summary</span></div>
          <div><b>02</b><span>Evidence-based gaps</span></div>
          <div><b>03</b><span>Interview preparation</span></div>
        </aside>
      </section>

      <section className="workspace">
        <div className="workspace-heading">
          <div>
            <p className="section-kicker">Your starting point</p>
            <h2>Build your career snapshot</h2>
          </div>
          <p>Two inputs. A clearer direction.</p>
        </div>

        <form className="analysis-form" onSubmit={handleSubmit}>
          <label htmlFor="target-role" className="compact-field target-role-field">
            <span className="step-number">01</span>
            <span className="field-title">Target role</span>
            <input id="target-role" value={targetRole} onChange={(event) => setTargetRole(event.target.value)} placeholder="e.g. Marketing Analyst" />
          </label>
          <label htmlFor="location" className="compact-field location-field">
            <span className="field-title">Preferred location</span>
            <input id="location" value={location} onChange={(event) => setLocation(event.target.value)} placeholder="e.g. Bengaluru or Remote" />
          </label>
          <label htmlFor="resume" className={`file-field ${resumeFile ? 'has-file' : ''}`}>
            <input
              id="resume"
              className="file-input"
              type="file"
              accept="application/pdf,.pdf"
              onChange={(event) => setResumeFile(event.target.files?.[0] ?? null)}
            />
            <span className="step-number">02</span>
            <span className="upload-icon" aria-hidden="true">↑</span>
            <span className="field-title">{resumeFile ? 'Resume selected' : 'Upload your resume'}</span>
            <span className="field-description">{resumeFile ? resumeFile.name : 'Choose a PDF file up to 5 MB'}</span>
            <span className="field-helper">{resumeFile ? 'Ready to analyze' : 'Your file is read temporarily and never stored'}</span>
          </label>

          <label htmlFor="job-description" className="job-field">
            <span className="step-number">03</span>
            <span className="field-title">Add the job description</span>
            <textarea
              id="job-description"
              value={jobDescription}
              onChange={(event) => setJobDescription(event.target.value)}
              placeholder="Paste the responsibilities, required skills, and qualifications here..."
              rows={10}
            />
            <span className="field-helper">The more specific the description, the more useful the analysis.</span>
          </label>

          {error && <p className="error" role="alert">{error}</p>}

          <div className="form-footer">
            <p><span aria-hidden="true">⌁</span> Your data stays in this session.</p>
            <button type="submit" disabled={isAnalyzing}>
              {isAnalyzing ? 'Preparing your analysis...' : 'Analyze my fit'} <span aria-hidden="true">→</span>
            </button>
          </div>
        </form>
      </section>

      {analysis && (
        <section className="result-card" aria-live="polite">
          <div className="result-status"><span className="pulse-dot" />{analysis.is_demo ? 'Analysis pipeline connected' : 'Career analysis'}</div>
          <div className="result-content">
            <div className="result-icon" aria-hidden="true">✓</div>
            <div>
              <h2>{analysis.summary}</h2>
              <p>{analysis.message}</p>
            </div>
          </div>
          <div className="match-score" aria-label={`Match score: ${analysis.match_score} percent`}>
            <div className="score-circle"><strong>{analysis.match_score}</strong><span>%</span></div>
            <div><b>Evidence match</b><p>Based on skills and relevant terms found in your CV and the role description.</p></div>
          </div>
          <div className="insight-grid">
            <article className="insight-card positive">
              <p>Skills already evidenced</p>
              {analysis.matching_skills.length > 0 ? <div className="tag-list">{analysis.matching_skills.map((skill) => <span key={skill}>{skill}</span>)}</div> : <small>No catalogued skill overlap was detected yet.</small>}
            </article>
            <article className="insight-card gap">
              <p>Skills to close the gap</p>
              {analysis.missing_skills.length > 0 ? <div className="tag-list">{analysis.missing_skills.map((skill) => <span key={skill}>{skill}</span>)}</div> : <small>No catalogued skill gaps were detected.</small>}
            </article>
          </div>
          {analysis.resume_suggestions.length > 0 && (
            <div className="suggestion-list">
              <p>Truthful resume improvements</p>
              <ol>{analysis.resume_suggestions.map((suggestion) => <li key={suggestion}>{suggestion}</li>)}</ol>
            </div>
          )}
          <section className={`readiness-card ${analysis.application_plan.readiness}`}>
            <p className="result-label">Your next best action</p>
            <h3>{analysis.application_plan.headline}</h3>
            <p>{analysis.application_plan.reason}</p>
            <ol>{analysis.application_plan.next_actions.map((action) => <li key={action}>{action}</li>)}</ol>
            <div className="tracker-actions">
              <button type="button" onClick={() => saveToTracker('saved')}>Save opportunity</button>
              <button type="button" className="secondary-action" onClick={() => saveToTracker('applied')}>Mark as applied</button>
            </div>
          </section>
          {feedback && <p className="feedback-message" role="status">{feedback}</p>}
          {analysis.extracted_links.length > 0 && (
            <p className="link-note">
              <b>{analysis.extracted_links.length}</b> link{analysis.extracted_links.length === 1 ? '' : 's'} found in your resume. They were extracted but not opened.
            </p>
          )}
        </section>
      )}
      <section className="tracker-panel" aria-label="Local application tracker">
        <div><p className="section-kicker">Your local tracker</p><h2>Opportunities you’re acting on</h2></div>
        {trackedOpportunities.length === 0 ? <p className="empty-tracker">Save an analyzed role to begin tracking it. Your tracker stays in this browser for now.</p> : (
          <ul>{trackedOpportunities.map((item) => <li key={item.id}><div><b>{item.role}</b><span>{item.location || 'Location not set'} · {item.score}% evidence match</span></div><em className={item.status}>{item.status === 'applied' ? 'Applied' : 'Saved'}</em></li>)}</ul>
        )}
      </section>
    </main>
  )
}

export default App
