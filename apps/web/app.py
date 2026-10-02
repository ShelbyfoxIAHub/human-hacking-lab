from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

LAB_NAME = os.getenv("LAB_NAME", "Human Hacking Lab")
SIMULATOR_URL = os.getenv("SIMULATOR_URL", "http://simulator:8090")


def record_click(query):
    payload = {
        "campaign_id": query.get("campaign", [""])[0],
        "user_id": query.get("user", [""])[0],
        "token": query.get("token", [""])[0],
        "event_type": "clicked",
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
    except Exception:
        return False


class Handler(BaseHTTPRequestHandler):
    def html(self, status, body):
        raw = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        parsed = urlparse(self.path)

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


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
