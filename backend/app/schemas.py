from pydantic import BaseModel, Field


class AnalysisResponse(BaseModel):
    """The structured response that the frontend can safely display."""

    is_demo: bool
    summary: str
    message: str
    resume_filename: str
    extracted_links: list[str] = Field(default_factory=list)
