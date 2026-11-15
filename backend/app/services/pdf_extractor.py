import logging
from dataclasses import dataclass

import pymupdf
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

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

    unreadable = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="CareerLens could not read this PDF. Try exporting it again as a standard PDF (e.g. 'Save as PDF' from Word or Google Docs).",
    )

    try:
        document = pymupdf.open(stream=file_bytes, filetype="pdf")
    except Exception as error:  # Malformed, encrypted, or unusual PDFs raise varied pymupdf errors.
        logger.warning("Could not open uploaded PDF: %s", error)
        raise unreadable from error

    try:
        if document.needs_pass:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This PDF is password-protected. Please upload a version without a password.",
            )
        pages = [page.get_text("text", sort=True) for page in document]
        links = [
            link["uri"]
            for page in document
            for link in page.get_links()
            if isinstance(link.get("uri"), str) and link["uri"].startswith(("http://", "https://"))
        ]
    except HTTPException:
        raise
    except Exception as error:
        # An unhandled error would become a 500 without CORS headers, which the browser
        # reports only as "Failed to fetch". Return a clear 400 instead.
        logger.warning("Could not extract text from uploaded PDF: %s", error)
        raise unreadable from error
    finally:
        document.close()

    text = "\n".join(pages).strip()
    if len(text) < 30:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No readable resume text was found. Upload a text-based PDF, not a scanned image.",
        )

    return ExtractedResume(text=text, links=list(dict.fromkeys(links)))
