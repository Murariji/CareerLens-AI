import os
import unittest
from types import SimpleNamespace
from unittest import mock

from app.schemas import EvidencedStrength, InterviewQuestion, SkillGap
from app.services.llm_analyzer import LLMAnalysisOutput, analyze_with_llm, apply_guardrails
from app.services.skill_matcher import build_match_report

RESUME = "Built Python data-analysis projects with Pandas and SQL.\nLed a 4-person   capstone team."
JOB = "We need a data analyst with Python, SQL, Power BI, and Tableau experience."


def make_output(**overrides) -> LLMAnalysisOutput:
    values = {
        "fit_summary": "A solid analytics foundation with clear gaps in BI tools.",
        "strengths": [
            EvidencedStrength(skill="Python", resume_evidence="Built Python data-analysis projects"),
            EvidencedStrength(skill="Leadership", resume_evidence="led a 4-person capstone team"),
            EvidencedStrength(skill="Kubernetes", resume_evidence="Deployed services on Kubernetes"),
        ],
        "gaps": [
            SkillGap(skill="Power BI", job_requirement="Power BI", how_to_close="Build one dashboard."),
            SkillGap(skill="Spark", job_requirement="5 years of Spark", how_to_close="Learn Spark."),
        ],
        "resume_suggestions": ["If you used SQL joins in the capstone, say so.", "  "],
        "interview_questions": [InterviewQuestion(question="Walk me through a Pandas project.", why_asked="Resume lists Pandas.")],
    }
    values.update(overrides)
    return LLMAnalysisOutput(**values)


class FakeMessages:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    async def parse(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


def fake_client(response=None, error=None):
    return SimpleNamespace(beta=SimpleNamespace(messages=FakeMessages(response, error)))


class GuardrailTests(unittest.TestCase):
    def test_keeps_only_claims_quoted_from_the_supplied_text(self) -> None:
        result = apply_guardrails(make_output(), RESUME, JOB, "claude-opus-5-5")

        self.assertEqual([s.skill for s in result.strengths], ["Python", "Leadership"])
        self.assertEqual([g.skill for g in result.gaps], ["Power BI"])
        self.assertEqual(result.removed_unsupported_items, 2)
        self.assertEqual(result.resume_suggestions, ["If you used SQL joins in the capstone, say so."])

    def test_rejects_quotes_that_are_too_short_to_prove_anything(self) -> None:
        output = make_output(strengths=[EvidencedStrength(skill="Python", resume_evidence=" . ")], gaps=[])
        result = apply_guardrails(output, RESUME, JOB, "claude-opus-5-5")

        self.assertEqual(result.strengths, [])
        self.assertEqual(result.removed_unsupported_items, 1)


class AnalyzeWithLLMTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.report = build_match_report(RESUME, JOB)

    async def test_returns_notice_when_no_api_key_is_configured(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            result = await analyze_with_llm(RESUME, JOB, "Data Analyst", self.report)

        self.assertIsNone(result.analysis)
        self.assertIn("not configured", result.notice)

    async def test_returns_guarded_analysis_on_success(self) -> None:
        response = SimpleNamespace(
            stop_reason="end_turn", parsed_output=make_output(), model="claude-opus-5-5", _request_id="req_1"
        )
        client = fake_client(response)

        result = await analyze_with_llm(RESUME, JOB, "Data Analyst", self.report, client=client)

        self.assertIsNone(result.notice)
        self.assertEqual(len(result.analysis.strengths), 2)
        call = client.beta.messages.calls[0]
        self.assertIs(call["output_format"], LLMAnalysisOutput)
        self.assertIn("<resume>", call["messages"][0]["content"])

    async def test_falls_back_to_baseline_on_refusal(self) -> None:
        response = SimpleNamespace(stop_reason="refusal", parsed_output=None, model="m", _request_id="req_2")

        result = await analyze_with_llm(RESUME, JOB, "Data Analyst", self.report, client=fake_client(response))

        self.assertIsNone(result.analysis)
        self.assertIn("baseline", result.notice)

    async def test_falls_back_to_baseline_on_connection_error(self) -> None:
        import anthropic

        error = anthropic.APIConnectionError(request=mock.Mock())
        result = await analyze_with_llm(RESUME, JOB, "Data Analyst", self.report, client=fake_client(error=error))

        self.assertIsNone(result.analysis)
        self.assertIn("temporarily unavailable", result.notice)


if __name__ == "__main__":
    unittest.main()
