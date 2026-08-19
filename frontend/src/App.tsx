import { FormEvent, useState } from 'react'
import { AnalysisResult, analyzeCareerFit } from './api/client'

function App() {
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [jobDescription, setJobDescription] = useState('')
  const [error, setError] = useState('')
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

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

    setIsAnalyzing(true)

    try {
      const result = await analyzeCareerFit(resumeFile, jobDescription)
      setAnalysis(result)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Something went wrong.')
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <main className="page-shell">
      <section className="hero">
        <p className="eyebrow">Evidence-grounded career guidance</p>
        <h1>See how your resume fits the role.</h1>
        <p className="hero-copy">
          CareerLens AI compares your real experience against a job description. It will never invent qualifications.
        </p>
      </section>

      <form className="analysis-form" onSubmit={handleSubmit}>
        <label htmlFor="resume" className="file-field">
          <span>Your resume (PDF)</span>
          <input
            id="resume"
            type="file"
            accept="application/pdf,.pdf"
            onChange={(event) => setResumeFile(event.target.files?.[0] ?? null)}
          />
          <small>{resumeFile ? `${resumeFile.name} selected` : 'Choose a PDF up to 5 MB. It is not stored.'}</small>
        </label>

        <label htmlFor="job-description">
          <span>Job description</span>
          <textarea
            id="job-description"
            value={jobDescription}
            onChange={(event) => setJobDescription(event.target.value)}
            placeholder="Paste the job description here..."
            rows={12}
          />
        </label>

        {error && <p className="error" role="alert">{error}</p>}

        <button type="submit" disabled={isAnalyzing}>
          {isAnalyzing ? 'Analyzing...' : 'Analyze my fit'}
        </button>
      </form>

      {analysis && (
        <section className="result-card" aria-live="polite">
          <p className="result-label">{analysis.is_demo ? 'Backend connection successful' : 'Career analysis'}</p>
          <h2>{analysis.summary}</h2>
          <p>{analysis.message}</p>
          {analysis.extracted_links.length > 0 && (
            <p className="link-note">
              Found {analysis.extracted_links.length} link{analysis.extracted_links.length === 1 ? '' : 's'} in the resume. They were extracted but not opened.
            </p>
          )}
        </section>
      )}
    </main>
  )
}

export default App
