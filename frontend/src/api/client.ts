export type AnalysisResult = {
  is_demo: boolean
  summary: string
  message: string
}

const API_BASE_URL = 'http://127.0.0.1:8000'

export async function analyzeCareerFit(
  resume: string,
  jobDescription: string,
): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ resume, job_description: jobDescription }),
  })

  if (!response.ok) {
    throw new Error('The analysis request could not be completed. Please try again.')
  }

  return response.json() as Promise<AnalysisResult>
}
