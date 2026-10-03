from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class VerificationArtifactsTest(unittest.TestCase):
 def read(self,p): return (ROOT/p).read_text(encoding="utf-8")
 def test_artifacts(self):
  for p in ["apps/verification/verification.py","apps/verification/Dockerfile","docs/VERIFICATION.md","exercises/phase-08/HHL-08.md"]: self.assertTrue((ROOT/p).exists(),p)
 def test_loopback(self):
  c=self.read("infra/docker-compose.yml"); self.assertIn("127.0.0.1:8095:8095",c); self.assertIn("verification-data:",c)
 def test_read_only_boundaries(self):
  c=self.read("infra/docker-compose.yml"); self.assertIn("assessment-data:/assessment:ro",c); self.assertIn("reporting-data:/reporting:ro",c)
  s=self.read("apps/verification/verification.py"); self.assertIn("?mode=ro",s); self.assertNotIn("INSERT INTO findings",s); self.assertNotIn("UPDATE findings",s); self.assertNotIn("DELETE FROM findings",s)
 def test_controls_and_gate(self):
  s=self.read("apps/verification/verification.py")
  for x in ["HHL-V001","HHL-V002","HHL-V003","HHL-V004","content_hash","status=\"PASS\" if not failed"]:
   self.assertIn(x,s)
if __name__=="__main__": unittest.main()
