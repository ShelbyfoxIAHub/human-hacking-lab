import json
import re
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

    def test_red_team_scenario_has_fixed_local_scope_and_stop_conditions(self):
        scenarios = json.loads(
            (ROOT / "apps" / "simulator" / "scenarios.json").read_text(
                encoding="utf-8"
            )
        )["scenarios"]
        self.assertEqual(len(scenarios), 1)
        scenario = scenarios[0]
        self.assertEqual(scenario["scenario_id"], "HHL-RT-01")
        self.assertEqual(scenario["campaign_id"], "HHL02-A")
        self.assertTrue(any("MailHog" in item for item in scenario["scope"]))
        self.assertTrue(
            any("Credential collection" in item for item in scenario["prohibited_actions"])
        )
        self.assertTrue(scenario["stop_conditions"])

    def test_compose_contains_local_only_ports(self):
        compose = (ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn('"127.0.0.1:8090:8090"', compose)
        self.assertIn('"127.0.0.1:8025:8025"', compose)
        self.assertIn('"127.0.0.1:8080:8080"', compose)

    def test_lab_network_blocks_external_egress(self):
        compose = (ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertRegex(
            compose,
            r"networks:\s+lab:\s+name:\s+hhl-isolated\s+driver:\s+bridge\s+internal:\s+true",
        )

    def test_every_published_port_is_loopback_bound(self):
        compose = (ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
        bindings = re.findall(
            r'^\s*-\s+"([^"]*:\d+:\d+)"\s*$',
            compose,
            re.MULTILINE,
        )
        self.assertTrue(bindings)
        self.assertTrue(
            all(re.fullmatch(r"127\.0\.0\.1:\d+:\d+", binding) for binding in bindings),
            bindings,
        )
        self.assertNotIn("network_mode: host", compose)

    def test_host_access_network_is_limited_to_dashboard_and_mailhog(self):
        compose = (ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertRegex(
            compose,
            re.compile(r"web:.*?networks: \[lab, host-access\]", re.DOTALL),
        )
        self.assertRegex(
            compose,
            re.compile(r"mail:.*?networks: \[lab, host-access\]", re.DOTALL),
        )
        self.assertRegex(
            compose,
            re.compile(
                r"host-access:\s+name:\s+hhl-host-access\s+driver:\s+bridge\s+driver_opts:\s+com\.docker\.network\.bridge\.enable_ip_masquerade:\s+\"false\"",
                re.DOTALL,
            ),
        )

    def test_telemetry_never_stores_plaintext_token_in_new_events(self):
        source = (ROOT / "apps" / "simulator" / "app.py").read_text(encoding="utf-8")
        self.assertIn("hash_token(token)", source)
        self.assertIn("token=NULL", source)
        self.assertIn("correlation_id", source)

    def test_telemetry_contract_exists(self):
        schema = (ROOT / "docs" / "TELEMETRY-SCHEMA.md").read_text(encoding="utf-8")
        for field in ("event_id", "campaign_id", "event_type", "timestamp", "correlation_id"):
            self.assertIn(field, schema)

    def test_training_request_preserves_run_correlation(self):
        source = (ROOT / "apps" / "web" / "app.py").read_text(encoding="utf-8")
        self.assertIn('"correlation_id": query.get("run", [""])[0]', source)
