# Security and privacy

## How CareerLens handles your data

- **Resumes are never stored.** The PDF is read in memory, analysed, and discarded when the request ends. There is no database of resumes.
- **The job description and resume text are sent to an AI provider only when AI mode is on** (Groq first, Gemini as a backup). Google may use inputs sent to the Gemini *free tier* to improve its products. The rule-based analysis never leaves the server.
- **The application tracker lives only in your browser** (`localStorage`). It is never sent to the server.
- **No accounts, no cookies, no tracking scripts.**

## Protections in place

| Risk | Protection |
|---|---|
| API keys leaking | Keys live only in the server's environment variables (Render). They are never in the repository, the frontend bundle, or API responses. `.env` files are git-ignored. |
| Someone draining the free AI quota | Per-visitor rate limit on `/api/analyze` (default 20 analyses per hour, set with `CAREERLENS_RATE_LIMIT_PER_HOUR`). |
| Oversized or malicious uploads | PDF-only, 5 MB cap enforced while reading, file signature check, password-protected and malformed PDFs rejected with a clear message. Links inside the PDF are extracted as text and never opened. |
| Prompt injection inside a resume or job post | Uploaded text is passed to the model as data inside tags, with instructions to ignore any commands in it. Every AI claim is then verified against the original text, and unverifiable claims are dropped. |
| AI inventing qualifications | Strengths and gaps must quote the documents word-for-word; bullet rewrites that add skills or numbers not in the original bullet are rejected. |
| Cross-site requests | CORS allows only the official frontend origin (`CAREERLENS_ALLOWED_ORIGINS`). |

## Reporting a vulnerability

Please **do not open a public issue** for security problems. Use GitHub's private reporting instead:
**Security** tab of this repository → **Report a vulnerability**.

Include what you found, how to reproduce it, and the impact. You'll get a reply as soon as possible.
