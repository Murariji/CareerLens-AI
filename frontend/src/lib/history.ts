// Saved reports and the application tracker, stored only in this browser (localStorage).
// Reports include resume snippets, so they never leave the device and can be cleared at any time.
import { AnalysisResult } from '../api/client'

export type SavedReport = { id: string; savedAt: string; analysis: AnalysisResult }

export type TrackedOpportunity = {
  id: string
  role: string
  location: string
  score: number
  readiness: AnalysisResult['application_plan']['readiness']
  status: 'saved' | 'applied'
  reportId?: string
  updatedAt?: string
}

const REPORTS_KEY = 'careerlens-reports'
const HISTORY_KEY = 'careerlens-history'
const TRACKER_KEY = 'careerlens-tracked-opportunities'
const MAX_HISTORY = 10

function read<T>(key: string, fallback: T): T {
  try {
    const raw = window.localStorage.getItem(key)
    return raw ? JSON.parse(raw) as T : fallback
  } catch {
    return fallback
  }
}

function write(key: string, value: unknown): boolean {
  try {
    window.localStorage.setItem(key, JSON.stringify(value))
    return true
  } catch {
    return false // Storage full or blocked (private mode); the app keeps working for this visit.
  }
}

export function loadTracker(): TrackedOpportunity[] {
  return read<TrackedOpportunity[]>(TRACKER_KEY, [])
}

export function saveTracker(items: TrackedOpportunity[]) {
  write(TRACKER_KEY, items)
  pruneReports(items)
}

export function loadHistory(): SavedReport[] {
  const reports = read<Record<string, SavedReport>>(REPORTS_KEY, {})
  return read<string[]>(HISTORY_KEY, []).map((id) => reports[id]).filter(Boolean)
}

export function getReport(id: string): SavedReport | null {
  return read<Record<string, SavedReport>>(REPORTS_KEY, {})[id] ?? null
}

/** Store a new analysis at the top of the history; returns its id. */
export function addToHistory(analysis: AnalysisResult): string {
  const id = `r${Date.now().toString(36)}`
  const reports = read<Record<string, SavedReport>>(REPORTS_KEY, {})
  reports[id] = { id, savedAt: new Date().toISOString(), analysis }
  const history = [id, ...read<string[]>(HISTORY_KEY, []).filter((existing) => existing !== id)].slice(0, MAX_HISTORY)
  write(HISTORY_KEY, history)
  if (!write(REPORTS_KEY, reports)) {
    // Storage full: keep only what history and the tracker still need, then retry once.
    write(REPORTS_KEY, keepOnly(reports, new Set([...history, ...trackedReportIds(loadTracker())])))
  }
  pruneReports(loadTracker())
  return id
}

export function clearHistory() {
  write(HISTORY_KEY, [])
  pruneReports(loadTracker())
}

function trackedReportIds(items: TrackedOpportunity[]): string[] {
  return items.map((item) => item.reportId).filter((id): id is string => Boolean(id))
}

function keepOnly(reports: Record<string, SavedReport>, keep: Set<string>) {
  return Object.fromEntries(Object.entries(reports).filter(([id]) => keep.has(id)))
}

/** Delete reports that are neither in the recent history nor linked from the tracker. */
function pruneReports(tracker: TrackedOpportunity[]) {
  const keep = new Set([...read<string[]>(HISTORY_KEY, []), ...trackedReportIds(tracker)])
  const reports = read<Record<string, SavedReport>>(REPORTS_KEY, {})
  if (Object.keys(reports).some((id) => !keep.has(id))) write(REPORTS_KEY, keepOnly(reports, keep))
}

export function formatWhen(iso: string): string {
  const date = new Date(iso)
  const days = Math.floor((Date.now() - date.getTime()) / 86_400_000)
  if (days === 0) return `Today, ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
  if (days === 1) return 'Yesterday'
  if (days < 7) return `${days} days ago`
  return date.toLocaleDateString([], { day: 'numeric', month: 'short' })
}
