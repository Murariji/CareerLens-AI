export type AIAnalysis = {
  model: string
  fit_summary: string
  strengths: { skill: string; resume_evidence: string }[]
  gaps: { skill: string; job_requirement: string; how_to_close: string }[]
  resume_suggestions: string[]
  interview_questions: { question: string; why_asked: string }[]
  removed_unsupported_items: number
}

export type AnalysisResult = {
  is_demo: boolean
  analysis_source: 'baseline' | 'ai'
  ai_analysis: AIAnalysis | null
  ai_notice: string | null
  summary: string
  message: string
  resume_filename: string
  extracted_links: string[]
  match_score: number
  matching_skills: string[]
  missing_skills: string[]
  resume_suggestions: string[]
  target_role: string
  location: string | null
  application_plan: {
    readiness: 'ready_to_apply' | 'apply_after_updates' | 'build_evidence_first'
    headline: string
    reason: string
    next_actions: string[]
  }
}

// Set VITE_API_BASE_URL in Netlify (Site configuration > Environment variables) for the live site.
// It is public by design: never put secret keys in a VITE_ variable.
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/+$/, '')

export async function analyzeCareerFit(
  resume: File,
  jobDescription: string,
  targetRole: string,
  location: string,
): Promise<AnalysisResult> {
  const formData = new FormData()
  formData.append('resume', resume)
  formData.append('job_description', jobDescription)
  formData.append('target_role', targetRole)
  formData.append('location', location)

  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error('The analysis request could not be completed. Please try again.')
  }

  return response.json() as Promise<AnalysisResult>
}
