from dataclasses import dataclass

import pymupdf
from fastapi import HTTPException, status

MAX_RESUME_BYTES = 5 * 1024 * 1024


@dataclass
class ExtractedResume:
    text: str
    links: list[str]


def extract_resume_from_pdf(file_bytes: bytes) -> ExtractedResume:
    """Extract text and HTTP(S) links from a PDF held only in memory."""

    if len(file_bytes) > MAX_RESUME_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Resume PDF must be 5 MB or smaller.",
        )

    if not file_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is not a valid PDF.",
        )

    try:
        document = pymupdf.open(stream=file_bytes, filetype="pdf")
    except (pymupdf.FileDataError, RuntimeError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CareerLens could not read this PDF.",
        ) from error

    try:
        pages = [page.get_text("text", sort=True) for page in document]
        links = [
            link["uri"]
            for page in document
            for link in page.get_links()
            if isinstance(link.get("uri"), str) and link["uri"].startswith(("http://", "https://"))
        ]
    finally:
        document.close()

    text = "\n".join(pages).strip()
    if len(text) < 30:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No readable resume text was found. Upload a text-based PDF, not a scanned image.",
        )

    return ExtractedResume(text=text, links=list(dict.fromkeys(links)))
