import unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
class AssessmentArtifactsTest(unittest.TestCase):
 def test_artifacts(self):
  for p in ["apps/assessment/assessment.py","apps/assessment/Dockerfile","docs/ASSESSMENT.md","exercises/phase-06/HHL-06.md"]:
   self.assertTrue((ROOT/p).exists(),p)
 def test_loopback(self):
  c=(ROOT/"infra/docker-compose.yml").read_text()
  self.assertIn('"127.0.0.1:8093:8093"',c)
 def test_read_only_telemetry(self):
  s=(ROOT/"apps/assessment/assessment.py").read_text()
  self.assertIn("mode=ro",s); self.assertNotIn("INSERT INTO events",s); self.assertNotIn("DELETE FROM events",s)
 def test_ctf_not_used_for_risk(self):
  s=(ROOT/"apps/assessment/assessment.py").read_text().lower()
  self.assertNotIn("leaderboard",s); self.assertNotIn("ctf",s)
 def test_residual_requires_verified_remediation(self):
  s=(ROOT/"apps/assessment/assessment.py").read_text()
  self.assertIn("action_type='REMEDIATION' AND status='VERIFIED'",s)
