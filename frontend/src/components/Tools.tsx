import { useMemo, useState } from 'react'
import { AnalysisResult, CategoryCoverage, Gap, JobSegment } from '../api/client'
import { Icon } from './Icon'

export function tone(percent: number): 'good' | 'mid' | 'low' {
  if (percent >= 70) return 'good'
  if (percent >= 45) return 'mid'
  return 'low'
}

/** Same formula as the backend (skill_matcher.build_match_report), so the simulator matches the real score. */
export function computeScore(requiredMatched: number, requiredTotal: number, bonusMatched: number, bonusTotal: number, termCoverage: number) {
  if (!requiredTotal && !bonusTotal) return Math.round(termCoverage * 100)
  const primary = requiredTotal ? requiredMatched / requiredTotal : bonusMatched / bonusTotal
  const secondary = bonusTotal ? bonusMatched / bonusTotal : primary
  return Math.max(0, Math.min(100, Math.round(primary * 70 + secondary * 15 + termCoverage * 15)))
}

export function ScoreRing({ value, label, size = 148 }: { value: number; label: string; size?: number }) {
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - Math.max(0, Math.min(value, 100)) / 100)
  return (
    <div className={`score-ring ${tone(value)}`} style={{ width: size, height: size }} role="img" aria-label={`${label}: ${value} percent`}>
      <svg viewBox="0 0 128 128" aria-hidden="true">
        <defs>
          <linearGradient id={`ring-${label}`} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" className="ring-stop-a" />
            <stop offset="100%" className="ring-stop-b" />
          </linearGradient>
        </defs>
        <circle className="ring-track" cx="64" cy="64" r={radius} />
        <circle
          className="ring-value"
          cx="64"
          cy="64"
          r={radius}
          stroke={`url(#ring-${label})`}
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

export function Meter({ label, matched, total, suffix }: { label: string; matched: number; total: number; suffix?: string }) {
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

export function RadarChart({ data }: { data: CategoryCoverage[] }) {
  const size = 300
  const center = size / 2
  const radius = 100
  const points = data.map((item, index) => {
    const angle = (Math.PI * 2 * index) / data.length - Math.PI / 2
    const value = item.total ? item.matched / item.total : 0
    return {
      ...item,
      value,
      x: center + Math.cos(angle) * radius * value,
      y: center + Math.sin(angle) * radius * value,
      axisX: center + Math.cos(angle) * radius,
      axisY: center + Math.sin(angle) * radius,
      labelX: center + Math.cos(angle) * (radius + 26),
      labelY: center + Math.sin(angle) * (radius + 26),
    }
  })
  const rings = [0.25, 0.5, 0.75, 1]

  return (
    <svg className="radar" viewBox={`-60 -10 ${size + 120} ${size + 20}`} role="img" aria-label="Skill coverage by area">
      {rings.map((ring) => (
        <polygon
          key={ring}
          className="radar-ring"
          points={points.map((p) => `${center + (p.axisX - center) * ring},${center + (p.axisY - center) * ring}`).join(' ')}
        />
      ))}
      {points.map((p) => <line key={p.category} className="radar-axis" x1={center} y1={center} x2={p.axisX} y2={p.axisY} />)}
      <polygon className="radar-area" points={points.map((p) => `${p.x},${p.y}`).join(' ')} />
      {points.map((p) => <circle key={p.category} className="radar-dot" cx={p.x} cy={p.y} r={4} />)}
      {points.map((p) => (
        <text
          key={p.category}
          className="radar-label"
          x={p.labelX}
          y={p.labelY}
          textAnchor={Math.abs(p.labelX - center) < 10 ? 'middle' : p.labelX > center ? 'start' : 'end'}
          dominantBaseline="middle"
        >
          {p.category} <tspan className="radar-value">{p.matched}/{p.total}</tspan>
        </text>
      ))}
    </svg>
  )
}

export function WhatIfSimulator({ analysis }: { analysis: AnalysisResult }) {
  const [picked, setPicked] = useState<Set<string>>(new Set())
  const current = analysis.match_score
  const projected = useMemo(() => {
    const required = analysis.gaps.filter((g) => g.required && picked.has(g.skill)).length
    const bonus = analysis.gaps.filter((g) => !g.required && picked.has(g.skill)).length
    return computeScore(
      analysis.required_matched + required,
      analysis.required_total,
      analysis.bonus_matched + bonus,
      analysis.bonus_total,
      analysis.term_coverage,
    )
  }, [analysis, picked])

  if (analysis.gaps.length === 0) {
    return <p className="muted">No gaps to simulate: your resume already covers the skills this job names.</p>
  }

  function toggle(skill: string) {
    setPicked((previous) => {
      const next = new Set(previous)
      if (next.has(skill)) next.delete(skill)
      else next.add(skill)
      return next
    })
  }

  const gain = projected - current
  return (
    <div className="whatif">
      <div className="whatif-scores">
        <div><span>Now</span><b className={tone(current)}>{current}%</b></div>
        <div className="whatif-arrow" aria-hidden="true">→</div>
        <div><span>If you add proof for the selected skills</span><b className={tone(projected)}>{projected}%</b></div>
        {gain > 0 && <em className="whatif-gain">+{gain} points</em>}
      </div>
      <p className="muted small">Pick the gaps you could realistically close with a project. Required skills move the score the most.</p>
      <div className="chip-grid">
        {analysis.gaps.map((gap) => (
          <button
            key={gap.skill}
            type="button"
            className={`chip ${picked.has(gap.skill) ? 'on' : ''} ${gap.required ? 'required' : 'bonus'}`}
            aria-pressed={picked.has(gap.skill)}
            onClick={() => toggle(gap.skill)}
          >
            <span className="chip-check" aria-hidden="true">{picked.has(gap.skill) ? '✓' : '+'}</span>
            {gap.skill}
            <small>{gap.required ? 'required' : 'bonus'}</small>
          </button>
        ))}
      </div>
    </div>
  )
}

const SEGMENT_LABELS: Record<string, string> = {
  matched: 'In your resume',
  missing_required: 'Missing (required)',
  missing_bonus: 'Missing (good to have)',
  covered: 'Covered by an alternative',
}

export function JobHighlighter({ segments }: { segments: JobSegment[] }) {
  if (!segments.length) return <p className="muted">The job description isn't available for this report.</p>
  return (
    <>
      <div className="legend">
        {Object.entries(SEGMENT_LABELS).map(([status, label]) => (
          <span key={status} className={`legend-item ${status}`}><i />{label}</span>
        ))}
      </div>
      <div className="jd-text">
        {segments.map((segment, index) =>
          segment.status ? (
            <mark key={index} className={segment.status} title={`${segment.skill}: ${SEGMENT_LABELS[segment.status]}`}>{segment.text}</mark>
          ) : (
            <span key={index}>{segment.text}</span>
          ),
        )}
      </div>
    </>
  )
}

export function LearningPlan({ gaps }: { gaps: Gap[] }) {
  const ordered = [...gaps.filter((g) => g.required), ...gaps.filter((g) => !g.required)].slice(0, 8)
  if (!ordered.length) return <p className="muted">Nothing to learn for this role: focus on presenting your evidence well.</p>
  const weeks: Gap[][] = []
  for (let index = 0; index < ordered.length; index += 2) weeks.push(ordered.slice(index, index + 2))

  return (
    <ol className="timeline">
      {weeks.map((week, index) => (
        <li key={index}>
          <div className="timeline-dot" aria-hidden="true">{index + 1}</div>
          <div className="timeline-body">
            <p className="timeline-week">Week {index + 1}</p>
            {week.map((gap) => (
              <div key={gap.skill} className="timeline-task">
                <b>{gap.skill}</b>
                <span className={`tag ${gap.required ? 'bad' : 'info'}`}>{gap.required ? 'required' : 'good to have'}</span>
                <p>{gap.project_idea}</p>
              </div>
            ))}
          </div>
        </li>
      ))}
    </ol>
  )
}

export function CopyButton({ text, label = 'Copy' }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false)
  async function copy() {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1500)
    } catch {
      // Clipboard can be blocked (permissions, insecure context); the text stays selectable.
    }
  }
  return (
    <button type="button" className="icon-btn" onClick={copy} aria-label={copied ? 'Copied' : label}>
      <Icon name={copied ? 'check' : 'copy'} size={15} />
      <span>{copied ? 'Copied' : label}</span>
    </button>
  )
}
