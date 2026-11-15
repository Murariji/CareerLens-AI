# Deployment Guide

CareerLens AI is deployed as two free services:

| Part | Host | Live URL |
|---|---|---|
| Backend (FastAPI) | Render (free web service) | https://careerlens-ai-z6xa.onrender.com |
| Frontend (React + Vite) | Netlify | https://careerlens-ai-lite.netlify.app |

Useful backend links:

- Health check: https://careerlens-ai-z6xa.onrender.com/api/health → `{"status":"ok"}`
- Interactive API docs: https://careerlens-ai-z6xa.onrender.com/docs

> The bare URL (`GET /`) returns a small JSON message pointing to `/docs`. The API has no web page of its own; users open the Netlify site.

Every `git push` to `main` redeploys both services automatically.

---

## 1. CareerLens backend on Render

| Field | Value |
|---|---|
| Name | `CareerLens-AI` |
| Language | Python 3 |
| Branch | `main` |
| Region | Singapore (Southeast Asia) |
| Root Directory | `backend` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Instance Type | Free ($0 / month, 0.1 CPU, 512 MB RAM) |

Environment variables (Render → service → **Environment**):

| Key | Value | Required |
|---|---|---|
| `PYTHON_VERSION` | `3.12.8` (no trailing dot) | Yes |
| `CAREERLENS_ALLOWED_ORIGINS` | `https://careerlens-ai-lite.netlify.app` (no trailing `/`; comma-separate several) | Yes |
| `GROQ_API_KEY` | Free key from console.groq.com → API Keys | Optional. Enables AI analysis (free tier). |
| `GEMINI_API_KEY` | Free key from aistudio.google.com → Get API key | Optional alternative to Groq (free tier). |
| `ANTHROPIC_API_KEY` | Key from console.anthropic.com → API Keys | Optional (paid). |
| `CAREERLENS_LLM_PROVIDER` | `groq`, `gemini` or `anthropic` | Optional. Which provider to try first; the others with keys are automatic fallbacks. |
| `CAREERLENS_LLM_MODEL` | e.g. `llama-3.3-70b-versatile` | Optional. Overrides the provider's default model. |

Without any AI key the app still returns the full rule-based report.

### Keep the free server warm (automatic, free)

Free Render services sleep after ~15 minutes idle, and the first request after that takes 30–60 s.
The repository includes a GitHub Action, [`.github/workflows/keep-api-warm.yml`](../.github/workflows/keep-api-warm.yml),
that pings `/api/health` every 10 minutes, so visitors almost never wait. Nothing to set up: it runs once the file is on `main`.

- Check it under the repository's **Actions** tab → **Keep API warm**. You can also run it by hand with **Run workflow**.
- GitHub can delay scheduled runs at busy times, and it pauses schedules after 60 days without commits.
  If that happens, press **Enable workflow** in the Actions tab.
- One always-on free service uses ~730 of Render's 750 free hours per month, so keep only one service warm.
- Backup option: a free monitor on **uptimerobot.com** pinging the same URL every 5–10 minutes.

### Rate limit

`/api/analyze` allows 20 analyses per visitor per hour by default, which protects the free AI quota.
Change it with the `CAREERLENS_RATE_LIMIT_PER_HOUR` environment variable on Render.

## 2. CareerLens frontend on Netlify

1. Netlify → **Add new project → Import an existing project → GitHub** → select `CareerLens-AI`.
   Do not use the drag-and-drop zone: it cannot build the app or run the Python backend.
2. Build settings are read from `netlify.toml`:

   | Field | Value |
   |---|---|
   | Base directory | `frontend` |
   | Build command | `npm run build` |
   | Publish directory | `frontend/dist` |

3. **Environment variables** → add `VITE_API_BASE_URL` = `https://careerlens-ai-z6xa.onrender.com` (no trailing `/`).
4. Deploy, copy the Netlify URL, and set it as `CAREERLENS_ALLOWED_ORIGINS` on Render (step 1).
5. New Netlify projects start **Private**. Click **Make public** on the project overview so others can open the site.

`VITE_` variables are compiled into the public JavaScript. Never put secrets in them.
If you change `VITE_API_BASE_URL`, trigger a new deploy: **Deploys → Trigger deploy → Deploy project**.

## 3. Troubleshooting

Open the live site, press **F12 → Console**, then match the error:

| Symptom | Cause and fix |
|---|---|
| Error mentions **CORS** | `CAREERLENS_ALLOWED_ORIGINS` on Render does not exactly match the Netlify URL (`https`, no trailing `/`). |
| Requests go to `127.0.0.1` | `VITE_API_BASE_URL` was missing at build time. Add it and redeploy on Netlify. |
| First analysis takes 30–60 s | The free Render instance was asleep. Normal after ~15 minutes idle. |
| Render build fails | Read the last lines of the Render deploy log. Check `PYTHON_VERSION` and the Root Directory. |

---

## 4. Reusable template: hosting any other backend on Render

### Give Render access to the new repository

Render was granted access to selected repositories only. For a new repo:

1. Render → **+ New → Web Service**.
2. Under the repository list, click **Configure GitHub** (opens GitHub's "Render" app settings).
3. **Only select repositories → Select repositories** → add the new repo → **Save**.
4. Back in Render, click **Connect** next to the repo.

### Fill in the form

| Field | What to enter | How to decide |
|---|---|---|
| Name | `<project>-api` | Becomes `<name>-xxxx.onrender.com` |
| Language | Python 3 / Node / Docker | Language of the backend |
| Branch | `main` | Branch you push to |
| Region | Singapore | Closest to your users |
| Root Directory | Folder containing `requirements.txt` or `package.json` | Blank if at repo root |
| Build Command | Installs dependencies | See table below |
| Start Command | Starts the server on `$PORT` | See table below |
| Instance Type | Free | Confirm it shows **$0 / month** |
| Environment Variables | `PYTHON_VERSION` / `NODE_VERSION`, API keys, allowed origins | Secrets go here, never in code |

### Build and start commands by framework

| Framework | Build Command | Start Command |
|---|---|---|
| FastAPI | `pip install -r requirements.txt` | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Flask | `pip install -r requirements.txt` (include `gunicorn`) | `gunicorn app:app` |
| Django | `pip install -r requirements.txt && python manage.py collectstatic --noinput` | `gunicorn <project>.wsgi` |
| Node / Express | `npm install` | `node server.js` or `npm start` |

In `app.main:app`, the part before the colon is the module path (`app/main.py` → `app.main`)
and the part after it is the variable holding the app (`app = FastAPI()`).

### Rules for every backend

1. Listen on `0.0.0.0` and the `$PORT` Render provides. A hard-coded port fails.
2. Read allowed frontend origins (CORS) from an environment variable.
3. Keep secrets in Render's **Environment** tab; locally, use a git-ignored `.env`.

### Free plan limits

- Free services sleep after ~15 minutes without traffic; the next request takes 30–60 s to wake them.
- All free services in a workspace share 750 instance hours per month.
- No persistent disk: files written on the server are lost on redeploy. Use a database (Supabase, Neon) for data.
