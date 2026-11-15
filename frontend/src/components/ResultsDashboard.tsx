import { useState } from 'react'
import { AnalysisResult } from '../api/client'

type Tab = 'overview' | 'skills' | 'fixes' | 'interview'

const TABS: { id: Tab; label: string }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'skills', label: 'Skills' },
  { id: 'fixes', label: 'Resume fixes' },
  { id: 'interview', label: 'Interview prep' },
]

function tone(percent: number): 'good' | 'mid' | 'low' {
  if (percent >= 70) return 'good'
  if (percent >= 45) return 'mid'
  return 'low'
}

function ScoreRing({ value, label }: { value: number; label: string }) {
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - Math.max(0, Math.min(value, 100)) / 100)
  return (
    <div className={`score-ring ${tone(value)}`} role="img" aria-label={`${label}: ${value} percent`}>
      <svg viewBox="0 0 128 128" aria-hidden="true">
        <circle className="ring-track" cx="64" cy="64" r={radius} />
        <circle
          className="ring-value"
          cx="64"
          cy="64"
          r={radius}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="ring-label">
        <strong>{value}<small>%</small></strong>
        <span>{label}</span>
      </div>
    </div>
  )
}

function Meter({ label, matched, total, suffix }: { label: string; matched: number; total: number; suffix?: string }) {
  const percent = total ? Math.round((matched / total) * 100) : 0
  return (
    <div className="meter">
      <div className="meter-head">
        <span>{label}</span>
        <b>{total ? `${matched}/${total}` : 'n/a'}{suffix ? ` ${suffix}` : ''}</b>
      </div>
      <div className="meter-track"><div className={`meter-fill ${tone(percent)}`} style={{ width: `${percent}%` }} /></div>
    </div>
  )
}

function fallbackQuestions(analysis: AnalysisResult) {
  const fromStrengths = analysis.skill_evidence.filter((e) => e.demonstrated).slice(0, 3).map((e) => ({
    question: `Walk me through how you used ${e.skill}: "${e.evidence}". What was hardest, and what would you do differently?`,
    why_asked: `Your resume claims ${e.skill}; interviewers test depth on claimed skills.`,
  }))
  const fromGaps = analysis.gaps.filter((g) => g.required).slice(0, 2).map((g) => ({
    question: `This role needs ${g.skill}. How would you get productive with it in your first month?`,
    why_asked: `${g.skill} is required but not shown on your resume, so expect to be asked about it.`,
  }))
  return [...fromStrengths, ...fromGaps]
}

export function ResultsDashboard({
  analysis,
  onTrack,
}: {
  analysis: AnalysisResult
  onTrack: (status: 'saved' | 'applied') => void
}) {
  const [tab, setTab] = useState<Tab>(() => {
    const requested = new URLSearchParams(window.location.search).get('tab')
    return TABS.some((item) => item.id === requested) ? (requested as Tab) : 'overview'
  })
  const ai = analysis.ai_analysis
  const ats = analysis.ats
  const requiredGaps = analysis.gaps.filter((g) => g.required)
  const bonusGaps = analysis.gaps.filter((g) => !g.required)
  const strengths = ai?.strengths.length
    ? ai.strengths.map((s) => ({ skill: s.skill, evidence: s.resume_evidence, demonstrated: true }))
    : analysis.skill_evidence
  const suggestions = ai?.resume_suggestions.length ? ai.resume_suggestions : analysis.resume_suggestions
  const questions = ai?.interview_questions.length ? ai.interview_questions : fallbackQuestions(analysis)
  const plan = analysis.application_plan

  return (
    <section className="dashboard" aria-live="polite">
      <header className="dash-header">
        <div>
          <p className="kicker">{analysis.target_role}{analysis.location ? ` · ${analysis.location}` : ''}</p>
          <h2>{analysis.summary}</h2>
        </div>
        <span className={`source-pill ${analysis.analysis_source}`}>
          {ai ? `AI + rules · ${ai.provider}` : 'Rule-based analysis'}
        </span>
      </header>

      {analysis.ai_notice && <p className="notice" role="status">{analysis.ai_notice}</p>}

      <nav className="tabs" role="tablist" aria-label="Analysis sections">
        {TABS.map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={tab === item.id}
            className={tab === item.id ? 'active' : ''}
            onClick={() => setTab(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>

      {tab === 'overview' && (
        <div className="tab-panel" role="tabpanel">
          <div className="overview-grid">
            <div className="panel score-panel">
              <ScoreRing value={analysis.match_score} label="match" />
              <div className="meters">
                <Meter label="Required skills" matched={analysis.required_matched} total={analysis.required_total} />
                <Meter label="Good-to-have" matched={analysis.bonus_matched} total={analysis.bonus_total} />
                {ats && <Meter label="ATS readiness" matched={ats.passed} total={ats.total} suffix="checks" />}
              </div>
            </div>
            <div className="panel">
              <p className="panel-title">The short version</p>
              <p className="lead">{analysis.message}</p>
              <div className="quick-stats">
                <div><b>{analysis.matching_skills.length}</b><span>skills matched</span></div>
                <div><b>{requiredGaps.length}</b><span>required gaps</span></div>
                <div><b>{ats ? `${ats.score}%` : '–'}</b><span>ATS checks passed</span></div>
              </div>
            </div>
          </div>

          <div className={`panel plan ${plan.readiness}`}>
            <p className="panel-title">Your next best action</p>
            <h3>{plan.headline}</h3>
            <p className="muted">{plan.reason}</p>
            <ol className="steps">{plan.next_actions.map((action) => <li key={action}>{action}</li>)}</ol>
            <div className="actions">
              <button type="button" className="btn primary" onClick={() => onTrack('saved')}>Save opportunity</button>
              <button type="button" className="btn ghost" onClick={() => onTrack('applied')}>Mark as applied</button>
            </div>
          </div>
        </div>
      )}

      {tab === 'skills' && (
        <div className="tab-panel" role="tabpanel">
          {analysis.category_coverage.length > 0 && (
            <div className="panel">
              <p className="panel-title">Coverage by area</p>
              <div className="category-grid">
                {analysis.category_coverage.map((c) => <Meter key={c.category} label={c.category} matched={c.matched} total={c.total} />)}
              </div>
            </div>
          )}

          <div className="two-col">
            <div className="panel">
              <p className="panel-title good-text">✓ Strengths with proof</p>
              {strengths.length === 0 ? (
                <p className="muted">No job skills were found in your resume yet.</p>
              ) : (
                <ul className="evidence">
                  {strengths.map((item) => (
                    <li key={item.skill}>
                      <div className="evidence-head">
                        <b>{item.skill}</b>
                        {!item.demonstrated && <span className="tag warn">listed only</span>}
                      </div>
                      {item.evidence && <q>{item.evidence}</q>}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="panel">
              <p className="panel-title bad-text">✗ Gaps and how to close them</p>
              {ai?.gaps.length ? (
                <ul className="evidence">
                  {ai.gaps.map((g) => (
                    <li key={g.skill}>
                      <div className="evidence-head"><b>{g.skill}</b></div>
                      <q>{g.job_requirement}</q>
                      <p className="idea">→ {g.how_to_close}</p>
                    </li>
                  ))}
                </ul>
              ) : analysis.gaps.length === 0 ? (
                <p className="muted">No gaps against the skills in this job description.</p>
              ) : (
                <ul className="evidence">
                  {[...requiredGaps, ...bonusGaps].map((g) => (
                    <li key={g.skill}>
                      <div className="evidence-head">
                        <b>{g.skill}</b>
                        <span className={`tag ${g.required ? 'bad' : 'info'}`}>{g.required ? 'required' : 'good to have'}</span>
                      </div>
                      <p className="idea">→ {g.project_idea}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}

      {tab === 'fixes' && (
        <div className="tab-panel" role="tabpanel">
          {ai && ai.bullet_rewrites.length > 0 && (
            <div className="panel">
              <p className="panel-title">Bullet rewrites</p>
              <div className="rewrites">
                {ai.bullet_rewrites.map((r) => (
                  <article key={r.original} className="rewrite">
                    <p className="before"><span>Before</span>{r.original}</p>
                    <p className="after"><span>After</span>{r.improved}</p>
                    <p className="why">{r.why}</p>
                  </article>
                ))}
              </div>
              <p className="footnote">Fill in any [X] placeholders with your real numbers, or delete them.</p>
            </div>
          )}

          <div className="two-col">
            {ats && (
              <div className="panel">
                <p className="panel-title">ATS readiness · {ats.passed}/{ats.total}</p>
                <ul className="checklist">
                  {ats.checks.map((check) => (
                    <li key={check.id} className={check.passed ? 'pass' : 'fail'}>
                      <span className="check-icon" aria-hidden="true">{check.passed ? '✓' : '!'}</span>
                      <div><b>{check.label}</b><p>{check.detail}</p></div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div className="panel">
              <p className="panel-title">Priority edits</p>
              <ol className="steps">{suggestions.map((s) => <li key={s}>{s}</li>)}</ol>
              {ai && ai.removed_unsupported_items > 0 && (
                <p className="footnote">
                  {ai.removed_unsupported_items} AI suggestion{ai.removed_unsupported_items === 1 ? ' was' : 's were'} removed because the evidence could not be verified in your documents.
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {tab === 'interview' && (
        <div className="tab-panel" role="tabpanel">
          <div className="panel">
            <p className="panel-title">Questions to prepare for</p>
            {questions.length === 0 ? (
              <p className="muted">Add more detail to your resume or the job description to generate questions.</p>
            ) : (
              <ol className="questions">
                {questions.map((q) => (
                  <li key={q.question}><b>{q.question}</b><p>{q.why_asked}</p></li>
                ))}
              </ol>
            )}
            {!ai && <p className="footnote">Generated from your skills and gaps. Enable AI on the server for questions tailored to your projects.</p>}
          </div>
        </div>
      )}
    </section>
  )
}
