import unittest

from apps.web.app import resolve_api_request


class DashboardProxyRoutesTest(unittest.TestCase):
    def test_dashboard_routes_only_to_configured_services(self):
        self.assertEqual(
            resolve_api_request("GET", "/api/campaigns"),
            ("simulator", "/campaigns"),
        )
        self.assertEqual(
            resolve_api_request("GET", "/api/alerts", "campaign=HHL02-A"),
            ("detection", "/alerts?campaign=HHL02-A"),
        )
        self.assertEqual(
            resolve_api_request("GET", "/api/hunts", "campaign=HHL02-A"),
            ("detection", "/hunts?campaign=HHL02-A"),
        )
        self.assertEqual(
            resolve_api_request("GET", "/api/timeline", "run=run-123"),
            ("detection", "/timeline?run=run-123"),
        )
        self.assertEqual(
            resolve_api_request(
                "GET", "/api/osint/search", "q=analyst-amber"
            ),
            ("osint", "/search?q=analyst-amber"),
        )
        self.assertEqual(
            resolve_api_request("GET", "/api/appsec/modules"),
            ("appsec", "/modules"),
        )
        self.assertEqual(
            resolve_api_request("GET", "/api/appsec/analyze", "id=APPSEC-01"),
            ("appsec", "/analyze?id=APPSEC-01"),
        )
        self.assertEqual(
            resolve_api_request(
                "GET", "/api/hrm/summary", "campaign=HHL02-A"
            ),
            ("hrm", "/summary?campaign=HHL02-A"),
        )
        self.assertEqual(
            resolve_api_request("GET", "/api/triage", "campaign=HHL02-A"),
            ("blueteam", "/records?campaign=HHL02-A"),
        )
        self.assertEqual(
            resolve_api_request("POST", "/api/triage"),
            ("blueteam", "/records"),
        )
        self.assertEqual(
            resolve_api_request("GET", "/api/red-team/scenarios"),
            ("simulator", "/scenarios"),
        )
        self.assertEqual(
            resolve_api_request("POST", "/api/actions"),
            ("assessment", "/actions"),
        )

    def test_campaign_and_assessment_ids_are_forwarded_as_path_or_query_values(self):
        self.assertEqual(
            resolve_api_request("POST", "/api/campaigns/HHL02-A/send"),
            ("simulator", "/campaigns/HHL02-A/send"),
        )
        self.assertEqual(
            resolve_api_request("GET", "/api/verify", "id=ASM-STUDENT-01"),
            ("verification", "/verify?id=ASM-STUDENT-01"),
        )

    def test_missing_or_invalid_parameters_are_rejected(self):
        self.assertIsNone(resolve_api_request("GET", "/api/verify"))
        self.assertIsNone(
            resolve_api_request("GET", "/api/alerts", "campaign=..%2Fother")
        )
        self.assertIsNone(
            resolve_api_request("GET", "/api/ctf/score", "player=bad%20id")
        )
        self.assertIsNone(resolve_api_request("GET", "/api/hunts"))
        self.assertIsNone(
            resolve_api_request("GET", "/api/timeline", "run=..%2Fother")
        )
        self.assertIsNone(resolve_api_request("GET", "/api/osint/search"))
        self.assertIsNone(
            resolve_api_request(
                "GET", "/api/osint/search", "q=https%3A%2F%2Fexample.com"
            )
        )
        self.assertIsNone(
            resolve_api_request(
                "GET", "/api/osint/search", "q=analyst-amber&q=external"
            )
        )
        self.assertIsNone(resolve_api_request("GET", "/api/appsec/analyze"))
        self.assertIsNone(
            resolve_api_request(
                "GET", "/api/appsec/analyze", "id=..%2Fexternal"
            )
        )
        self.assertIsNone(resolve_api_request("GET", "/api/hrm/summary"))
        self.assertIsNone(
            resolve_api_request(
                "GET", "/api/hrm/summary", "campaign=HHL02-A&campaign=HHL02-B"
            )
        )
        self.assertIsNone(resolve_api_request("GET", "/api/triage"))

    def test_unknown_routes_and_methods_are_not_proxyable(self):
        self.assertIsNone(resolve_api_request("GET", "/api/proxy/http://example.com"))
        self.assertIsNone(resolve_api_request("DELETE", "/api/actions"))
        self.assertIsNone(
            resolve_api_request("GET", "/api/campaigns/HHL02-A/send")
        )


if __name__ == "__main__":
    unittest.main()
