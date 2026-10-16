import json
import logging
import os
import re
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

LAB_NAME = os.getenv("LAB_NAME", "Human Hacking Lab")
SIMULATOR_URL = os.getenv("SIMULATOR_URL", "http://simulator:8090")
SERVICE_URLS = {
    "simulator": SIMULATOR_URL,
    "detection": os.getenv("DETECTION_URL", "http://detection:8091"),
    "ctf": os.getenv("CTF_URL", "http://ctf:8092"),
    "assessment": os.getenv("ASSESSMENT_URL", "http://assessment:8093"),
    "reporting": os.getenv("REPORTING_URL", "http://reporting:8094"),
    "verification": os.getenv("VERIFICATION_URL", "http://verification:8095"),
}
PAGE_PATH = Path(__file__).with_name("index.html")
MAX_REQUEST_BYTES = 16_384
MAX_RESPONSE_BYTES = 2_097_152
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
PLAYER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$")
LOGGER = logging.getLogger("hhl-web")


def _single_query_value(query, key, pattern=ID_PATTERN):
    values = query.get(key, [])
    if len(values) != 1 or not pattern.fullmatch(values[0]):
        return None
    return values[0]


def resolve_api_request(method, path, query_string=""):
    query = parse_qs(query_string, keep_blank_values=True)

    if method == "GET":
        exact_routes = {
            "/api/campaigns": ("simulator", "/campaigns"),
            "/api/ctf/challenges": ("ctf", "/challenges"),
            "/api/ctf/score": ("ctf", "/score"),
            "/api/assessment": ("assessment", "/assessments"),
            "/api/report": ("reporting", "/reports"),
            "/api/verify": ("verification", "/verify"),
        }
        if path in exact_routes:
            service, target = exact_routes[path]
            if path == "/api/ctf/score":
                player = _single_query_value(query, "player", PLAYER_PATTERN)
                if player is None:
                    return None
                return service, f"{target}?{urlencode({'player': player})}"
            if path in {"/api/assessment", "/api/report", "/api/verify"}:
                assessment_id = _single_query_value(query, "id")
                if assessment_id is None:
                    return None
                return service, f"{target}?{urlencode({'id': assessment_id})}"
            return service, target

        if path == "/api/alerts":
            campaign_id = _single_query_value(query, "campaign")
            if campaign_id is None:
                return None
            return "detection", f"/alerts?{urlencode({'campaign': campaign_id})}"

        campaign_match = re.fullmatch(
            r"/api/campaigns/([A-Za-z0-9][A-Za-z0-9_-]{0,63})/(summary|events)",
            path,
        )
        if campaign_match:
            campaign_id, resource = campaign_match.groups()
            suffix = "summary" if resource == "summary" else "events?limit=100"
            return "simulator", f"/campaigns/{campaign_id}/{suffix}"

        hint_match = re.fullmatch(
            r"/api/ctf/challenges/([A-Za-z0-9][A-Za-z0-9_-]{0,63})/hint",
            path,
        )
        if hint_match:
            challenge_id = hint_match.group(1)
            return "ctf", f"/challenges/{challenge_id}/hint"

    if method == "POST":
        campaign_match = re.fullmatch(
            r"/api/campaigns/([A-Za-z0-9][A-Za-z0-9_-]{0,63})/send",
            path,
        )
        if campaign_match:
            return "simulator", f"/campaigns/{campaign_match.group(1)}/send"

        post_routes = {
            "/api/ctf/submit": ("ctf", "/submit"),
            "/api/actions": ("assessment", "/actions"),
        }
        return post_routes.get(path)

    return None


def record_click(query):
    payload = {
        "campaign_id": query.get("campaign", [""])[0],
        "user_id": query.get("user", [""])[0],
        "token": query.get("token", [""])[0],
        "event_type": "clicked",
        "correlation_id": query.get("run", [""])[0],
    }
    if not all(payload.values()):
        return False

    request = Request(
        f"{SIMULATOR_URL}/events",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=3) as response:
            return response.status == 201
    except HTTPError as exc:
        LOGGER.warning("Training interaction was rejected by simulator: %s", exc.code)
        return False
    except (URLError, TimeoutError) as exc:
        LOGGER.error("Unable to record training interaction: %s", exc)
        return False


class Handler(BaseHTTPRequestHandler):
    def html(self, status, body):
        raw = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def json_response(self, status, payload):
        raw = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def proxy(self, method, path, query_string="", body=None):
        resolved = resolve_api_request(method, path, query_string)
        if resolved is None:
            return self.json_response(404, {"error": "not_found"})

        service, target = resolved
        headers = {"Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = Request(
            f"{SERVICE_URLS[service]}{target}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=8) as response:
                status = response.status
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except HTTPError as exc:
            status = exc.code
            raw = exc.read(MAX_RESPONSE_BYTES + 1)
        except (URLError, TimeoutError) as exc:
            LOGGER.error("Dashboard request to %s failed: %s", service, exc)
            return self.json_response(
                503, {"error": "service_unavailable", "service": service}
            )

        if len(raw) > MAX_RESPONSE_BYTES:
            return self.json_response(502, {"error": "service_response_too_large"})
        try:
            payload = json.loads(raw or b"{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            LOGGER.error("Service %s returned an invalid JSON response", service)
            return self.json_response(502, {"error": "invalid_service_response"})
        return self.json_response(status, payload)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            try:
                page = PAGE_PATH.read_text(encoding="utf-8")
            except OSError as exc:
                LOGGER.error("Dashboard page could not be read: %s", exc)
                return self.html(500, "<h1>Dashboard unavailable</h1>")
            return self.html(200, page.replace("{{LAB_NAME}}", escape(LAB_NAME)))

        if parsed.path == "/health":
            return self.json_response(200, {"status": "ok", "service": "hhl-web"})

        if parsed.path.startswith("/api/"):
            return self.proxy("GET", parsed.path, parsed.query)

        if parsed.path == "/training/click":
            query = parse_qs(parsed.query)
            recorded = record_click(query)
            state = "recorded" if recorded else "not-recorded"
            return self.html(
                200,
                f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Training Complete</title></head>
<body>
<h1>Human Hacking Lab</h1>
<h2>Training interaction detected</h2>
<p>Event status: <strong>{state}</strong></p>
<p>This is a controlled training page. No credentials are requested or stored.</p>
<p>Return to MailHog and inspect the synthetic message.</p>
</body>
</html>""",
            )

        return self.html(
            200,
            f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{LAB_NAME}</title>
</head>
<body>
  <h1>{LAB_NAME}</h1>
  <p>Educational portal for an isolated cybersecurity training lab.</p>
  <p>This service does not process credentials.</p>
  <ul>
    <li>Identities: synthetic</li>
    <li>Data: synthetic</li>
    <li>Scope: local lab</li>
  </ul>
</body>
</html>""",
        )

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))

    def do_POST(self):
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/"):
            return self.json_response(404, {"error": "not_found"})

        if resolve_api_request("POST", parsed.path) is None:
            return self.json_response(404, {"error": "not_found"})

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.json_response(400, {"error": "invalid_content_length"})
        if content_length < 0 or content_length > MAX_REQUEST_BYTES:
            return self.json_response(413, {"error": "payload_too_large"})

        body = self.rfile.read(content_length) if content_length else None
        if body:
            try:
                payload = json.loads(body)
            except (UnicodeDecodeError, json.JSONDecodeError):
                return self.json_response(400, {"error": "invalid_json"})
            if not isinstance(payload, dict):
                return self.json_response(400, {"error": "invalid_payload"})

        return self.proxy("POST", parsed.path, body=body)


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
