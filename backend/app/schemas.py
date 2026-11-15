from typing import Literal

from pydantic import BaseModel, Field


class ApplicationPlanResponse(BaseModel):
    readiness: Literal["ready_to_apply", "apply_after_updates", "build_evidence_first"]
    headline: str
    reason: str
    next_actions: list[str] = Field(default_factory=list)


class EvidencedStrength(BaseModel):
    skill: str = Field(description="A skill or qualification the job asks for that the resume demonstrates.")
    resume_evidence: str = Field(
        description="A short phrase copied word-for-word from the resume that proves this strength."
    )


class SkillGap(BaseModel):
    skill: str = Field(description="A requirement from the job description that the resume does not demonstrate.")
    job_requirement: str = Field(
        description="A short phrase copied word-for-word from the job description that states this requirement."
    )
    how_to_close: str = Field(description="One honest, concrete step to build or show this skill.")


class InterviewQuestion(BaseModel):
    question: str = Field(description="A question an interviewer for this role is likely to ask this candidate.")
    why_asked: str = Field(description="Why this question matters, tied to the resume or job description.")


class AIAnalysisResponse(BaseModel):
    """Grounded LLM analysis after CareerLens has verified every quoted piece of evidence."""

    model: str
    fit_summary: str
    strengths: list[EvidencedStrength] = Field(default_factory=list)
    gaps: list[SkillGap] = Field(default_factory=list)
    resume_suggestions: list[str] = Field(default_factory=list)
    interview_questions: list[InterviewQuestion] = Field(default_factory=list)
    removed_unsupported_items: int = Field(
        default=0,
        ge=0,
        description="How many AI claims were dropped because their quoted evidence was not found in the supplied text.",
    )


class AnalysisResponse(BaseModel):
    """The structured response that the frontend can safely display."""

    is_demo: bool
    analysis_source: Literal["baseline", "ai"] = "baseline"
    ai_analysis: AIAnalysisResponse | None = None
    ai_notice: str | None = None
    summary: str
    message: str
    resume_filename: str
    extracted_links: list[str] = Field(default_factory=list)
    match_score: int = Field(ge=0, le=100)
    matching_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    resume_suggestions: list[str] = Field(default_factory=list)
    target_role: str
    location: str | None = None
    application_plan: ApplicationPlanResponse
