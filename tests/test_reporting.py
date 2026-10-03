from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class ReportingArtifactsTest(unittest.TestCase):
    def read(self,p): return (ROOT/p).read_text(encoding="utf-8")

    def test_required_artifacts_exist(self):
        for p in ["apps/reporting/reporting.py","apps/reporting/Dockerfile","docs/REPORTING.md","exercises/phase-07/HHL-07.md"]:
            self.assertTrue((ROOT/p).exists(),p)

    def test_loopback_and_port(self):
        c=self.read("infra/docker-compose.yml")
        self.assertIn("127.0.0.1:8094:8094",c)
        self.assertIn("reporting-data:",c)

    def test_assessment_boundary_is_read_only(self):
        c=self.read("infra/docker-compose.yml")
        self.assertIn("assessment-data:/assessment:ro",c)
        s=self.read("apps/reporting/reporting.py")
        self.assertIn("?mode=ro",s)
        self.assertNotIn("UPDATE findings",s)
        self.assertNotIn("INSERT INTO findings",s)
        self.assertNotIn("DELETE FROM findings",s)

    def test_audit_is_append_only(self):
        s=self.read("apps/reporting/reporting.py")
        self.assertIn("audit_no_update",s)
        self.assertIn("audit_no_delete",s)
        self.assertIn("INSERT INTO audit",s)
        self.assertNotIn("UPDATE audit",s)
        self.assertNotIn("DELETE FROM audit",s)

    def test_no_ctf_or_external_messaging_dependency(self):
        s=self.read("apps/reporting/reporting.py")
        self.assertNotIn("HHL-CTF",s)
        self.assertNotIn("requests.",s)
        self.assertNotIn("smtplib",s)

    def test_export_and_evidence_features(self):
        s=self.read("apps/reporting/reporting.py")
        for token in ["REPORT_GENERATED","evidence_index","residual_risk_register","json_path","markdown_path"]:
            self.assertIn(token,s)
        self.assertIn("hashlib.sha256",s)

if __name__=="__main__":
    unittest.main()
