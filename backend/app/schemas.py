from pydantic import BaseModel, Field


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
