import json
import time
from http.client import RemoteDisconnected
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


BASE_URL = "http://127.0.0.1:8080"
LOCAL_OPENER = build_opener(ProxyHandler({}))


def request(path, method="GET", payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    req = Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    with LOCAL_OPENER.open(req, timeout=5) as response:
        content_type = response.headers.get("Content-Type", "")
        result = response.read()
        if "application/json" in content_type:
            return json.loads(result)
        return result.decode("utf-8")


def wait_for_dashboard():
    deadline = time.monotonic() + 120
    last_error = None
    while time.monotonic() < deadline:
        try:
            request("/health")
            return
        except (HTTPError, URLError, TimeoutError, RemoteDisconnected) as exc:
            last_error = exc
            time.sleep(2)
    raise RuntimeError(f"Dashboard did not become ready: {last_error}")


def main():
    wait_for_dashboard()

    page = request("/")
    if "Enviar campaña sintética" not in page:
        raise AssertionError("Dashboard page is missing its campaign workflow")

    campaigns = request("/api/campaigns")
    if not campaigns or campaigns[0]["id"] != "HHL02-A":
        raise AssertionError("Expected the configured synthetic campaign")

    challenges = request("/api/ctf/challenges")
    if len(challenges) != 4:
        raise AssertionError("Expected all four CTF challenges")

    score = request("/api/ctf/score?player=CI-SMOKE")
    if score["score"] != 0:
        raise AssertionError("New smoke-test player should start with zero points")

    sent = request("/api/campaigns/HHL02-A/send", method="POST")
    if sent["delivered"] <= 0:
        raise AssertionError("Synthetic campaign did not reach the local mail sink")

    events = request("/api/campaigns/HHL02-A/events")
    if not any(event["event_type"] == "delivered" for event in events["events"]):
        raise AssertionError("Campaign delivery was not recorded in telemetry")

    assessment_id = "ASM-CI-SMOKE"
    assessment = request(f"/api/assessment?id={assessment_id}")
    if assessment["assessment_id"] != assessment_id:
        raise AssertionError("Assessment endpoint returned an unexpected ID")

    report = request(f"/api/report?id={assessment_id}")
    if report["assessment_id"] != assessment_id:
        raise AssertionError("Report endpoint returned an unexpected ID")

    verification = request(f"/api/verify?id={assessment_id}")
    if verification["status"] != "PASS":
        raise AssertionError(f"Fresh synthetic assessment did not pass: {verification}")

    print("Dashboard smoke test passed: local campaign, CTF, assessment, report and verification.")


if __name__ == "__main__":
    main()
