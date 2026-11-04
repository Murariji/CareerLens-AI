from typing import Literal

from pydantic import BaseModel, Field


class ApplicationPlanResponse(BaseModel):
    readiness: Literal["ready_to_apply", "apply_after_updates", "build_evidence_first"]
    headline: str
    reason: str
    next_actions: list[str] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    """The structured response that the frontend can safely display."""

    is_demo: bool
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
