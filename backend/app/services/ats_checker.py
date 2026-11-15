"""Rule-based ATS readiness checks.

There is no single official "ATS score": applicant tracking systems parse a
resume into fields and recruiters filter on keywords. These checks cover what
reliably helps parsing and keyword filtering, and each one explains how to fix it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.skill_matcher import MatchReport

SECTION_PATTERNS = {
    "Experience": r"\b(?:work\s+)?experience\b|\bemployment\b|\binternships?\b",
    "Education": r"\beducation\b|\bacademic\b",
    "Skills": r"\b(?:technical\s+)?skills\b",
    "Projects": r"\bprojects?\b",
}
ACTION_VERBS = (
    "built", "developed", "designed", "led", "implemented", "improved", "created", "deployed",
    "trained", "analyzed", "analysed", "automated", "optimized", "optimised", "reduced", "increased",
    "launched", "engineered", "architected", "delivered", "integrated", "migrated", "researched",
    "fine-tuned", "managed", "collaborated", "achieved", "streamlined", "evaluated",
)


@dataclass(frozen=True)
class ATSCheck:
    id: str
    label: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class ATSReport:
    score: int
    passed: int
    total: int
    checks: list[ATSCheck]


def run_ats_checks(resume_text: str, links: list[str], report: MatchReport) -> ATSReport:
    lower = resume_text.lower()
    words = len(resume_text.split())
    lines = [" ".join(line.split()) for line in resume_text.splitlines() if line.strip()]
    all_links = " ".join(links).lower() + " " + lower

    checks: list[ATSCheck] = []

    checks.append(ATSCheck(
        "readable", "Text is machine-readable", words >= 150,
        f"About {words} words were extracted." if words >= 150
        else f"Only about {words} words could be read. Use a text-based PDF, not a scan or an image-heavy design.",
    ))

    has_email = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", resume_text))
    has_phone = bool(re.search(r"(?:\+?\d[\d\s-]{8,}\d)", resume_text))
    checks.append(ATSCheck(
        "contact", "Email and phone number", has_email and has_phone,
        "Both found." if has_email and has_phone
        else "Add " + " and ".join(x for x, ok in (("an email", has_email), ("a phone number", has_phone)) if not ok) + " in plain text at the top.",
    ))

    has_linkedin = "linkedin.com" in all_links
    has_github = "github.com" in all_links or "gitlab.com" in all_links
    checks.append(ATSCheck(
        "profiles", "LinkedIn and GitHub/portfolio links", has_linkedin and has_github,
        "Both found." if has_linkedin and has_github
        else "Add " + " and ".join(x for x, ok in (("your LinkedIn URL", has_linkedin), ("a GitHub or portfolio link", has_github)) if not ok) + ". Recruiters check these for tech roles.",
    ))

    found_sections = [name for name, pattern in SECTION_PATTERNS.items() if re.search(pattern, lower)]
    missing_sections = [name for name in SECTION_PATTERNS if name not in found_sections]
    checks.append(ATSCheck(
        "sections", "Standard section headings", len(missing_sections) <= 1,
        "Found: " + ", ".join(found_sections) + "." if len(missing_sections) <= 1
        else "Missing or unusual headings: " + ", ".join(missing_sections) + ". Use plain headings ATS parsers recognise.",
    ))

    quantified = [line for line in lines if re.search(r"\d", line) and len(line.split()) >= 5 and not re.search(r"\b(?:19|20)\d{2}\b", line)]
    checks.append(ATSCheck(
        "metrics", "Results are quantified", len(quantified) >= 3,
        f"{len(quantified)} bullets include numbers." if len(quantified) >= 3
        else f"Only {len(quantified)} bullets include numbers. Where true, add accuracy, time saved, users, or data size.",
    ))

    verb_lines = [line for line in lines if re.match(r"^[\W\d]*(" + "|".join(ACTION_VERBS) + r")\b", line.lower())]
    checks.append(ATSCheck(
        "verbs", "Bullets start with action verbs", len(verb_lines) >= 4,
        f"{len(verb_lines)} bullets start with strong verbs." if len(verb_lines) >= 4
        else f"Only {len(verb_lines)} bullets start with action verbs like Built, Trained, Deployed, Improved.",
    ))

    good_length = 300 <= words <= 1100
    checks.append(ATSCheck(
        "length", "Length suits an early-career resume", good_length,
        "Length looks right (about 1-2 pages)." if good_length
        else ("Too short: add projects, coursework, or internships." if words < 300 else "Too long: trim to the most relevant 1-2 pages."),
    ))

    keyword_ratio = report.required_matched / report.required_total if report.required_total else 1.0
    checks.append(ATSCheck(
        "keywords", "Covers the job's required keywords", keyword_ratio >= 0.6,
        f"{report.required_matched} of {report.required_total} required skills appear in your resume." if report.required_total
        else "No catalogued required skills were detected in the job description.",
    ))

    passed = sum(check.passed for check in checks)
    return ATSReport(score=round(passed / len(checks) * 100), passed=passed, total=len(checks), checks=checks)
