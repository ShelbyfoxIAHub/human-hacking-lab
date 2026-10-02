import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


class DetectionArtifactsTest(unittest.TestCase):
    def test_detection_rules_are_documented(self):
        source = (ROOT / "apps" / "detection" / "detector.py").read_text(encoding="utf-8")
        docs = (ROOT / "docs" / "DETECTION-RULES.md").read_text(encoding="utf-8")
        for rule in ("HHL-D001", "HHL-D002"):
            self.assertIn(rule, source)
            self.assertIn(rule, docs)

    def test_detection_service_does_not_write_to_shared_db(self):
        source = (ROOT / "apps" / "detection" / "detector.py").read_text(encoding="utf-8")
        self.assertNotIn(".commit(", source)
        self.assertNotIn("INSERT INTO", source)
        self.assertNotIn("UPDATE ", source)
        self.assertNotIn("DELETE FROM", source)

    def test_detection_port_is_loopback_bound(self):
        compose = (ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn('"127.0.0.1:8091:8091"', compose)
