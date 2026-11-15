import { ReactNode } from 'react'
import { AnalysisResult } from '../api/client'
import { Icon, IconName } from './Icon'
import { CopyButton, JobHighlighter, LearningPlan, Meter, RadarChart, ScoreRing, WhatIfSimulator, tone } from './Tools'

export const DASHBOARD_SECTIONS: { id: string; label: string; icon: IconName }[] = [
  { id: 'overview', label: 'Overview', icon: 'gauge' },
  { id: 'skills', label: 'Skills map', icon: 'radar' },
  { id: 'what-if', label: 'What-if simulator', icon: 'sliders' },
  { id: 'job-match', label: 'Job description', icon: 'file' },
  { id: 'learning-plan', label: 'Learning plan', icon: 'map' },
  { id: 'resume-fixes', label: 'Resume fixes', icon: 'edit' },
  { id: 'ats', label: 'ATS checklist', icon: 'shield' },
  { id: 'interview', label: 'Interview prep', icon: 'chat' },
]

function Section({ id, icon, title, subtitle, children, actions }: {
  id: string
  icon: IconName
  title: string
  subtitle?: string
  children: ReactNode
  actions?: ReactNode
}) {
  return (
    <section id={id} className="panel section" aria-labelledby={`${id}-title`}>
      <header className="section-head">
        <span className="section-icon"><Icon name={icon} size={18} /></span>
        <div>
          <h3 id={`${id}-title`}>{title}</h3>
          {subtitle && <p className="muted small">{subtitle}</p>}
        </div>
        {actions && <div className="section-actions">{actions}</div>}
      </header>
      {children}
    </section>
  )
}

function KpiCard({ icon, label, value, hint, tone: kpiTone }: { icon: IconName; label: string; value: string; hint: string; tone: string }) {
  return (
    <div className={`kpi ${kpiTone}`}>
      <span className="kpi-icon"><Icon name={icon} size={18} /></span>
      <div>
        <b>{value}</b>
        <span>{label}</span>
        <small>{hint}</small>
      </div>
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
  const ai = analysis.ai_analysis
  const ats = analysis.ats
  const requiredGaps = analysis.gaps.filter((g) => g.required)
  const strengths = ai?.strengths.length
    ? ai.strengths.map((s) => ({ skill: s.skill, evidence: s.resume_evidence, demonstrated: true }))
    : analysis.skill_evidence
  const suggestions = ai?.resume_suggestions.length ? ai.resume_suggestions : analysis.resume_suggestions
  const questions = ai?.interview_questions.length ? ai.interview_questions : fallbackQuestions(analysis)
  const plan = analysis.application_plan
  const requiredPercent = analysis.required_total ? Math.round((analysis.required_matched / analysis.required_total) * 100) : 0

  return (
    <div className="dashboard" aria-live="polite">
      <header className="dash-header">
        <div>
          <p className="kicker">{analysis.target_role}{analysis.location ? ` · ${analysis.location}` : ''}</p>
          <h2>{analysis.summary}</h2>
        </div>
        <div className="dash-tools">
          <span className={`source-pill ${analysis.analysis_source}`}>
            <Icon name={ai ? 'sparkles' : 'check'} size={14} />
            {ai ? `AI + rules · ${ai.provider}` : 'Rule-based'}
          </span>
          <button type="button" className="icon-btn" onClick={() => window.print()}>
            <Icon name="download" size={15} /><span>Save as PDF</span>
          </button>
        </div>
      </header>

      {analysis.ai_notice && <p className="notice" role="status"><Icon name="alert" size={16} />{analysis.ai_notice}</p>}

      <Section id="overview" icon="gauge" title="Overview" subtitle="Your fit at a glance and the single best next step.">
        <div className="overview-hero">
          <ScoreRing value={analysis.match_score} label="match" />
          <div className="overview-copy">
            <p className="lead">{analysis.message}</p>
            <div className="meters">
              <Meter label="Required skills" matched={analysis.required_matched} total={analysis.required_total} />
              <Meter label="Good-to-have skills" matched={analysis.bonus_matched} total={analysis.bonus_total} />
              {ats && <Meter label="ATS readiness" matched={ats.passed} total={ats.total} suffix="checks" />}
            </div>
          </div>
        </div>
        <div className="kpi-grid">
          <KpiCard icon="target" label="Match score" value={`${analysis.match_score}%`} hint="Weighted: required 70%, bonus 15%, keywords 15%" tone={tone(analysis.match_score)} />
          <KpiCard icon="check" label="Skills proven" value={`${analysis.matching_skills.length}`} hint={`${requiredPercent}% of required skills`} tone={tone(requiredPercent)} />
          <KpiCard icon="alert" label="Required gaps" value={`${requiredGaps.length}`} hint="See the learning plan" tone={requiredGaps.length === 0 ? 'good' : requiredGaps.length <= 2 ? 'mid' : 'low'} />
          <KpiCard icon="shield" label="ATS checks" value={ats ? `${ats.passed}/${ats.total}` : '–'} hint="Parsing and keyword readiness" tone={ats ? tone(ats.score) : 'mid'} />
        </div>
        <div className={`plan ${plan.readiness}`}>
          <p className="panel-title">Your next best action</p>
          <h4>{plan.headline}</h4>
          <p className="muted">{plan.reason}</p>
          <ol className="steps">{plan.next_actions.map((action) => <li key={action}>{action}</li>)}</ol>
          <div className="actions">
            <button type="button" className="btn primary" onClick={() => onTrack('saved')}><Icon name="bookmark" size={16} />Save opportunity</button>
            <button type="button" className="btn ghost" onClick={() => onTrack('applied')}><Icon name="check" size={16} />Mark as applied</button>
          </div>
        </div>
      </Section>

      <Section id="skills" icon="radar" title="Skills map" subtitle="Where you're strong, where you're thin, and the proof behind each skill.">
        {analysis.category_coverage.length >= 3 ? (
          <div className="skills-visual">
            <RadarChart data={analysis.category_coverage} />
            <div className="meters">
              {analysis.category_coverage.map((c) => <Meter key={c.category} label={c.category} matched={c.matched} total={c.total} />)}
            </div>
          </div>
        ) : analysis.category_coverage.length > 0 && (
          <div className="meters">
            {analysis.category_coverage.map((c) => <Meter key={c.category} label={c.category} matched={c.matched} total={c.total} />)}
          </div>
        )}
        <div className="two-col">
          <div>
            <p className="panel-title good-text">Strengths with proof</p>
            {strengths.length === 0 ? <p className="muted">No job skills were found in your resume yet.</p> : (
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
          <div>
            <p className="panel-title bad-text">Gaps</p>
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
            ) : analysis.gaps.length === 0 ? <p className="muted">No gaps against the skills in this job description.</p> : (
              <ul className="evidence">
                {analysis.gaps.map((g) => (
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
      </Section>

      <Section id="what-if" icon="sliders" title="What-if simulator" subtitle="See how your score would change if you closed specific gaps.">
        <WhatIfSimulator analysis={analysis} />
      </Section>

      <Section id="job-match" icon="file" title="Job description, decoded" subtitle="Every skill the job mentions, colour-coded against your resume.">
        <JobHighlighter segments={analysis.job_segments} />
      </Section>

      <Section id="learning-plan" icon="map" title="Learning plan" subtitle="A week-by-week plan to close the gaps with small, public projects.">
        <LearningPlan gaps={analysis.gaps} />
      </Section>

      <Section id="resume-fixes" icon="edit" title="Resume fixes" subtitle="Copy-ready rewrites and the edits that matter most.">
        {ai && ai.bullet_rewrites.length > 0 && (
          <div className="rewrites">
            {ai.bullet_rewrites.map((r) => (
              <article key={r.original} className="rewrite">
                <p className="before"><span>Before</span>{r.original}</p>
                <p className="after"><span>After</span>{r.improved}</p>
                <div className="rewrite-foot">
                  <p className="why">{r.why}</p>
                  <CopyButton text={r.improved} />
                </div>
              </article>
            ))}
            <p className="footnote">Fill in any [X] placeholders with your real numbers, or delete them.</p>
          </div>
        )}
        <p className="panel-title">Priority edits</p>
        <ol className="steps">{suggestions.map((s) => <li key={s}>{s}</li>)}</ol>
        {ai && ai.removed_unsupported_items > 0 && (
          <p className="footnote">
            <Icon name="shield" size={13} /> {ai.removed_unsupported_items} AI suggestion{ai.removed_unsupported_items === 1 ? ' was' : 's were'} removed because the evidence couldn't be verified in your documents.
          </p>
        )}
      </Section>

      {ats && (
        <Section id="ats" icon="shield" title={`ATS checklist · ${ats.passed}/${ats.total}`} subtitle="What applicant tracking systems need to read your resume correctly.">
          <div className="ats-bar" role="img" aria-label={`${ats.passed} of ${ats.total} checks passed`}>
            {ats.checks.map((check) => <span key={check.id} className={check.passed ? 'pass' : 'fail'} />)}
          </div>
          <ul className="checklist">
            {ats.checks.map((check) => (
              <li key={check.id} className={check.passed ? 'pass' : 'fail'}>
                <span className="check-icon" aria-hidden="true">{check.passed ? '✓' : '!'}</span>
                <div><b>{check.label}</b><p>{check.detail}</p></div>
              </li>
            ))}
          </ul>
        </Section>
      )}

      <Section
        id="interview"
        icon="chat"
        title="Interview prep"
        subtitle={ai ? 'Questions tailored to your projects and this job.' : 'Generated from your skills and gaps. AI mode tailors them to your projects.'}
        actions={questions.length > 0 ? <CopyButton text={questions.map((q, i) => `${i + 1}. ${q.question}`).join('\n')} label="Copy all" /> : undefined}
      >
        {questions.length === 0 ? <p className="muted">Add more detail to your resume or the job description to generate questions.</p> : (
          <div className="questions">
            {questions.map((q, index) => (
              <details key={q.question} className="question">
                <summary><span className="q-num">{index + 1}</span>{q.question}</summary>
                <p>{q.why_asked}</p>
              </details>
            ))}
          </div>
        )}
      </Section>
    </div>
  )
}
