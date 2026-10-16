import unittest
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "apps" / "detection"))
import detector


class DetectionArtifactsTest(unittest.TestCase):
    def test_detection_rules_are_documented(self):
        source = (ROOT / "apps" / "detection" / "detector.py").read_text(encoding="utf-8")
        docs = (ROOT / "docs" / "DETECTION-RULES.md").read_text(encoding="utf-8")
        for rule in ("HHL-D001", "HHL-D002"):
            self.assertIn(rule, source)
            self.assertIn(rule, docs)

    def test_detection_service_does_not_write_to_shared_db(self):
        source = (ROOT / "apps" / "detection" / "detector.py").read_text(encoding="utf-8")
        self.assertIn("mode=ro", source)
        self.assertNotIn(".commit(", source)
        self.assertNotIn("INSERT INTO", source)
        self.assertNotIn("UPDATE ", source)
        self.assertNotIn("DELETE FROM", source)

    def test_detection_port_is_loopback_bound(self):
        compose = (ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn('"127.0.0.1:8091:8091"', compose)

    def test_hunt_hypotheses_return_deterministic_evidence(self):
        events = [
            {
                "event_id": f"event-{user_id}-{click_number}",
                "campaign_id": "HHL02-A",
                "user_id": user_id,
                "event_type": "clicked",
                "timestamp": f"2026-10-16T12:00:{click_number:02d}Z",
                "correlation_id": "run-1",
                "source": "training",
                "metadata": {},
            }
            for user_id in ("U001", "U002", "U003", "U004", "U005")
            for click_number in range(1, 5 if user_id == "U001" else 2)
        ]

        results = {
            hunt["hunt_id"]: hunt
            for hunt in detector.hunt_hypotheses(events)
        }

        self.assertEqual(
            [hunt["hunt_id"] for hunt in detector.hunt_hypotheses(events)],
            ["HHL-H001", "HHL-H002", "HHL-H003"],
        )
        self.assertEqual(results["HHL-H001"]["matches"][0]["user_id"], "U001")
        self.assertEqual(results["HHL-H001"]["matches"][0]["click_count"], 4)
        self.assertEqual(results["HHL-H002"]["matches"][0]["user_count"], 5)
        self.assertEqual(results["HHL-H003"]["matches"][0]["correlation_id"], "run-1")

    def test_incident_timeline_is_run_scoped_and_chronological(self):
        events = [
            {
                "event_id": "event-2",
                "campaign_id": "HHL02-A",
                "user_id": "U001",
                "event_type": "clicked",
                "timestamp": "2026-10-16T12:00:02Z",
                "correlation_id": "run-1",
                "source": "training",
                "metadata": {},
            },
            {
                "event_id": "event-other",
                "campaign_id": "HHL02-A",
                "user_id": "U002",
                "event_type": "clicked",
                "timestamp": "2026-10-16T12:00:00Z",
                "correlation_id": "run-2",
                "source": "training",
                "metadata": {},
            },
            {
                "event_id": "event-1",
                "campaign_id": "HHL02-A",
                "user_id": "U001",
                "event_type": "delivered",
                "timestamp": "2026-10-16T12:00:01Z",
                "correlation_id": "run-1",
                "source": "smtp",
                "metadata": {},
            },
        ]

        timeline = detector.incident_timeline(events, "run-1")

        self.assertEqual([event["event_id"] for event in timeline], ["event-1", "event-2"])
        self.assertTrue(
            all(event["correlation_id"] == "run-1" for event in timeline)
        )
        self.assertTrue(all("token" not in event for event in timeline))

    def test_campaign_burst_alert_contains_all_supporting_event_ids(self):
        events = [
            {
                "event_id": f"event-{user_id}",
                "campaign_id": "HHL02-A",
                "user_id": user_id,
                "event_type": "clicked",
                "timestamp": "2026-10-16T12:00:00Z",
                "correlation_id": "run-blue",
                "source": "training",
                "metadata": {},
            }
            for user_id in ("U001", "U002", "U003", "U004", "U005")
        ]

        with patch("detector.load_events", return_value=events):
            alerts = detector.detect("HHL02-A")

        campaign_alert = next(alert for alert in alerts if alert["rule_id"] == "HHL-D002")
        self.assertEqual(
            campaign_alert["evidence_event_ids"],
            [f"event-U00{index}" for index in range(1, 6)],
        )
