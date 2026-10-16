import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "apps" / "appsec"))
import appsec


class AppsecStaticAnalysisTest(unittest.TestCase):
    def test_bundled_sql_fixture_reports_parameterization_finding(self):
        result = appsec.analyze_module("APPSEC-01")

        self.assertFalse(result["secure"])
        self.assertEqual(
            [finding["rule_id"] for finding in result["findings"]],
            ["APPSEC-R001"],
        )
        self.assertEqual(result["findings"][0]["line"], 2)
        self.assertIn("email = ?", result["remediated_code"])
        self.assertIn("never executed", result["analysis_mode"])

    def test_bundled_dom_fixture_reports_text_rendering_finding(self):
        result = appsec.analyze_module("APPSEC-02")

        self.assertEqual(
            [finding["rule_id"] for finding in result["findings"]],
            ["APPSEC-R002"],
        )
        self.assertIn("textContent", result["remediated_code"])

    def test_remediated_fixture_has_no_static_findings(self):
        result = appsec.analyze_module("APPSEC-03")

        self.assertTrue(result["secure"])
        self.assertEqual(result["findings"], [])

    def test_only_known_module_ids_can_be_analyzed(self):
        with self.assertRaisesRegex(ValueError, "invalid_module_id"):
            appsec.analyze_module("../outside")
        with self.assertRaisesRegex(KeyError, "unknown_module"):
            appsec.analyze_module("APPSEC-99")

    def test_service_does_not_execute_or_accept_arbitrary_code(self):
        source = (ROOT / "apps" / "appsec" / "appsec.py").read_text(encoding="utf-8")
        self.assertNotIn("exec(", source)
        self.assertNotIn("eval(", source)
        self.assertNotIn("do_POST", source)

    def test_appsec_service_port_is_loopback_bound(self):
        compose = (ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn('"127.0.0.1:8097:8097"', compose)


if __name__ == "__main__":
    unittest.main()
