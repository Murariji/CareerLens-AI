import unittest

from app.services.skill_matcher import MatchReport, build_application_plan, build_match_report


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

    def test_builds_apply_now_plan_only_when_evidence_is_strong(self) -> None:
        report = build_match_report(
            "Python, SQL, Power BI, Tableau, data analysis, 3 years of experience.",
            "Data analyst role requiring Python, SQL, Power BI, and Tableau.",
        )

        plan = build_application_plan(report, "Data Analyst")

        self.assertEqual(plan.readiness, "ready_to_apply")
        self.assertIn("apply", plan.headline.lower())

    def test_partial_match_recommends_updates_before_applying(self) -> None:
        report = MatchReport(
            match_score=55,
            matching_skills=["Python"],
            missing_skills=["Tableau"],
            resume_skills=["Python"],
            suggestions=["Add a Tableau project.", "Add measurable outcomes."],
        )

        plan = build_application_plan(report, "Data Analyst")

        self.assertEqual(plan.readiness, "apply_after_updates")
        self.assertIn("Tableau", plan.reason)
        self.assertEqual(plan.next_actions[:2], report.suggestions)

    def test_high_score_with_missing_skill_is_not_ready(self) -> None:
        report = MatchReport(
            match_score=85,
            matching_skills=["Python", "SQL"],
            missing_skills=["Tableau"],
            resume_skills=["Python", "SQL"],
            suggestions=["Add a Tableau project."],
        )

        plan = build_application_plan(report, "Data Analyst")

        self.assertEqual(plan.readiness, "apply_after_updates")

    def test_weak_match_recommends_building_evidence_first(self) -> None:
        report = build_match_report(
            "I use Excel for coursework.",
            "The role requires Python and SQL.",
        )

        plan = build_application_plan(report, "  ")

        self.assertEqual(plan.readiness, "build_evidence_first")
        self.assertIn("this role", plan.headline)
        self.assertIn("Python", plan.reason)


if __name__ == "__main__":
    unittest.main()
