import unittest

from fastapi.testclient import TestClient

from app.main import app
from app.services import rate_limit
from app.services.rate_limit import RateLimiter


class RateLimiterTests(unittest.TestCase):
    def test_blocks_after_limit_and_recovers_after_window(self) -> None:
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        self.assertEqual(limiter.check("ip", now=0), 0)
        self.assertEqual(limiter.check("ip", now=1), 0)
        self.assertGreater(limiter.check("ip", now=2), 0)
        self.assertEqual(limiter.check("other-ip", now=2), 0)
        self.assertEqual(limiter.check("ip", now=61), 0)

    def test_endpoint_returns_429_with_clear_message(self) -> None:
        original = rate_limit.analysis_limiter
        rate_limit.analysis_limiter = RateLimiter(max_requests=0, window_seconds=60)
        try:
            response = TestClient(app).post(
                "/api/analyze",
                files={"resume": ("r.pdf", b"%PDF-1.4", "application/pdf")},
                data={"job_description": "x" * 40, "target_role": "ML"},
                headers={"X-Forwarded-For": "203.0.113.9"},
            )
        finally:
            rate_limit.analysis_limiter = original

        self.assertEqual(response.status_code, 429)
        self.assertIn("hourly limit", response.json()["detail"])
        self.assertIn("Retry-After", response.headers)


if __name__ == "__main__":
    unittest.main()
