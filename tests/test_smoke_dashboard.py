import unittest
from unittest.mock import patch

from smoke_dashboard import click_training_link, derive_flag, message_links_for_run


class DashboardSmokeHelpersTest(unittest.TestCase):
    def test_message_links_are_scoped_to_the_requested_local_run(self):
        response = {
            "items": [
                {
                    "Content": {
                        "Body": "\n".join(
                            [
                                "http://127.0.0.1:8080/training/click?campaign=HHL02-A&user=U001&run=run-1&token=synthetic",
                                "http://127.0.0.1:8080/training/click?campaign=HHL02-A&user=U002&run=run-2&token=other",
                                "https://example.invalid/training/click?campaign=HHL02-A&user=U003&run=run-1&token=external",
                            ]
                        )
                    }
                }
            ]
        }
        with patch("smoke_dashboard.request", return_value=response) as get:
            links = message_links_for_run("run-1")

        self.assertEqual(
            links,
            {
                "U001": "/training/click?campaign=HHL02-A&user=U001&run=run-1&token=synthetic"
            },
        )
        get.assert_called_once_with(
            "/api/v2/messages?limit=100", base_url="http://127.0.0.1:8025"
        )

    def test_message_links_decode_quoted_printable_wrapped_urls(self):
        encoded_body = (
            "Training link:\r\n"
            "http://127.0.0.1:8080/training/click?campaign=3DHHL02-A"
            "\u0026user=3DU001\u0026run=3Drun-1\u0026token=3Dsynthetic=\r\n"
            "token\r\n"
        )
        response = {
            "items": [
                {
                    "Content": {
                        "Headers": {
                            "Content-Transfer-Encoding": ["quoted-printable"]
                        },
                        "Body": encoded_body,
                    }
                }
            ]
        }
        with patch("smoke_dashboard.request", return_value=response):
            links = message_links_for_run("run-1")

        self.assertEqual(
            links["U001"],
            "/training/click?campaign=HHL02-A&user=U001&run=run-1&token=synthetictoken",
        )

    def test_derived_flags_are_deterministic_and_material_bound(self):
        first = derive_flag("HHL-CTF-01", "run-123")
        self.assertEqual(first, derive_flag("HHL-CTF-01", "run-123"))
        self.assertNotEqual(first, derive_flag("HHL-CTF-01", "run-456"))
        self.assertTrue(first.startswith("HHL{01_"))

    def test_training_link_must_record_a_click(self):
        with patch(
            "smoke_dashboard.request",
            return_value="Event status: <strong>recorded</strong>",
        ):
            click_training_link("/training/click?token=synthetic")

        with patch(
            "smoke_dashboard.request",
            return_value="Event status: <strong>not-recorded</strong>",
        ):
            with self.assertRaises(AssertionError):
                click_training_link("/training/click?token=invalid")


if __name__ == "__main__":
    unittest.main()
