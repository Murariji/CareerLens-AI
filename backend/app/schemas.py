from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """Data submitted by the user from the frontend form."""

    resume: str = Field(min_length=30, max_length=20_000)
    job_description: str = Field(min_length=30, max_length=20_000)


class AnalysisResponse(BaseModel):
    """The structured response that the frontend can safely display."""

    is_demo: bool
    summary: str
    message: str
