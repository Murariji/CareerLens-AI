import os
from typing import Annotated, Any, Literal

from dotenv import load_dotenv

# Read backend/.env (if present) before anything looks at environment variables.
load_dotenv()

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    AnalysisResponse,
    ApplicationPlanResponse,
    ATSCheckResponse,
    ATSReportResponse,
    CategoryCoverageResponse,
    GapResponse,
    SkillEvidenceResponse,
    TextSegmentResponse,
)
from app.services.ats_checker import run_ats_checks
from app.services.llm_analyzer import analyze_with_llm, resolve_providers
from app.services.pdf_extractor import MAX_RESUME_BYTES, extract_resume_from_pdf
from app.services.rate_limit import client_ip, enforce_analysis_limit, enforce_report_limit
from app.services.report_export import build_doc, build_markdown, build_pdf, report_filename
from app.services.skill_matcher import build_application_plan, build_match_report
from app.services.stats import StatsEvent, role_category, stats_service

app = FastAPI(
    title="CareerLens AI API",
    description="Evidence-grounded career analysis API.",
    version="0.2.0",
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
    expose_headers=["Content-Disposition"],
)


@app.api_route("/", methods=["GET", "HEAD"])
def root() -> dict[str, str]:
    """A friendly landing response so visiting the bare API URL isn't a 404."""

    return {
        "name": "CareerLens AI API",
        "status": "ok",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.api_route("/api/health", methods=["GET", "HEAD"])
def health_check(request: Request, background_tasks: BackgroundTasks, visit: bool = False) -> dict[str, str | bool | None]:
    """Confirms the server is running. The frontend calls it with ?visit=1 on page load,
    which both wakes the free server early and counts an anonymous visit."""

    if visit:
        visitor = stats_service.visitor_hash(client_ip(request), request.headers.get("user-agent", ""))
        background_tasks.add_task(stats_service.record, StatsEvent(kind="visit", visitor=visitor))
    providers = [name for name, _, _ in resolve_providers()]
    return {"status": "ok", "ai_enabled": bool(providers), "ai_provider": " + ".join(providers) or None}


@app.get("/api/stats")
async def usage_stats() -> dict[str, Any]:
    """Anonymous usage totals: visits, unique visitors, analyses, role categories, last 30 days."""

    return await stats_service.summary()


REPORT_FORMATS = {
    "pdf": ("application/pdf", "pdf"),
    "doc": ("application/msword", "doc"),
    "md": ("text/markdown; charset=utf-8", "md"),
}


@app.post("/api/report/{fmt}", dependencies=[Depends(enforce_report_limit)])
def download_report(fmt: Literal["pdf", "doc", "md"], report: AnalysisResponse) -> Response:
    """Turn an analysis (as returned by /api/analyze) into a PDF, Word or Markdown file. Nothing is stored."""

    if fmt == "pdf":
        content = build_pdf(report)
    elif fmt == "doc":
        content = build_doc(report)
    else:
        content = build_markdown(report).encode("utf-8")
    media_type, extension = REPORT_FORMATS[fmt]
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{report_filename(report, extension)}"'},
    )


@app.post("/api/analyze", response_model=AnalysisResponse, dependencies=[Depends(enforce_analysis_limit)])
async def analyze_career_fit(
    background_tasks: BackgroundTasks,
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

    # Read at most one byte over the limit so an oversized upload is rejected without loading it all.
    resume_bytes = await resume.read(MAX_RESUME_BYTES + 1)
    extracted_resume = extract_resume_from_pdf(resume_bytes)
    report = build_match_report(extracted_resume.text, job_description)
    plan = build_application_plan(report, target_role)
    ats = run_ats_checks(extracted_resume.text, extracted_resume.links, report)
    llm_result = await analyze_with_llm(extracted_resume.text, job_description, target_role, report)
    ai_analysis = llm_result.analysis
    background_tasks.add_task(
        stats_service.record,
        StatsEvent(kind="analysis", role_category=role_category(target_role), score=report.match_score, ai=ai_analysis is not None),
    )

    if report.match_score >= 70:
        verdict = "Strong fit"
    elif report.match_score >= 45:
        verdict = "Partial fit"
    else:
        verdict = "Early fit"
    if report.required_total:
        summary = f"{verdict}: {report.required_matched} of {report.required_total} required skills are evidenced in your resume."
    else:
        summary = f"{verdict}: no catalogued skills were detected in this job description, so the score uses keyword overlap."

    message = ai_analysis.fit_summary if ai_analysis else (
        "Rule-based analysis: every skill below is traced to text in your resume or the job description."
    )

    return AnalysisResponse(
        is_demo=ai_analysis is None,
        analysis_source="ai" if ai_analysis else "baseline",
        ai_analysis=ai_analysis,
        ai_notice=llm_result.notice,
        summary=summary,
        message=message,
        resume_filename=resume.filename,
        extracted_links=extracted_resume.links,
        match_score=report.match_score,
        required_matched=report.required_matched,
        required_total=report.required_total,
        bonus_matched=report.bonus_matched,
        bonus_total=report.bonus_total,
        matching_skills=report.matching_skills,
        missing_skills=report.missing_skills,
        skill_evidence=[SkillEvidenceResponse(**vars(item)) for item in report.skill_evidence],
        gaps=[GapResponse(**vars(item)) for item in report.gaps],
        category_coverage=[CategoryCoverageResponse(**vars(item)) for item in report.category_coverage],
        term_coverage=report.term_coverage,
        job_segments=[TextSegmentResponse(**vars(item)) for item in report.job_segments],
        resume_suggestions=report.suggestions,
        ats=ATSReportResponse(
            score=ats.score,
            passed=ats.passed,
            total=ats.total,
            checks=[ATSCheckResponse(**vars(check)) for check in ats.checks],
        ),
        target_role=target_role,
        location=location.strip() if location else None,
        application_plan=ApplicationPlanResponse(
            readiness=plan.readiness,
            headline=plan.headline,
            reason=plan.reason,
            next_actions=plan.next_actions,
        ),
    )
