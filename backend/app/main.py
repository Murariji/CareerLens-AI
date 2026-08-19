from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import AnalysisResponse
from app.services.pdf_extractor import extract_resume_from_pdf

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
async def analyze_career_fit(
    resume: Annotated[UploadFile, File(description="A resume PDF, 5 MB maximum")],
    job_description: Annotated[str, Form(min_length=30, max_length=20_000)],
) -> AnalysisResponse:
    """Extract a resume PDF and return a temporary non-AI analysis response.

    This is deliberately a demo response. In the next milestone, this function
    will call the AI service through a dedicated analyzer module.
    """

    if not resume.filename or not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload a PDF resume.",
        )

    resume_bytes = await resume.read()
    extracted_resume = extract_resume_from_pdf(resume_bytes)
    resume_words = len(extracted_resume.text.split())
    job_words = len(job_description.split())

    return AnalysisResponse(
        is_demo=True,
        summary="Your PDF resume was read securely by the backend.",
        message=(
            f"{resume.filename} contains about {resume_words} words and the job description "
            f"contains about {job_words} words. AI-powered analysis will be added next."
        ),
        resume_filename=resume.filename,
        extracted_links=extracted_resume.links,
    )
