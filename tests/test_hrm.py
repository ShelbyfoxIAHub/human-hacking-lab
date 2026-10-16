import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "apps" / "hrm"))
import hrm


def synthetic_event(event_id, user_id, event_type, run_id="run-1", campaign="HHL02-A"):
    return {
        "event_id": event_id,
        "campaign_id": campaign,
        "user_id": user_id,
        "event_type": event_type,
        "timestamp": "2026-10-16T12:00:00Z",
        "correlation_id": run_id,
    }


class AggregateHrmTest(unittest.TestCase):
    def test_metrics_are_aggregated_and_rates_are_bounded(self):
        events = [
            synthetic_event(f"delivery-{index}", f"U00{index}", "delivered")
            for index in range(1, 6)
        ]
        events.extend(
            [
                synthetic_event("click-1", "U001", "clicked"),
                synthetic_event("click-2", "U001", "clicked"),
                synthetic_event("click-3", "U002", "clicked"),
                synthetic_event("report-1", "U003", "reported"),
                synthetic_event("open-1", "U001", "opened"),
                synthetic_event("open-2", "U002", "opened"),
            ]
        )

        summary = hrm.summarize_events(events, "HHL02-A")
        run = summary["runs"][0]

        self.assertEqual(run["participant_count"], 5)
        self.assertEqual(run["delivery_count"], 5)
        self.assertEqual(run["click_event_count"], 3)
        self.assertEqual(run["unique_clickers"], 2)
        self.assertEqual(run["click_rate_pct"], 40.0)
        self.assertEqual(run["unique_reporters"], 1)
        self.assertEqual(run["report_rate_pct"], 20.0)
        self.assertEqual(run["open_rate_pct"], 40.0)

    def test_small_cohorts_are_suppressed_without_run_or_person_identifiers(self):
        events = [
            synthetic_event(f"delivery-{index}", f"U00{index}", "delivered")
            for index in range(1, 5)
        ]

        summary = hrm.summarize_events(events, "HHL02-A")
        serialized = json.dumps(summary)

        self.assertEqual(summary["minimum_cohort_size"], 5)
        self.assertEqual(summary["suppressed_run_count"], 1)
        self.assertEqual(summary["runs"], [])
        self.assertNotIn("run-1", serialized)
        self.assertNotIn("U001", serialized)
        self.assertNotIn("user_id", serialized)

    def test_campaigns_are_isolated_in_aggregation(self):
        events = [
            synthetic_event(f"delivery-{index}", f"U00{index}", "delivered", campaign="HHL02-B")
            for index in range(1, 6)
        ]

        summary = hrm.summarize_events(events, "HHL02-A")

        self.assertEqual(summary["runs"], [])
        self.assertEqual(summary["suppressed_run_count"], 0)

    def test_service_reads_telemetry_only(self):
        source = (ROOT / "apps" / "hrm" / "hrm.py").read_text(encoding="utf-8")
        self.assertIn("mode=ro", source)
        self.assertNotIn(".commit(", source)
        self.assertNotIn("INSERT INTO", source)
        self.assertNotIn("UPDATE ", source)
        self.assertNotIn("DELETE FROM", source)

    def test_hrm_service_port_is_loopback_bound(self):
        compose = (ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn('"127.0.0.1:8098:8098"', compose)


if __name__ == "__main__":
    unittest.main()
