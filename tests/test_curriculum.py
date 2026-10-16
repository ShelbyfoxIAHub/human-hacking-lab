import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
MANIFEST_PATH = ROOT / "apps" / "web" / "curriculum.json"


class IntegratedCurriculumTest(unittest.TestCase):
    def test_curriculum_prerequisites_form_a_valid_acyclic_graph(self):
        curriculum = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        modules = curriculum["modules"]
        module_ids = [module["id"] for module in modules]
        self.assertEqual(len(module_ids), len(set(module_ids)))
        known_ids = set(module_ids)
        self.assertTrue(
            all(
                prerequisite in known_ids
                for module in modules
                for prerequisite in module["prerequisites"]
            )
        )

        remaining = set(module_ids)
        completed = set()
        while remaining:
            ready = {
                module["id"]
                for module in modules
                if module["id"] in remaining
                and set(module["prerequisites"]).issubset(completed)
            }
            self.assertTrue(ready, "Curriculum prerequisites must be acyclic")
            completed.update(ready)
            remaining.difference_update(ready)

    def test_all_curriculum_exercises_exist_and_define_evidence(self):
        curriculum = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        for module in curriculum["modules"]:
            with self.subTest(module=module["id"]):
                self.assertTrue((ROOT / module["exercise_path"]).is_file())
                self.assertTrue(module["evidence"])

    def test_progress_is_local_self_reported_and_uses_synthetic_ids(self):
        curriculum = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        page = (ROOT / "apps" / "web" / "index.html").read_text(encoding="utf-8")

        self.assertEqual(curriculum["progress_mode"], "local_self_reported")
        self.assertIn("autodeclarado", page.lower())
        self.assertIn("localStorage", page)
        self.assertIn("learnerIdPattern", page)

    def test_curriculum_covers_requested_learning_tracks(self):
        curriculum = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        module_ids = {module["id"] for module in curriculum["modules"]}

        self.assertTrue(
            {
                "RED-TEAM",
                "BLUE-TEAM",
                "DETECTION",
                "THREAT-HUNT-DFIR",
                "OSINT",
                "APPSEC",
                "HUMAN-RISK",
                "SECURITY-ENGINEERING",
            }.issubset(module_ids)
        )


if __name__ == "__main__":
    unittest.main()
