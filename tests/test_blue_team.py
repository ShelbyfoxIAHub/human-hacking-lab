import json
import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "apps" / "blue_team"))
import blue_team


class BlueTeamTriageTest(unittest.TestCase):
    def setUp(self):
        self.db = blue_team.initialize_database(sqlite3.connect(":memory:"))
        self.alert = {
            "alert_id": "HHL-D002-HHL02-A-run-1",
            "campaign_id": "HHL02-A",
            "correlation_id": "run-1",
            "rule_id": "HHL-D002",
            "evidence_event_ids": ["event-2", "event-1", "event-2"],
            "user_id": "U001",
        }

    def tearDown(self):
        self.db.close()

    def test_triage_record_is_evidence_linked_and_omits_person_identifiers(self):
        record = blue_team.persist_triage(
            self.db, self.alert, "VALIDATED_SYNTHETIC_ACTIVITY"
        )
        records = blue_team.records_for_campaign(self.db, "HHL02-A")
        serialized = json.dumps(records)

        self.assertEqual(record["evidence_event_ids"], ["event-1", "event-2"])
        self.assertEqual(len(records), 1)
        self.assertNotIn("user_id", serialized)
        self.assertNotIn("U001", serialized)

    def test_triage_history_is_append_only(self):
        record = blue_team.persist_triage(
            self.db, self.alert, "RULE_REVIEW_RECOMMENDED"
        )

        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "UPDATE triage_records SET decision='ESCALATED_TO_INSTRUCTOR' WHERE record_id=?",
                (record["record_id"],),
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "DELETE FROM triage_records WHERE record_id=?",
                (record["record_id"],),
            )

    def test_invalid_decisions_and_missing_evidence_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_decision"):
            blue_team.persist_triage(self.db, self.alert, ["not", "a", "decision"])
        with self.assertRaisesRegex(ValueError, "alert_evidence_missing"):
            blue_team.persist_triage(
                self.db,
                {**self.alert, "evidence_event_ids": []},
                "VALIDATED_SYNTHETIC_ACTIVITY",
            )

    def test_triage_service_does_not_write_to_telemetry(self):
        source = (ROOT / "apps" / "blue_team" / "blue_team.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("INSERT INTO events", source)
        self.assertNotIn("UPDATE events", source)
        self.assertNotIn("DELETE FROM events", source)

    def test_blue_team_service_port_is_loopback_bound(self):
        compose = (ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn('"127.0.0.1:8099:8099"', compose)


if __name__ == "__main__":
    unittest.main()
