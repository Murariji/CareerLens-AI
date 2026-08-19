import { FormEvent, useState } from 'react'

type DraftAnalysis = {
  matchScore: number
  message: string
}

function App() {
  const [resume, setResume] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [error, setError] = useState('')
  const [analysis, setAnalysis] = useState<DraftAnalysis | null>(null)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setAnalysis(null)

    if (resume.trim().length < 30 || jobDescription.trim().length < 30) {
      setError('Please enter at least 30 characters in both fields before analyzing.')
      return
    }

    // Temporary local result. In the next milestone this will call our FastAPI backend.
    setAnalysis({
      matchScore: 0,
      message: 'Your inputs are ready. The next milestone connects this form to the AI analysis API.',
    })
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

        <button type="submit">Analyze my fit</button>
      </form>

      {analysis && (
        <section className="result-card" aria-live="polite">
          <p className="result-label">Interface check complete</p>
          <h2>Ready for AI analysis</h2>
          <p>{analysis.message}</p>
        </section>
      )}
    </main>
  )
}

export default App
