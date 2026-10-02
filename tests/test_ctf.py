import unittest
from pathlib import Path
import tempfile

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
