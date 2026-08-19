# CareerLens AI: Project Map

This document explains where each kind of work belongs. It is the map you can use while building and explaining the project in an interview.

## Folder responsibilities

| Location | What belongs here | Why it exists |
| --- | --- | --- |
| `frontend/` | Pages, buttons, forms, styling, and API calls | Everything the user sees and clicks lives here. |
| `backend/` | API routes, AI prompts, validation, and business logic | It protects the API key and decides how the application processes data. |
| `docs/` | Architecture, decisions, setup notes, and diagrams | It makes the project understandable to recruiters and future contributors. |
| `tests/` | Automated checks and sample cases | It proves that the application continues to work after changes. |
| `README.md` | Project overview and setup instructions | It is the first page people see on GitHub. |
| `.gitignore` | Files Git must not upload | It prevents secrets, temporary files, and personal uploads from reaching GitHub. |

## Backend files we will add

| File | Responsibility |
| --- | --- |
| `backend/app/main.py` | Starts FastAPI and exposes API endpoints. |
| `backend/app/schemas.py` | Defines the shape of incoming data and AI results. |
| `backend/app/services/analyzer.py` | Builds the AI request and converts its answer into a useful analysis. |
| `backend/app/core/config.py` | Reads safe configuration, such as an API key, from a local `.env` file. |
| `backend/requirements.txt` | Lists the Python packages needed to run the backend. |

## Frontend files we will add

| File | Responsibility |
| --- | --- |
| `frontend/src/App.tsx` | Main page and application flow. |
| `frontend/src/components/AnalysisForm.tsx` | Text areas and the Analyze button. |
| `frontend/src/components/AnalysisResult.tsx` | Presents the AI analysis clearly. |
| `frontend/src/api/client.ts` | Sends the frontend's request to the backend. |
| `frontend/src/styles.css` | Defines the visual styling and responsive layout. |

## One request, step by step

1. The user pastes their resume and a job description into the frontend form.
2. The frontend sends both texts to the backend's `/api/analyze` endpoint.
3. The backend validates that neither text is empty or excessively long.
4. The analyzer sends clear instructions and the validated texts to the AI model.
5. The model returns structured data rather than an unstructured paragraph.
6. The backend validates the structure and sends it to the frontend.
7. The frontend renders the analysis for the user.

## Interview explanation

> CareerLens AI uses a React frontend for user interaction and a FastAPI backend to securely orchestrate the LLM call. The backend validates input and requires structured output. The prompt includes a grounding rule: every recommendation must be supported by the supplied resume or job description, and it must never fabricate experience.
