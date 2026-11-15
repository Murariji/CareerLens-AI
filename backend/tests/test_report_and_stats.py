import json
import os
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

import httpx
import pymupdf
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import AnalysisResponse
from app.services import stats as stats_module
from app.services.report_export import build_markdown
from app.services.stats import (
    MemoryStatsStore,
    StatsEvent,
    StatsService,
    SupabaseStatsStore,
    role_category,
)

SAMPLE = json.loads((Path(__file__).parents[2] / "frontend" / "src" / "sampleReport.json").read_text(encoding="utf-8"))


class ReportExportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_pdf_download_is_a_real_pdf_with_the_report_content(self) -> None:
        response = self.client.post("/api/report/pdf", json=SAMPLE)

        self.assertEqual(response.status_code, 200, response.text[:300])
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertIn("attachment; filename=\"careerlens-ml-ai-engineer-", response.headers["content-disposition"])
        document = pymupdf.open(stream=response.content, filetype="pdf")
        text = "".join(page.get_text() for page in document)
        self.assertIn("67% match", text)
        self.assertIn("ATS checklist", text)
        self.assertIn("Interview questions", text)

    def test_word_download_opens_as_html_document(self) -> None:
        response = self.client.post("/api/report/doc", json=SAMPLE)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/msword")
        body = response.content.decode("utf-8")
        self.assertIn("urn:schemas-microsoft-com:office:word", body)
        self.assertIn("Bullet rewrites", body)

    def test_markdown_download_and_escaping(self) -> None:
        report = AnalysisResponse.model_validate({**SAMPLE, "target_role": "<script>alert(1)</script> Engineer"})
        markdown = build_markdown(report)
        self.assertTrue(markdown.startswith("# CareerLens report:"))
        self.assertIn("- [x] **Email and phone number**", markdown)

        html_doc = self.client.post("/api/report/doc", json=report.model_dump()).content.decode()
        self.assertNotIn("<script>", html_doc)
        self.assertIn("&lt;script&gt;", html_doc)

    def test_head_requests_used_by_uptime_checks_succeed(self) -> None:
        self.assertEqual(self.client.head("/").status_code, 200)
        self.assertEqual(self.client.head("/api/health").status_code, 200)

    def test_unknown_format_is_rejected(self) -> None:
        self.assertEqual(self.client.post("/api/report/exe", json=SAMPLE).status_code, 422)


class StatsTests(unittest.IsolatedAsyncioTestCase):
    def test_role_category_never_stores_free_text(self) -> None:
        self.assertEqual(role_category("ML/AI Engineer"), "ML / AI")
        self.assertEqual(role_category("Data Analyst"), "Data & analytics")
        self.assertEqual(role_category("Backend Developer"), "Software engineering")
        self.assertEqual(role_category("Chef"), "Other")

    def test_visitor_hash_is_stable_per_day_and_changes_daily(self) -> None:
        service = StatsService(MemoryStatsStore(), salt="s")
        today = service.visitor_hash("1.2.3.4", "ua", date(2026, 11, 15))
        self.assertEqual(today, service.visitor_hash("1.2.3.4", "ua", date(2026, 11, 15)))
        self.assertNotEqual(today, service.visitor_hash("1.2.3.4", "ua", date(2026, 11, 16)))
        self.assertNotIn("1.2.3.4", today)

    async def test_memory_summary_counts(self) -> None:
        service = StatsService(MemoryStatsStore(), salt="s", cache_seconds=0)
        for visitor in ("a", "a", "b"):
            await service.record(StatsEvent(kind="visit", visitor=visitor))
        await service.record(StatsEvent(kind="analysis", role_category="ML / AI", score=60, ai=True))
        await service.record(StatsEvent(kind="analysis", role_category="Other", score=40, ai=False))

        summary = await service.summary()
        self.assertEqual(summary["visits"], 3)
        self.assertEqual(summary["unique_visitors"], 2)
        self.assertEqual(summary["analyses"], 2)
        self.assertEqual(summary["ai_analyses"], 1)
        self.assertEqual(summary["average_score"], 50)
        self.assertEqual(len(summary["last_30_days"]), 30)
        self.assertEqual(summary["last_30_days"][-1]["analyses"], 2)

    async def test_supabase_store_calls_rpc_with_token(self) -> None:
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append((str(request.url), json.loads(request.content), request.headers["apikey"]))
            if request.url.path.endswith("careerlens_stats"):
                return httpx.Response(200, json={"visits": 10, "analyses": 4, "unexpected": "ignored"})
            return httpx.Response(204)

        store = SupabaseStatsStore("https://x.supabase.co/", "pub-key", "tok", http=httpx.AsyncClient(transport=httpx.MockTransport(handler)))
        await store.record(StatsEvent(kind="analysis", role_category="ML / AI", score=70, ai=True))
        summary = await store.summary()

        self.assertEqual(calls[0][0], "https://x.supabase.co/rest/v1/rpc/careerlens_record_event")
        self.assertEqual(calls[0][1]["p_token"], "tok")
        self.assertEqual(calls[0][2], "pub-key")
        self.assertEqual(summary["visits"], 10)
        self.assertTrue(summary["persistent"])
        self.assertNotIn("unexpected", summary)

    async def test_stats_failures_never_break_requests(self) -> None:
        store = SupabaseStatsStore("https://x", "k", "t", http=httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(500))))
        service = StatsService(store, salt="t", cache_seconds=0)
        await service.record(StatsEvent(kind="visit", visitor="v"))  # Must not raise.
        self.assertEqual((await service.summary())["storage"], "unavailable")

    def test_endpoints_record_visits_and_expose_stats(self) -> None:
        fresh = StatsService(MemoryStatsStore(), salt="s", cache_seconds=0)
        with mock.patch.object(stats_module, "stats_service", fresh), mock.patch("app.main.stats_service", fresh), \
                mock.patch.dict(os.environ, {}, clear=True):
            client = TestClient(app)
            client.get("/api/health")              # wake-up ping: not a visit
            client.get("/api/health?visit=1")      # page load: a visit
            body = client.get("/api/stats").json()

        self.assertEqual(body["visits"], 1)
        self.assertEqual(body["storage"], "memory")


if __name__ == "__main__":
    unittest.main()
