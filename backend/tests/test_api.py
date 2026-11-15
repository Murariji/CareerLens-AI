import os
import unittest
from unittest import mock

import pymupdf
from fastapi.testclient import TestClient

from app.main import app

RESUME_TEXT = """Asha Kumar | asha@example.com | +91 98765 43210 | linkedin.com/in/asha | github.com/asha
Education
B.Tech Computer Science, 2025
Skills
Python, PyTorch, SQL, Docker, Git
Projects
Trained a PyTorch CNN image classifier reaching 92% accuracy on 10,000 images.
Built a FastAPI service that serves model predictions to 200 users.
Developed a RAG chatbot over course notes using LangChain and FAISS.
Experience
Improved data pipeline speed by 30% during a 3-month internship.
"""
JOB = """We are hiring an ML/AI Engineer.
Requirements:
- Machine learning and deep learning with PyTorch or TensorFlow
- Build REST APIs with FastAPI and Docker; deploy on AWS
Good to have:
- Hugging Face, LangChain, or vector databases
"""


def make_pdf(text: str) -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_textbox(pymupdf.Rect(40, 40, 560, 800), text, fontsize=10)
    return document.tobytes()


class AnalyzeEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_reports_ai_status(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            body = self.client.get("/api/health").json()
        self.assertEqual(body, {"status": "ok", "ai_enabled": False, "ai_provider": None})

    def test_full_rule_based_analysis(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            response = self.client.post(
                "/api/analyze",
                files={"resume": ("resume.pdf", make_pdf(RESUME_TEXT), "application/pdf")},
                data={"job_description": JOB, "target_role": "ML/AI Engineer", "location": "India"},
            )

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["analysis_source"], "baseline")
        self.assertIn("PyTorch", body["matching_skills"])
        self.assertIn("AWS", [g["skill"] for g in body["gaps"] if g["required"]])
        self.assertIn("Hugging Face", [g["skill"] for g in body["gaps"] if not g["required"]])
        self.assertGreater(body["required_total"], 0)
        self.assertEqual(body["ats"]["total"], len(body["ats"]["checks"]))
        checks = {c["id"]: c["passed"] for c in body["ats"]["checks"]}
        self.assertTrue(checks["contact"])
        self.assertTrue(checks["profiles"])
        self.assertTrue(checks["metrics"])
        self.assertTrue(any(c["category"] for c in body["category_coverage"]))


if __name__ == "__main__":
    unittest.main()
