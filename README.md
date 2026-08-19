# CareerLens AI

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

- Compare resume content with job requirements
- Identify matching skills and genuine skill gaps
- Give suggestions grounded only in the supplied resume and job description
- Generate targeted interview questions
- Refuse to invent skills, achievements, or experience

## Technology

- Frontend: React, TypeScript, and Vite
- Backend: Python and FastAPI
- AI: LLM API with structured output and guardrails
- Database: PostgreSQL (added after Version 1 works)

## Project guide

See [the project map](docs/project-map.md) to understand every folder and [the roadmap](docs/roadmap.md) for the build sequence.

## Privacy

Never commit API keys, passwords, or uploaded resumes to this repository.
