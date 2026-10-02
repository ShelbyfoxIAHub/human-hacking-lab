import json
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


class SimulationArtifactsTest(unittest.TestCase):
    def test_campaign_is_synthetic(self):
        campaigns = json.loads(
            (ROOT / "apps" / "simulator" / "campaigns.json").read_text()
        )
        self.assertTrue(campaigns)
        for campaign in campaigns:
            self.assertIn(".lab.invalid", campaign["sender"])
            self.assertNotIn("password", campaign["body"].lower())
            self.assertNotIn("credential", campaign["body"].lower())

    def test_compose_contains_local_only_ports(self):
        compose = (ROOT / "infra" / "docker-compose.yml").read_text()
        self.assertIn('127.0.0.1:8090:8090', compose)
        self.assertIn('127.0.0.1:8025:8025', compose)
