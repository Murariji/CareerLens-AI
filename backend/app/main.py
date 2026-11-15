import os
from typing import Annotated

from dotenv import load_dotenv

# Read backend/.env (if present) before anything looks at environment variables.
load_dotenv()

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import AnalysisResponse, ApplicationPlanResponse
from app.services.llm_analyzer import analyze_with_llm
from app.services.pdf_extractor import extract_resume_from_pdf
from app.services.skill_matcher import build_application_plan, build_match_report

app = FastAPI(
    title="CareerLens AI API",
    description="Evidence-grounded career analysis API.",
    version="0.1.0",
)

# The React app runs on a different address from this API, so CORS must allow it.
# Locally that is the Vite dev server; in production, set CAREERLENS_ALLOWED_ORIGINS
# to your Netlify URL (comma-separate several, no trailing slash).
ALLOWED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.environ.get("CAREERLENS_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
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
    target_role: Annotated[str, Form(min_length=2, max_length=100)],
    location: Annotated[str | None, Form(max_length=100)] = None,
) -> AnalysisResponse:
    """Extract a resume PDF, build the transparent baseline, and add a grounded AI analysis.

    The AI step is optional: without an API key, or if the call fails, the
    response contains the baseline report and an `ai_notice` explaining why.
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
    report = build_match_report(extracted_resume.text, job_description)
    plan = build_application_plan(report, target_role)
    llm_result = await analyze_with_llm(extracted_resume.text, job_description, target_role, report)
    ai_analysis = llm_result.analysis

    if ai_analysis:
        message = (
            "AI analysis is grounded in your resume and this job description. Every strength and gap "
            "quotes the text it came from, and the evidence match score is the transparent baseline."
        )
    else:
        message = (
            f"{resume.filename} contains about {resume_words} words and the job description "
            f"contains about {job_words} words. This is an explainable baseline, not an AI-generated claim."
        )

    return AnalysisResponse(
        is_demo=ai_analysis is None,
        analysis_source="ai" if ai_analysis else "baseline",
        ai_analysis=ai_analysis,
        ai_notice=llm_result.notice,
        summary=f"Your current evidence match is {report.match_score}%.",
        message=message,
        resume_filename=resume.filename,
        extracted_links=extracted_resume.links,
        match_score=report.match_score,
        matching_skills=report.matching_skills,
        missing_skills=report.missing_skills,
        resume_suggestions=report.suggestions,
        target_role=target_role,
        location=location.strip() if location else None,
        application_plan=ApplicationPlanResponse(
            readiness=plan.readiness,
            headline=plan.headline,
            reason=plan.reason,
            next_actions=plan.next_actions,
        ),
    )
