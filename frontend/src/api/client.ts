export type AnalysisResult = {
  is_demo: boolean
  summary: string
  message: string
  resume_filename: string
  extracted_links: string[]
}

const API_BASE_URL = 'http://127.0.0.1:8000'

export async function analyzeCareerFit(
  resume: File,
  jobDescription: string,
): Promise<AnalysisResult> {
  const formData = new FormData()
  formData.append('resume', resume)
  formData.append('job_description', jobDescription)

  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error('The analysis request could not be completed. Please try again.')
  }

  return response.json() as Promise<AnalysisResult>
}
