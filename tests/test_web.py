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

    def test_unknown_routes_and_methods_are_not_proxyable(self):
        self.assertIsNone(resolve_api_request("GET", "/api/proxy/http://example.com"))
        self.assertIsNone(resolve_api_request("DELETE", "/api/actions"))
        self.assertIsNone(
            resolve_api_request("GET", "/api/campaigns/HHL02-A/send")
        )


if __name__ == "__main__":
    unittest.main()
