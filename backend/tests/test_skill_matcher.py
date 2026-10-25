import unittest

from app.services.skill_matcher import build_match_report


class SkillMatcherTests(unittest.TestCase):
    def test_reports_evidenced_and_missing_job_skills(self) -> None:
        report = build_match_report(
            "Built Python data-analysis projects with Pandas and SQL.",
            "We need a data analyst with Python, SQL, Power BI, and Tableau.",
        )

        self.assertEqual(report.matching_skills, ["Data Analysis", "Python", "SQL"])
        self.assertEqual(report.missing_skills, ["Power BI", "Tableau"])
        self.assertGreater(report.match_score, 0)
        self.assertLess(report.match_score, 100)

    def test_never_claims_missing_skill_as_evidenced(self) -> None:
        report = build_match_report(
            "I use Excel for coursework.",
            "The role requires Python and SQL.",
        )

        self.assertEqual(report.matching_skills, [])
        self.assertEqual(report.missing_skills, ["Python", "SQL"])
        self.assertIn("Python", report.suggestions[0])


if __name__ == "__main__":
    unittest.main()
