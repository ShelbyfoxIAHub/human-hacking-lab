import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class SimulationArtifactsTest(unittest.TestCase):
    def test_campaign_is_synthetic(self):
        campaigns = json.loads(
            (ROOT / "apps" / "simulator" / "campaigns.json").read_text(encoding="utf-8")
        )
        self.assertTrue(campaigns)
        for campaign in campaigns:
            self.assertIn(".lab.invalid", campaign["sender"])
            self.assertNotIn("password", campaign["body"].lower())
            self.assertNotIn("<form", campaign["body"].lower())
            self.assertNotIn("input", campaign["body"].lower())

    def test_compose_contains_local_only_ports(self):
        compose = (ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn('"127.0.0.1:8090:8090"', compose)
        self.assertIn('"127.0.0.1:8025:8025"', compose)
        self.assertIn('"127.0.0.1:8080:8080"', compose)

    def test_telemetry_never_stores_plaintext_token_in_new_events(self):
        source = (ROOT / "apps" / "simulator" / "app.py").read_text(encoding="utf-8")
        self.assertIn("hash_token(token)", source)
        self.assertIn("token=NULL", source)
        self.assertIn("correlation_id", source)

    def test_telemetry_contract_exists(self):
        schema = (ROOT / "docs" / "TELEMETRY-SCHEMA.md").read_text(encoding="utf-8")
        for field in ("event_id", "campaign_id", "event_type", "timestamp", "correlation_id"):
            self.assertIn(field, schema)
