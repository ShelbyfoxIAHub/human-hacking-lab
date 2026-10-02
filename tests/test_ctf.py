import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


class CTFArtifactsTest(unittest.TestCase):
    def test_ctf_rules_are_documented(self):
        source = (ROOT / "apps" / "ctf" / "ctf.py").read_text(encoding="utf-8")
        docs = (ROOT / "docs" / "CTF-RULES.md").read_text(encoding="utf-8")
        for challenge in ("HHL-CTF-01", "HHL-CTF-02", "HHL-CTF-03", "HHL-CTF-04"):
            self.assertIn(challenge, source)
            self.assertIn(challenge, docs)

    def test_ctf_is_loopback_bound(self):
        compose = (ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn('"127.0.0.1:8092:8092"', compose)

    def test_ctf_reads_telemetry_read_only(self):
        source = (ROOT / "apps" / "ctf" / "ctf.py").read_text(encoding="utf-8")
        self.assertIn("mode=ro", source)
        self.assertNotIn("INSERT INTO events", source)
        self.assertNotIn("UPDATE events", source)
        self.assertNotIn("DELETE FROM events", source)

    def test_flags_are_derived_and_not_hardcoded(self):
        source = (ROOT / "apps" / "ctf" / "ctf.py").read_text(encoding="utf-8")
        self.assertIn("hashlib.sha256", source)
        self.assertIn("flag_for", source)
        self.assertNotIn("HHL{01_", source)

    def test_player_id_is_constrained(self):
        source = (ROOT / "apps" / "ctf" / "ctf.py").read_text(encoding="utf-8")
        self.assertIn("PLAYER_RE", source)
        self.assertIn("invalid_player_id", source)

    def test_flag_format_is_deterministic(self):
        import sys
        sys.path.insert(0, str(ROOT / "apps" / "ctf"))
        import ctf
        self.assertEqual(ctf.flag_for("HHL-CTF-01", "run-123"), ctf.flag_for("HHL-CTF-01", "run-123"))
        self.assertNotEqual(ctf.flag_for("HHL-CTF-01", "run-123"), ctf.flag_for("HHL-CTF-01", "run-456"))

    def test_challenge_material_requires_expected_evidence(self):
        import sys
        sys.path.insert(0, str(ROOT / "apps" / "ctf"))
        import ctf
        import sqlite3

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute(
            "CREATE TABLE events (id TEXT, campaign_id TEXT, user_id TEXT, event_type TEXT, timestamp TEXT, correlation_id TEXT)"
        )
        conn.execute(
            "INSERT INTO events VALUES ('e1','HHL02-A','u1','delivered','2026-10-02T00:00:00Z','run-1')"
        )
        conn.commit()

        self.assertEqual(ctf.challenge_material("HHL-CTF-01", conn), "run-1")
        self.assertIsNone(ctf.challenge_material("HHL-CTF-02", conn))
        conn.close()
