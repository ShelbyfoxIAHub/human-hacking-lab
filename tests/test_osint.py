import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "apps" / "osint"))
import osint


class SyntheticOsintTest(unittest.TestCase):
    def test_search_correlates_only_bundled_synthetic_sources(self):
        result = osint.search_sources("analyst-amber")

        self.assertEqual(result["dataset_id"], "OSINT-HHL-SYNTH-01")
        self.assertEqual(result["result_count"], 3)
        self.assertEqual(
            [source["source_id"] for source in result["results"]],
            ["OSINT-SRC-003", "OSINT-SRC-004", "OSINT-SRC-005"],
        )
        self.assertTrue(
            all(
                "SYN-PERSON-001" in source["related_entity_ids"]
                for source in result["results"]
            )
        )
        self.assertTrue(
            all(
                source["confidence"] == "SIMULATED"
                and source["collection_method"]
                for source in result["results"]
            )
        )

    def test_domain_search_returns_multiple_provenance_records(self):
        result = osint.search_sources("staging.northstar-lab.invalid")

        self.assertEqual(result["result_count"], 2)
        self.assertEqual(
            {source["source_type"] for source in result["results"]},
            {"simulated_dns", "simulated_repository"},
        )

    def test_query_validation_rejects_external_target_syntax(self):
        for query in ("", "https://example.com", "../private", "x" * 81, "bad\nquery"):
            with self.subTest(query=query):
                with self.assertRaisesRegex(ValueError, "invalid_query"):
                    osint.search_sources(query)

    def test_catalog_uses_reserved_synthetic_domains_and_no_network_client(self):
        for source in osint.SOURCE_CATALOG["sources"]:
            self.assertTrue(source["uri"].split("/", 1)[0].endswith(".invalid"))
        implementation = (
            ROOT / "apps" / "osint" / "osint.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("urlopen(", implementation)
        self.assertNotIn("requests.get(", implementation)

    def test_osint_service_port_is_loopback_bound(self):
        compose = (ROOT / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn('"127.0.0.1:8096:8096"', compose)


if __name__ == "__main__":
    unittest.main()
