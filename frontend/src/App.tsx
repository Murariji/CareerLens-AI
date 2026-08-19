import { FormEvent, useState } from 'react'
import { AnalysisResult, analyzeCareerFit } from './api/client'

function App() {
  const [resume, setResume] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [error, setError] = useState('')
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setAnalysis(null)

    if (resume.trim().length < 30 || jobDescription.trim().length < 30) {
      setError('Please enter at least 30 characters in both fields before analyzing.')
      return
    }

    setIsAnalyzing(true)

    try {
      const result = await analyzeCareerFit(resume, jobDescription)
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
        <label htmlFor="resume">
          <span>Your resume</span>
          <textarea
            id="resume"
            value={resume}
            onChange={(event) => setResume(event.target.value)}
            placeholder="Paste your resume text here..."
            rows={12}
          />
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
        </section>
      )}
    </main>
  )
}

export default App
