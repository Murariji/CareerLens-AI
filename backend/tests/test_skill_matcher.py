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
        self.assertIn("Tableau", plan.next_actions[0])
        # The plan must not just repeat the suggestions shown elsewhere on the page.
        self.assertFalse(set(plan.next_actions) & set(report.suggestions))

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

    def test_detects_ml_skills_and_separates_good_to_have(self) -> None:
        job = (
            "Requirements:\n"
            "- Hands-on experience with machine learning and deep learning (PyTorch or TensorFlow)\n"
            "- Experience building REST APIs and working with Docker\n"
            "Good to have:\n"
            "- Experience with Hugging Face, LangChain, or vector databases\n"
        )
        resume = (
            "Skills: Python, PyTorch, Docker, FastAPI\n"
            "Trained a PyTorch CNN image classifier reaching 92% accuracy on 10,000 images.\n"
        )
        report = build_match_report(resume, job)

        self.assertIn("PyTorch", report.matching_skills)
        self.assertIn("Deep Learning", report.matching_skills)
        required = {g.skill for g in report.gaps if g.required}
        bonus = {g.skill for g in report.gaps if not g.required}
        self.assertEqual(required, set())  # FastAPI implies REST APIs; PyTorch covers "PyTorch or TensorFlow".
        self.assertIn("REST APIs", report.matching_skills)
        self.assertEqual(bonus, {"Hugging Face", "LangChain", "Vector Databases"})
        self.assertEqual(report.bonus_total, 3)
        pytorch = next(e for e in report.skill_evidence if e.skill == "PyTorch")
        self.assertTrue(pytorch.demonstrated)
        self.assertIn("92%", pytorch.evidence)

    def test_alternatives_and_implied_skills_are_not_gaps(self) -> None:
        report = build_match_report(
            "Trained a PyTorch CNN on 10,000 images. Built a FastAPI service for predictions.",
            "ML Engineer. Requirements: machine learning with PyTorch or TensorFlow; REST APIs; AWS/Azure.",
        )

        gaps = {g.skill for g in report.gaps}
        self.assertNotIn("TensorFlow", gaps)
        self.assertNotIn("Machine Learning", gaps)
        self.assertNotIn("REST APIs", gaps)
        self.assertTrue({"AWS", "Azure"} <= gaps)  # Neither alternative is evidenced, so both stay.
        ml = next(e for e in report.skill_evidence if e.skill == "Machine Learning")
        self.assertIn("PyTorch", ml.evidence)

    def test_flags_skills_that_only_appear_in_a_list(self) -> None:
        report = build_match_report(
            "Skills: Python, SQL, Docker, Git, Pandas\nEducation: B.Tech Computer Science",
            "We need Python, SQL and Docker experience for this backend role.",
        )

        docker = next(e for e in report.skill_evidence if e.skill == "Docker")
        self.assertFalse(docker.demonstrated)
        self.assertTrue(any("only in a skills list" in s for s in report.suggestions))

    def test_suggestions_are_not_repetitive_templates(self) -> None:
        report = build_match_report(
            "Built dashboards in Excel for 3 college clubs, saving 5 hours a week. Led a team of 4. Improved reports by 20%.",
            "Requirements: AWS, Azure, Agile, Kubernetes, Docker and Python.",
        )

        self.assertLessEqual(len(report.suggestions), 4)
        self.assertEqual(len(report.suggestions), len(set(report.suggestions)))
        self.assertEqual(sum("required but your resume" in s for s in report.suggestions), 2)


if __name__ == "__main__":
    unittest.main()
