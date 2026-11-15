# CareerLens AI

**Live demo:** https://careerlens-ai-lite.netlify.app · **API docs:** https://careerlens-ai-z6xa.onrender.com/docs · [Deployment guide](docs/deployment.md)

> The API runs on a free server that sleeps when idle, so the first analysis can take 30–60 seconds.

CareerLens AI is a GenAI-powered career assistant for students and early-career professionals. It compares a resume with a job description, identifies evidence-based skill gaps, and prepares tailored interview questions without inventing qualifications.

## Version 1 goal

A user uploads a resume PDF and pastes a job description into a web page. The application extracts the resume text in memory and returns a structured analysis containing a match summary, strengths, skill gaps, truthful improvement suggestions, and interview questions.

## How it works

```text
User's browser
     |
     v
React frontend  -->  FastAPI backend  -->  LLM API
     ^                    |
     |                    v
Display result        Guardrails and validation
```

The frontend collects and displays information. The backend keeps the AI key secure, gives the model precise instructions, and validates its response before returning it to the user.

## Planned capabilities

- Compare resume content with job requirements using an explainable baseline
- Identify matching skills and genuine skill gaps
- Give suggestions grounded only in the supplied resume and job description
- Generate targeted interview questions
- Refuse to invent skills, achievements, or experience

## How the current match score works

The match score comes from a transparent baseline. It detects a curated set of skills in both the uploaded resume and the job description, then combines skill coverage with relevant-term coverage. The result is an **evidence match**, not a promise of interview success or an ATS score.

This baseline is important: it is reproducible, testable, and gives us a benchmark for evaluating the AI analysis.

## How the AI analysis works

When the backend has an Anthropic API key, it also asks Claude (`claude-opus-5-5` by default) for a structured analysis: a fit summary, strengths, gaps, truthful resume suggestions, and interview questions. The code is in `backend/app/services/llm_analyzer.py`.

- Every strength must quote the resume word-for-word, and every gap must quote the job description. The backend checks each quote against the real text and drops any claim it cannot find.
- Resume and job text are passed to the model as data, never as instructions.
- If no key is set or the AI call fails, the API still returns the baseline report with a short notice.

To enable it locally (PowerShell):

```powershell
$env:ANTHROPIC_API_KEY = "your-key"            # never commit this
# optional: $env:CAREERLENS_LLM_MODEL = "claude-sonnet-5-5"
cd backend; .venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Technology

- Frontend: React, TypeScript, and Vite
- Backend: Python and FastAPI
- AI: LLM API with structured output and guardrails
- Database: PostgreSQL (added after Version 1 works)

## Project guide

See [the project map](docs/project-map.md) to understand every folder and [the roadmap](docs/roadmap.md) for the build sequence.

## Privacy

Never commit API keys, passwords, or uploaded resumes to this repository.
