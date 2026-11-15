import json
import os
import unittest
from types import SimpleNamespace
from unittest import mock

import httpx

from app.schemas import BulletRewrite, EvidencedStrength, InterviewQuestion, SkillGap
from app.services.llm_analyzer import (
    LLMAnalysisOutput,
    _inline_schema,
    analyze_with_llm,
    apply_guardrails,
    resolve_provider,
    resolve_providers,
)
from app.services.skill_matcher import build_match_report

RESUME = (
    "Built Python data-analysis projects with Pandas and SQL.\n"
    "Led a 4-person   capstone team.\n"
    "Created a sales dashboard for the college fest."
)
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
        "bullet_rewrites": [
            BulletRewrite(
                original="Created a sales dashboard for the college fest.",
                improved="Created a sales dashboard used by [N] fest organisers to track ticket revenue.",
                why="Shows impact.",
            ),
            BulletRewrite(  # invents a metric
                original="Created a sales dashboard for the college fest.",
                improved="Created a sales dashboard that increased revenue by 40%.",
                why="Adds a number.",
            ),
            BulletRewrite(  # invents a skill
                original="Created a sales dashboard for the college fest.",
                improved="Created a Tableau sales dashboard for the college fest.",
                why="Uses job keyword.",
            ),
            BulletRewrite(  # original not in resume
                original="Managed a 50-person event.",
                improved="Managed a large event.",
                why="Leadership.",
            ),
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


def mock_http(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


class GuardrailTests(unittest.TestCase):
    def test_keeps_only_claims_quoted_from_the_supplied_text(self) -> None:
        result = apply_guardrails(make_output(), RESUME, JOB, "claude-opus-5-5")

        self.assertEqual([s.skill for s in result.strengths], ["Python", "Leadership"])
        self.assertEqual([g.skill for g in result.gaps], ["Power BI"])
        self.assertEqual(result.resume_suggestions, ["If you used SQL joins in the capstone, say so."])

    def test_rejects_rewrites_that_invent_numbers_or_skills(self) -> None:
        result = apply_guardrails(make_output(), RESUME, JOB, "m")

        self.assertEqual(len(result.bullet_rewrites), 1)
        self.assertIn("[N]", result.bullet_rewrites[0].improved)
        # 1 strength + 1 gap + 3 rewrites were unverifiable.
        self.assertEqual(result.removed_unsupported_items, 5)

    def test_rejects_quotes_that_are_too_short_to_prove_anything(self) -> None:
        output = make_output(strengths=[EvidencedStrength(skill="Python", resume_evidence=" . ")], gaps=[], bullet_rewrites=[])
        result = apply_guardrails(output, RESUME, JOB, "claude-opus-5-5")

        self.assertEqual(result.strengths, [])
        self.assertEqual(result.removed_unsupported_items, 1)

    def test_inline_schema_has_no_refs_and_forbids_extra_keys(self) -> None:
        schema = _inline_schema(LLMAnalysisOutput)
        text = json.dumps(schema)

        self.assertNotIn("$ref", text)
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(schema["properties"]["bullet_rewrites"]["items"]["additionalProperties"])


class ProviderResolutionTests(unittest.TestCase):
    def test_auto_detects_first_available_key(self) -> None:
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "g", "ANTHROPIC_API_KEY": "a"}, clear=True):
            self.assertEqual(resolve_provider(), ("gemini", "g", "gemini-3.5-flash-lite"))

    def test_explicit_provider_and_model(self) -> None:
        env = {"CAREERLENS_LLM_PROVIDER": "groq", "GROQ_API_KEY": "k", "CAREERLENS_LLM_MODEL": "llama-3.3-70b-versatile"}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(resolve_provider(), ("groq", "k", "llama-3.3-70b-versatile"))

    def test_explicit_provider_without_key_falls_back_to_others(self) -> None:
        with mock.patch.dict(os.environ, {"CAREERLENS_LLM_PROVIDER": "groq", "GEMINI_API_KEY": "g"}, clear=True):
            self.assertEqual(resolve_provider(), ("gemini", "g", "gemini-3.5-flash-lite"))

    def test_both_free_providers_are_used_in_order(self) -> None:
        env = {"GROQ_API_KEY": "k", "GEMINI_API_KEY": "g", "CAREERLENS_LLM_PROVIDER": "gemini"}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual([p[0] for p in resolve_providers()], ["gemini", "groq"])


class AnalyzeWithLLMTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.report = build_match_report(RESUME, JOB)
        self.output_json = make_output().model_dump_json()

    async def test_returns_notice_when_no_provider_is_configured(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            result = await analyze_with_llm(RESUME, JOB, "Data Analyst", self.report)

        self.assertIsNone(result.analysis)
        self.assertIn("not configured", result.notice)

    async def test_anthropic_success(self) -> None:
        response = SimpleNamespace(
            stop_reason="end_turn", parsed_output=make_output(), model="claude-opus-5-5", _request_id="req_1"
        )
        client = fake_client(response)

        result = await analyze_with_llm(RESUME, JOB, "Data Analyst", self.report, client=client)

        self.assertIsNone(result.notice)
        self.assertEqual(result.analysis.provider, "anthropic")
        self.assertEqual(len(result.analysis.strengths), 2)
        call = client.beta.messages.calls[0]
        self.assertIs(call["output_format"], LLMAnalysisOutput)
        self.assertIn("<resume>", call["messages"][0]["content"])

    async def test_anthropic_refusal_falls_back(self) -> None:
        response = SimpleNamespace(stop_reason="refusal", parsed_output=None, model="m", _request_id="req_2")

        result = await analyze_with_llm(RESUME, JOB, "Data Analyst", self.report, client=fake_client(response))

        self.assertIsNone(result.analysis)
        self.assertIn("rule-based report", result.notice)

    async def test_groq_success_sends_strict_schema(self) -> None:
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["auth"] = request.headers["authorization"]
            seen["body"] = json.loads(request.content)
            return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": self.output_json}}]})

        with mock.patch.dict(os.environ, {"GROQ_API_KEY": "secret"}, clear=True):
            result = await analyze_with_llm(RESUME, JOB, "Data Analyst", self.report, http_client=mock_http(handler))

        self.assertIsNone(result.notice)
        self.assertEqual(result.analysis.provider, "groq")
        self.assertEqual(result.analysis.model, "openai/gpt-oss-120b")
        self.assertEqual(seen["auth"], "Bearer secret")
        self.assertTrue(seen["body"]["response_format"]["json_schema"]["strict"])

    async def test_groq_rate_limit_shows_busy_notice(self) -> None:
        with mock.patch.dict(os.environ, {"GROQ_API_KEY": "k"}, clear=True):
            result = await analyze_with_llm(
                RESUME, JOB, "Data Analyst", self.report, http_client=mock_http(lambda r: httpx.Response(429, json={}))
            )

        self.assertIsNone(result.analysis)
        self.assertIn("busy", result.notice)

    async def test_gemini_success(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["x-goog-api-key"] == "gk"
            assert "gemini-3.5-flash-lite:generateContent" in str(request.url)
            body = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": self.output_json}]}}]}
            return httpx.Response(200, json=body)

        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "gk"}, clear=True):
            result = await analyze_with_llm(RESUME, JOB, "Data Analyst", self.report, http_client=mock_http(handler))

        self.assertIsNone(result.notice)
        self.assertEqual(result.analysis.provider, "gemini")

    async def test_groq_rate_limit_falls_through_to_gemini(self) -> None:
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            if "groq.com" in str(request.url):
                calls.append("groq")
                return httpx.Response(429, json={})
            calls.append("gemini")
            body = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": self.output_json}]}}]}
            return httpx.Response(200, json=body)

        with mock.patch.dict(os.environ, {"GROQ_API_KEY": "k", "GEMINI_API_KEY": "g"}, clear=True):
            result = await analyze_with_llm(RESUME, JOB, "Data Analyst", self.report, http_client=mock_http(handler))

        self.assertEqual(calls, ["groq", "gemini"])
        self.assertIsNone(result.notice)
        self.assertEqual(result.analysis.provider, "gemini")

    async def test_invalid_json_from_provider_falls_back(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": "{not json"}}]})

        with mock.patch.dict(os.environ, {"GROQ_API_KEY": "k"}, clear=True):
            result = await analyze_with_llm(RESUME, JOB, "Data Analyst", self.report, http_client=mock_http(handler))

        self.assertIsNone(result.analysis)
        self.assertIn("temporarily unavailable", result.notice)

    async def test_network_error_falls_back(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("boom", request=request)

        with mock.patch.dict(os.environ, {"GROQ_API_KEY": "k"}, clear=True):
            result = await analyze_with_llm(RESUME, JOB, "Data Analyst", self.report, http_client=mock_http(handler))

        self.assertIsNone(result.analysis)
        self.assertIn("temporarily unavailable", result.notice)


if __name__ == "__main__":
    unittest.main()
