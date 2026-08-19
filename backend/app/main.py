from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import AnalysisRequest, AnalysisResponse

app = FastAPI(
    title="CareerLens AI API",
    description="Evidence-grounded career analysis API.",
    version="0.1.0",
)

# During development, the React app runs on a different local address.
# CORS explicitly permits that address to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    """A small endpoint used to confirm the server is running."""

    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalysisResponse)
def analyze_career_fit(request: AnalysisRequest) -> AnalysisResponse:
    """Validate user input and return a temporary non-AI analysis response.

    This is deliberately a demo response. In the next milestone, this function
    will call the AI service through a dedicated analyzer module.
    """

    resume_words = len(request.resume.split())
    job_words = len(request.job_description.split())

    return AnalysisResponse(
        is_demo=True,
        summary="Your resume and job description were received securely by the backend.",
        message=(
            f"The resume contains about {resume_words} words and the job description "
            f"contains about {job_words} words. AI-powered analysis will be added next."
        ),
    )
