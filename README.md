# CareerLens AI

**See exactly how your resume fits a job, with evidence for every claim.**

**Live demo:** https://careerlens-ai-lite.netlify.app · **Sample report (no upload needed):** https://careerlens-ai-lite.netlify.app/?sample=1 · **API docs:** https://careerlens-ai-z6xa.onrender.com/docs

> Runs entirely on free tiers. The API sleeps when idle; the page wakes it as soon as it opens, so it's usually ready by the time you've filled in the form.

## What it does

Upload a resume PDF, paste a job description, and get a dashboard with four tabs:

| Tab | What you get |
|---|---|
| **Overview** | Match score, required vs good-to-have skill coverage, ATS readiness, and a concrete next-step plan |
| **Skills** | Coverage by area (ML & AI, Cloud & MLOps, Data…), each matched skill with the resume line that proves it, and each gap with a 1–2 week project idea to close it |
| **Resume fixes** | 8-point ATS checklist, priority edits, and (with AI on) before/after bullet rewrites |
| **Interview prep** | Questions this interviewer is likely to ask *you*, based on your projects and the job's gaps |

## Why it's different

Most resume tools give a black-box score and generic tips, and some will happily "optimise" your resume with skills you don't have. CareerLens is built around **evidence**:

- **Every strength quotes your resume; every gap quotes the job description.** The backend verifies each quote against the real text and drops anything it can't find.
- **AI rewrites can't invent facts.** A bullet rewrite is rejected if it adds a skill or a number that isn't in your original bullet; missing metrics become `[X]` placeholders for you to fill in.
- **Smart matching, not just keywords.** "PyTorch *or* TensorFlow" counts as one requirement; a PyTorch project counts as machine-learning evidence; skills that only appear in a skills list are flagged as "listed only".
- **Private.** Resumes are processed in memory and never stored.
- **Free and open source.**

## How it works

```text
Browser (React, Netlify)
   │  resume PDF + job description
   ▼
FastAPI backend (Render)
   ├─ PDF text extraction (PyMuPDF, in memory)
   ├─ Rule-based matcher: 45+ skills, required vs good-to-have, alternatives, implied skills
   ├─ ATS checker: 8 parsing and keyword checks
   └─ Optional LLM (Groq / Gemini / Claude) ──► guardrails verify every quote ──► JSON
```

The rule-based report always works, even with no AI key, and it doubles as a benchmark for the AI output.

## AI providers (optional)

Set one or more keys on the backend. With several keys, they back each other up: if the first provider fails or hits its free-tier limit, the same request is retried on the next. The order is the table's order (Groq, Gemini, Claude), and `CAREERLENS_LLM_PROVIDER` moves one provider to the front.

| Provider | Env var | Default model | Cost |
|---|---|---|---|
| Groq | `GROQ_API_KEY` | `openai/gpt-oss-120b` | Free tier (rate-limited) |
| Google Gemini | `GEMINI_API_KEY` | `gemini-3.5-flash-lite` | Free tier (Google may use free-tier inputs to improve its products) |
| Anthropic Claude | `ANTHROPIC_API_KEY` | `claude-opus-5-5` | Paid |

Override the model with `CAREERLENS_LLM_MODEL`. Keys live only on the server (Render → Environment, or `backend/.env` locally) and never in the frontend.

## Run locally

```powershell
# Backend
cd backend
python -m venv .venv; .venv\Scripts\pip install -r requirements.txt
copy .env.example .env      # optional: add GROQ_API_KEY=...
.venv\Scripts\python.exe -m uvicorn app.main:app --reload

# Frontend (second terminal)
cd frontend; npm install; npm run dev     # http://localhost:5173
```

Tests: `cd backend; .venv\Scripts\python.exe -m unittest discover -s tests`

## Tech stack

React + TypeScript + Vite · Python + FastAPI · PyMuPDF · httpx · Groq / Gemini / Anthropic APIs · Netlify + Render (free tiers)

## Limitations

- The skill catalogue is focused on tech, data and ML roles; other fields rely more on the AI analysis.
- There is no universal "ATS score". The checklist covers what reliably helps parsing and keyword filters.
- Scanned (image-only) PDFs can't be read.

## Docs

- [Deployment guide](docs/deployment.md): Render + Netlify setup, environment variables, keeping the free server warm
- [Project map](docs/project-map.md) and [roadmap](docs/roadmap.md)
