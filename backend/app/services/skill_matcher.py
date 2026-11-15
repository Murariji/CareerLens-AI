"""Transparent, deterministic resume-to-job skill matching.

This is intentionally a baseline rather than an LLM. Every item in the result
is traceable to text supplied by the user, making it useful for testing and for
comparison with the grounded LLM analysis.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SkillSpec:
    category: str
    patterns: tuple[str, ...]
    project_idea: str


PROGRAMMING = "Programming"
ML_AI = "ML & AI"
DATA = "Data"
CLOUD = "Cloud & MLOps"
WEB = "Web & APIs"
PRACTICES = "Tools & practices"

SKILLS: dict[str, SkillSpec] = {
    # Programming
    "Python": SkillSpec(PROGRAMMING, (r"\bpython\b",), "Ship a small Python CLI or script that automates a real task and publish it on GitHub with a README."),
    "Java": SkillSpec(PROGRAMMING, (r"\bjava\b",), "Build a small Java REST service (Spring Boot) with tests and link it on your resume."),
    "JavaScript": SkillSpec(PROGRAMMING, (r"\bjavascript\b", r"\bjs\b"), "Build an interactive web page in JavaScript and deploy it free on Netlify."),
    "TypeScript": SkillSpec(PROGRAMMING, (r"\btypescript\b",), "Convert a small JavaScript project to TypeScript and note what bugs the types caught."),
    "C++": SkillSpec(PROGRAMMING, (r"\bc\+\+", r"\bcpp\b"), "Solve 20 data-structure problems in C++ and publish the repo with complexity notes."),
    "SQL": SkillSpec(PROGRAMMING, (r"\bsql\b", r"\bmysql\b", r"\bpostgres(?:ql)?\b", r"\bsqlite\b"), "Load a public dataset into PostgreSQL and write 10 analysis queries (joins, window functions) in a repo."),
    # ML & AI
    "Machine Learning": SkillSpec(ML_AI, (r"\bmachine learning\b", r"\bml\b"), "Train and evaluate a model on a Kaggle dataset; report baseline vs final metrics in the README."),
    "Deep Learning": SkillSpec(ML_AI, (r"\bdeep learning\b", r"\bneural networks?\b", r"\bcnns?\b", r"\brnns?\b", r"\blstms?\b"), "Train a small neural network (e.g. image classifier) and document accuracy, loss curves and what you tuned."),
    "PyTorch": SkillSpec(ML_AI, (r"\bpytorch\b", r"\btorch\b"), "Re-implement a simple model in PyTorch (training loop, evaluation) and push it with results."),
    "TensorFlow": SkillSpec(ML_AI, (r"\btensorflow\b", r"\bkeras\b"), "Build and train a Keras/TensorFlow model and export it for inference."),
    "scikit-learn": SkillSpec(ML_AI, (r"\bscikit[\s-]?learn\b", r"\bsklearn\b"), "Build a scikit-learn pipeline (preprocessing + model + cross-validation) on a tabular dataset."),
    "NLP": SkillSpec(ML_AI, (r"\bnlp\b", r"\bnatural language processing\b", r"\btext classification\b", r"\bsentiment analysis\b"), "Fine-tune a small text classifier (e.g. sentiment) and report precision/recall."),
    "Computer Vision": SkillSpec(ML_AI, (r"\bcomputer vision\b", r"\bopencv\b", r"\bimage (?:classification|segmentation|detection)\b", r"\bobject detection\b", r"\byolo\b"), "Build an image classifier or object detector on a public dataset and show sample predictions."),
    "LLMs": SkillSpec(ML_AI, (r"\bllms?\b", r"\blarge language models?\b", r"\bgpt\b", r"\bgenerative ai\b", r"\bgen\s?ai\b"), "Build a small LLM app (e.g. document Q&A) with a free API and describe how you evaluated answers."),
    "RAG": SkillSpec(ML_AI, (r"\brag\b", r"\bretrieval[\s-]augmented\b"), "Build a RAG chatbot over your college notes or docs, with citations to the source chunks."),
    "Prompt Engineering": SkillSpec(ML_AI, (r"\bprompt engineering\b", r"\bprompting\b"), "Compare 3 prompt versions on 20 test inputs and document which worked best and why."),
    "Hugging Face": SkillSpec(ML_AI, (r"\bhugging\s?face\b", r"\btransformers library\b"), "Fine-tune or deploy a Hugging Face model and publish it as a free Hugging Face Space."),
    "LangChain": SkillSpec(ML_AI, (r"\blangchain\b", r"\blanggraph\b", r"\bllamaindex\b"), "Build a small LangChain or LlamaIndex pipeline (retriever + LLM) and explain each step in the README."),
    "Vector Databases": SkillSpec(ML_AI, (r"\bvector (?:databases?|db|stores?)\b", r"\bpinecone\b", r"\bfaiss\b", r"\bchroma(?:db)?\b", r"\bweaviate\b", r"\bqdrant\b", r"\bpgvector\b"), "Index 1,000 documents in FAISS or Chroma and build semantic search with a simple UI."),
    "Statistics": SkillSpec(ML_AI, (r"\bstatistic(?:s|al)\b", r"\bhypothesis testing\b", r"\bprobability\b", r"\ba/b test(?:ing)?\b"), "Run an A/B-test style analysis on a public dataset and explain p-values and confidence intervals."),
    # Data
    "Data Analysis": SkillSpec(DATA, (r"\bdata[\s-]+analys(?:is|t|ts|tics)\b", r"\bexploratory data analysis\b", r"\beda\b"), "Publish an exploratory analysis notebook with 3 clear, data-backed findings."),
    "Pandas": SkillSpec(DATA, (r"\bpandas\b",), "Clean a messy real-world CSV with Pandas and document each transformation."),
    "NumPy": SkillSpec(DATA, (r"\bnumpy\b",), "Implement a small algorithm (e.g. linear regression) from scratch with NumPy."),
    "Excel": SkillSpec(DATA, (r"\bexcel\b",), "Build an Excel dashboard with pivot tables and lookups from a public dataset."),
    "Power BI": SkillSpec(DATA, (r"\bpower\s*bi\b",), "Build a Power BI dashboard from a public dataset and share screenshots in your portfolio."),
    "Tableau": SkillSpec(DATA, (r"\btableau\b",), "Publish a dashboard on Tableau Public (free) and link it on your resume."),
    "Data Visualization": SkillSpec(DATA, (r"\bdata visuali[sz]ation\b", r"\bmatplotlib\b", r"\bseaborn\b", r"\bplotly\b"), "Create 5 clear charts telling one story from a dataset and publish them."),
    "Spark": SkillSpec(DATA, (r"\bspark\b", r"\bpyspark\b"), "Process a large public dataset with PySpark (free Databricks Community Edition) and compare it with Pandas."),
    "Airflow": SkillSpec(DATA, (r"\bairflow\b",), "Schedule a small daily data pipeline with Airflow running locally in Docker."),
    "MongoDB": SkillSpec(DATA, (r"\bmongo(?:db)?\b",), "Build a small API backed by MongoDB Atlas free tier."),
    # Cloud & MLOps
    "Docker": SkillSpec(CLOUD, (r"\bdocker\b", r"\bcontaineri[sz](?:ed|ation)\b"), "Dockerize one of your projects and add the Dockerfile and run instructions to the repo."),
    "Kubernetes": SkillSpec(CLOUD, (r"\bkubernetes\b", r"\bk8s\b"), "Deploy a containerized app on a local Kubernetes cluster (kind or minikube) and document it."),
    "AWS": SkillSpec(CLOUD, (r"\baws\b", r"\bamazon web services\b", r"\bsagemaker\b", r"\bec2\b", r"\bs3\b", r"\blambda\b"), "Deploy a small API or model on the AWS free tier (e.g. Lambda or EC2) and note the architecture."),
    "Azure": SkillSpec(CLOUD, (r"\bazure\b",), "Deploy a small app on Azure (student credits) and describe the services used."),
    "GCP": SkillSpec(CLOUD, (r"\bgcp\b", r"\bgoogle cloud\b", r"\bvertex ai\b", r"\bbigquery\b"), "Run an analysis in BigQuery's free sandbox or deploy to Cloud Run, then document it."),
    "MLOps": SkillSpec(CLOUD, (r"\bmlops\b", r"\bmlflow\b", r"\bmodel (?:deployment|monitoring|serving)\b", r"\bexperiment tracking\b"), "Track experiments with MLflow and serve the best model behind an API."),
    "CI/CD": SkillSpec(CLOUD, (r"\bci/cd\b", r"\bgithub actions\b", r"\bcontinuous integration\b", r"\bjenkins\b"), "Add a GitHub Actions workflow that runs tests on every push to one of your projects."),
    "Linux": SkillSpec(CLOUD, (r"\blinux\b", r"\bbash\b", r"\bshell scripting\b"), "Automate a routine task with a Bash script and explain it in your repo."),
    # Web & APIs
    "FastAPI": SkillSpec(WEB, (r"\bfastapi\b",), "Expose a model or dataset through a FastAPI service with auto-generated docs, deployed free on Render."),
    "Flask": SkillSpec(WEB, (r"\bflask\b",), "Build a small Flask app with a database and deploy it free."),
    "Django": SkillSpec(WEB, (r"\bdjango\b",), "Build a Django app with authentication and an admin panel."),
    "REST APIs": SkillSpec(WEB, (r"\brest(?:ful)?\s*apis?\b", r"\bapi integration\b", r"\bapi development\b"), "Build and document a REST API with at least 4 endpoints and tests."),
    "React": SkillSpec(WEB, (r"\breact(?:\.js|js)?\b",), "Build a React front end for one of your APIs and deploy it on Netlify."),
    "Node.js": SkillSpec(WEB, (r"\bnode(?:\.js|js)?\b", r"\bexpress(?:\.js)?\b"), "Build a Node.js/Express API with validation and deploy it."),
    "HTML/CSS": SkillSpec(WEB, (r"\bhtml5?\b", r"\bcss3?\b"), "Build a responsive personal portfolio page from scratch."),
    # Tools & practices
    "Git": SkillSpec(PRACTICES, (r"\bgit\b", r"\bgithub\b", r"\bgitlab\b", r"\bversion control\b"), "Keep your projects on GitHub with clear commits, branches and READMEs."),
    "Agile": SkillSpec(PRACTICES, (r"\bagile\b", r"\bscrum\b", r"\bkanban\b", r"\bjira\b"), "Run a team or solo project in 1-week sprints on a free Jira or GitHub Projects board."),
    "Testing": SkillSpec(PRACTICES, (r"\bunit tests?\b", r"\bunit testing\b", r"\bpytest\b", r"\bjest\b", r"\btest[\s-]driven\b"), "Add unit tests with coverage reporting to one of your projects."),
}

# Evidence for a specific skill also proves the broader one (e.g. a PyTorch project is ML work).
IMPLIED_BY: dict[str, tuple[str, ...]] = {
    "Machine Learning": ("Deep Learning", "PyTorch", "TensorFlow", "scikit-learn", "NLP", "Computer Vision", "MLOps"),
    "Deep Learning": ("PyTorch", "TensorFlow"),
    "REST APIs": ("FastAPI", "Flask", "Django", "Node.js"),
    "LLMs": ("RAG", "LangChain", "Prompt Engineering"),
    "Data Analysis": ("Pandas",),
}
ALTERNATIVE_SEPARATOR = re.compile(r"^[\s,/(]*(?:or|and/or|/|either)[\s,/(]*$")

STOP_WORDS = {
    "about", "across", "and", "are", "for", "from", "have", "into", "job",
    "looking", "role", "that", "the", "this", "with", "will", "you", "your",
    "years", "work", "team", "ability", "experience", "skills", "required",
    "our", "their", "they", "who", "what", "such", "using", "use", "strong",
    "good", "plus", "must", "should", "can", "all", "any", "including",
}

BONUS_HEADING = re.compile(r"\b(?:good|nice)[\s-]to[\s-]have\b|\bpreferred\b|\bbonus\b|\bdesirable\b|\boptional\b|\bplus points?\b|\ba plus\b|\bbonus points?\b")
REQUIRED_HEADING = re.compile(r"\brequirements?\b|\bresponsibilit(?:y|ies)\b|\bqualifications?\b|\bmust[\s-]have\b|\bwhat you(?:'|’)?ll do\b|\babout the role\b")
SKILLS_LIST_LINE = re.compile(r"^(?:[^,]+,){3,}")


@dataclass(frozen=True)
class SkillEvidence:
    skill: str
    category: str
    evidence: str
    demonstrated: bool


@dataclass(frozen=True)
class GapDetail:
    skill: str
    category: str
    required: bool
    project_idea: str


@dataclass(frozen=True)
class CategoryCoverage:
    category: str
    matched: int
    total: int


@dataclass(frozen=True)
class MatchReport:
    match_score: int
    matching_skills: list[str]
    missing_skills: list[str]
    resume_skills: list[str]
    suggestions: list[str]
    required_matched: int = 0
    required_total: int = 0
    bonus_matched: int = 0
    bonus_total: int = 0
    skill_evidence: list[SkillEvidence] = field(default_factory=list)
    gaps: list[GapDetail] = field(default_factory=list)
    category_coverage: list[CategoryCoverage] = field(default_factory=list)


@dataclass(frozen=True)
class ApplicationPlan:
    readiness: str
    headline: str
    reason: str
    next_actions: list[str]


def find_skills(text: str) -> set[str]:
    lower_text = text.lower()
    return {
        skill
        for skill, spec in SKILLS.items()
        if any(re.search(pattern, lower_text) for pattern in spec.patterns)
    }


def _with_implied(skills: set[str]) -> dict[str, str | None]:
    """Map each evidenced skill to None (direct) or to the specific skill that implies it."""

    result: dict[str, str | None] = {skill: None for skill in skills}
    for broad, specifics in IMPLIED_BY.items():
        if broad not in result:
            source = next((s for s in specifics if s in skills), None)
            if source:
                result[broad] = source
    return result


def _alternative_groups(text: str) -> list[set[str]]:
    """Find skills offered as alternatives, e.g. "PyTorch or TensorFlow", "AWS/Azure"."""

    groups: list[set[str]] = []
    for line in text.lower().splitlines():
        hits: list[tuple[int, int, str]] = []
        for skill, spec in SKILLS.items():
            for pattern in spec.patterns:
                match = re.search(pattern, line)
                if match:
                    hits.append((match.start(), match.end(), skill))
                    break
        hits.sort()
        group: set[str] = set()
        for (_, end, skill), (start, _, next_skill) in zip(hits, hits[1:]):
            if ALTERNATIVE_SEPARATOR.match(line[end:start]):
                group |= {skill, next_skill}
            elif len(group) > 1:
                groups.append(group)
                group = set()
        if len(group) > 1:
            groups.append(group)
    return groups


def _split_job_sections(job_description: str) -> tuple[str, str]:
    """Split the job description into required text and good-to-have text."""

    required_lines: list[str] = []
    bonus_lines: list[str] = []
    in_bonus = False

    for line in job_description.splitlines():
        lowered = line.lower().strip()
        is_heading = len(lowered) <= 60 and (lowered.endswith(":") or len(lowered.split()) <= 5)
        if is_heading and BONUS_HEADING.search(lowered):
            in_bonus = True
        elif is_heading and REQUIRED_HEADING.search(lowered):
            in_bonus = False
        elif BONUS_HEADING.search(lowered) and not is_heading:
            # Inline phrases such as "Experience with Spark is a plus" belong to the bonus list.
            bonus_lines.append(line)
            continue
        (bonus_lines if in_bonus else required_lines).append(line)

    return "\n".join(required_lines), "\n".join(bonus_lines)


def _meaningful_terms(text: str) -> set[str]:
    return {
        term
        for term in re.findall(r"[a-zA-Z][a-zA-Z+#.-]{2,}", text.lower())
        if term not in STOP_WORDS
    }


def _find_evidence(skill: str, resume_text: str) -> tuple[str, bool]:
    """Return the resume line that mentions a skill and whether it shows use (not just a list)."""

    patterns = SKILLS[skill].patterns
    best: tuple[str, bool] | None = None
    for raw_line in resume_text.splitlines():
        line = " ".join(raw_line.split())
        if not line or not any(re.search(p, line.lower()) for p in patterns):
            continue
        demonstrated = not SKILLS_LIST_LINE.match(line) and len(line.split()) >= 6
        snippet = line if len(line) <= 140 else line[:137].rstrip() + "..."
        if demonstrated:
            return snippet, True
        best = best or (snippet, False)
    return best or ("", False)


def _build_suggestions(
    gaps: list[GapDetail], evidence: list[SkillEvidence], resume_text: str
) -> list[str]:
    suggestions: list[str] = []

    for gap in [g for g in gaps if g.required][:2]:
        suggestions.append(
            f"{gap.skill} is required but your resume doesn't show it. If you have used it, add a bullet that proves it; "
            f"if not, a quick way to build evidence: {gap.project_idea}"
        )

    listed_only = [e.skill for e in evidence if not e.demonstrated]
    if listed_only:
        names = ", ".join(listed_only[:3])
        single = len(listed_only[:3]) == 1
        suggestions.append(
            f"{names} {'appears' if single else 'appear'} only in a skills list. Add a project or experience bullet "
            f"showing how you used {'it' if single else 'them'}, so recruiters and ATS see real evidence."
        )

    quantified = sum(1 for line in resume_text.splitlines() if re.search(r"\d", line) and len(line.split()) >= 5)
    if quantified < 3:
        suggestions.append(
            "Few bullets include numbers. Where true, add measurable results such as accuracy reached, time saved, "
            "users served, or dataset size."
        )

    bonus_gap = next((g for g in gaps if not g.required), None)
    if bonus_gap and len(suggestions) < 4:
        suggestions.append(f"{bonus_gap.skill} is a good-to-have that would set you apart: {bonus_gap.project_idea}")

    if not suggestions:
        suggestions.append(
            "Move the matching skills into your top project bullets and lead each bullet with the result you achieved."
        )

    return suggestions[:4]


def build_match_report(resume_text: str, job_description: str) -> MatchReport:
    """Build a reproducible fit report from supplied resume and job text."""

    required_text, bonus_text = _split_job_sections(job_description)
    direct_resume_skills = find_skills(resume_text)
    implied_by = _with_implied(direct_resume_skills)
    resume_skills = set(implied_by)
    required_skills = find_skills(required_text)
    bonus_skills = find_skills(bonus_text) - required_skills

    # "PyTorch or TensorFlow": if the resume shows one alternative, the others are not gaps.
    for group in _alternative_groups(job_description):
        if group & resume_skills:
            required_skills -= group - resume_skills
            bonus_skills -= group - resume_skills
    job_skills = required_skills | bonus_skills

    matching_skills = sorted(resume_skills & job_skills)
    missing_required = sorted(required_skills - resume_skills)
    missing_bonus = sorted(bonus_skills - resume_skills)

    job_terms = _meaningful_terms(job_description)
    term_coverage = len(job_terms & _meaningful_terms(resume_text)) / len(job_terms) if job_terms else 0

    required_coverage = len(required_skills & resume_skills) / len(required_skills) if required_skills else None
    bonus_coverage = len(bonus_skills & resume_skills) / len(bonus_skills) if bonus_skills else None

    if required_coverage is None and bonus_coverage is None:
        score = round(term_coverage * 100)
    else:
        primary = required_coverage if required_coverage is not None else bonus_coverage
        secondary = bonus_coverage if bonus_coverage is not None else primary
        score = round(primary * 70 + secondary * 15 + term_coverage * 15)

    evidence = []
    for skill in matching_skills:
        snippet, demonstrated = _find_evidence(implied_by[skill] or skill, resume_text)
        evidence.append(SkillEvidence(skill, SKILLS[skill].category, snippet, demonstrated))

    gaps = [GapDetail(s, SKILLS[s].category, True, SKILLS[s].project_idea) for s in missing_required] + [
        GapDetail(s, SKILLS[s].category, False, SKILLS[s].project_idea) for s in missing_bonus
    ]

    categories: dict[str, list[int]] = {}
    for skill in job_skills:
        counts = categories.setdefault(SKILLS[skill].category, [0, 0])
        counts[1] += 1
        counts[0] += skill in resume_skills
    coverage = [CategoryCoverage(name, matched, total) for name, (matched, total) in sorted(categories.items())]

    return MatchReport(
        match_score=max(0, min(score, 100)),
        matching_skills=matching_skills,
        missing_skills=sorted(missing_required + missing_bonus),
        resume_skills=sorted(resume_skills),
        suggestions=_build_suggestions(gaps, evidence, resume_text),
        required_matched=len(required_skills & resume_skills),
        required_total=len(required_skills),
        bonus_matched=len(bonus_skills & resume_skills),
        bonus_total=len(bonus_skills),
        skill_evidence=evidence,
        gaps=gaps,
        category_coverage=coverage,
    )


def build_application_plan(report: MatchReport, target_role: str) -> ApplicationPlan:
    """Convert evidence into an honest, concrete next-step plan (without repeating the suggestions)."""

    role = target_role.strip() or "this role"
    required_gaps = [g for g in report.gaps if g.required]
    top_gap = required_gaps[0].skill if required_gaps else (report.missing_skills[0] if report.missing_skills else None)

    if report.match_score >= 70 and not report.missing_skills:
        return ApplicationPlan(
            readiness="ready_to_apply",
            headline=f"You have evidence to apply for {role} now.",
            reason="Your resume already demonstrates the skills this job description names.",
            next_actions=[
                "Mirror the job's wording in your summary and top project bullet.",
                "Submit only claims you can defend in an interview.",
                "Prepare one concrete story for each matching skill.",
            ],
        )

    if report.match_score >= 45:
        gap = top_gap or "role-specific evidence"
        return ApplicationPlan(
            readiness="apply_after_updates",
            headline=f"Apply after a focused update for {role}.",
            reason=f"Your profile has relevant evidence, but {gap} needs a clearer proof point or a learning plan.",
            next_actions=[
                f"This week: close the {gap} gap with the project idea in the Skills tab.",
                "Rewrite your top 3 bullets to lead with measurable results.",
                "Save this opportunity and apply once the update is truthful and complete.",
            ],
        )

    gap = top_gap or "relevant project evidence"
    return ApplicationPlan(
        readiness="build_evidence_first",
        headline=f"Build evidence before prioritizing {role}.",
        reason=f"The current CV does not yet show enough overlap with the role. Start with {gap}.",
        next_actions=[
            f"Start with {gap}: build one small, public project that proves it.",
            "Pick 2-3 required skills from the Skills tab and plan a 4-week learning sprint.",
            "Return and re-run this analysis once the project is on your resume.",
        ],
    )
