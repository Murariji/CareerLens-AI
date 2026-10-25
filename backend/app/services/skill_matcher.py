"""Transparent, deterministic resume-to-job skill matching.

This is intentionally a baseline rather than an LLM. Every item in the result
is traceable to text supplied by the user, making it useful for testing and for
comparison with a later grounded LLM analysis.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


SKILL_PATTERNS: dict[str, tuple[str, ...]] = {
    "Python": (r"\bpython\b",),
    "SQL": (r"\bsql\b", r"\bmysql\b", r"\bpostgres(?:ql)?\b"),
    "Excel": (r"\bexcel\b", r"\bms excel\b"),
    "Power BI": (r"\bpower\s*bi\b",),
    "Tableau": (r"\btableau\b",),
    "Java": (r"\bjava\b",),
    "JavaScript": (r"\bjavascript\b", r"\bjs\b"),
    "TypeScript": (r"\btypescript\b", r"\bts\b"),
    "React": (r"\breact(?:\.js)?\b",),
    "Node.js": (r"\bnode(?:\.js)?\b",),
    "HTML/CSS": (r"\bhtml\b", r"\bcss\b"),
    "Git": (r"\bgit(?:hub)?\b",),
    "Docker": (r"\bdocker\b",),
    "AWS": (r"\baws\b", r"\bamazon web services\b"),
    "Azure": (r"\bazure\b",),
    "Machine Learning": (r"\bmachine learning\b", r"\bml\b"),
    "Data Analysis": (r"\bdata[\s-]+analys(?:is|t|tics)\b",),
    "Pandas": (r"\bpandas\b",),
    "NumPy": (r"\bnumpy\b",),
    "FastAPI": (r"\bfastapi\b",),
    "REST APIs": (r"\brest(?:ful)?\s+api(?:s)?\b", r"\bapi integration\b"),
    "Agile": (r"\bagile\b", r"\bscrum\b"),
}

STOP_WORDS = {
    "about", "across", "and", "are", "for", "from", "have", "into", "job",
    "looking", "role", "that", "the", "this", "with", "will", "you", "your",
    "years", "work", "team", "ability", "experience", "skills", "required",
}


@dataclass(frozen=True)
class MatchReport:
    match_score: int
    matching_skills: list[str]
    missing_skills: list[str]
    resume_skills: list[str]
    suggestions: list[str]


def _find_skills(text: str) -> set[str]:
    lower_text = text.lower()
    return {
        skill
        for skill, patterns in SKILL_PATTERNS.items()
        if any(re.search(pattern, lower_text) for pattern in patterns)
    }


def _meaningful_terms(text: str) -> set[str]:
    return {
        term
        for term in re.findall(r"[a-zA-Z][a-zA-Z+#.-]{2,}", text.lower())
        if term not in STOP_WORDS
    }


def _build_suggestions(missing_skills: list[str], resume_text: str) -> list[str]:
    suggestions: list[str] = []

    for skill in missing_skills[:3]:
        suggestions.append(
            f"If you have used {skill}, add one specific project or achievement that proves it; otherwise, do not claim it."
        )

    if not re.search(r"\d|%", resume_text):
        suggestions.append("Add measurable outcomes to relevant bullet points, such as time saved, accuracy improved, or project scale.")

    if not suggestions:
        suggestions.append("Prioritize the matching skills near the top of your resume and support each with a project, outcome, or work example.")

    return suggestions[:4]


def build_match_report(resume_text: str, job_description: str) -> MatchReport:
    """Build a reproducible fit report from supplied resume and job text."""

    resume_skills = _find_skills(resume_text)
    job_skills = _find_skills(job_description)
    matching_skills = sorted(resume_skills & job_skills)
    missing_skills = sorted(job_skills - resume_skills)

    job_terms = _meaningful_terms(job_description)
    resume_terms = _meaningful_terms(resume_text)
    term_coverage = len(job_terms & resume_terms) / len(job_terms) if job_terms else 0

    if job_skills:
        skill_coverage = len(matching_skills) / len(job_skills)
        score = round((skill_coverage * 80) + (term_coverage * 20))
    else:
        score = round(term_coverage * 100)

    return MatchReport(
        match_score=max(0, min(score, 100)),
        matching_skills=matching_skills,
        missing_skills=missing_skills,
        resume_skills=sorted(resume_skills),
        suggestions=_build_suggestions(missing_skills, resume_text),
    )
