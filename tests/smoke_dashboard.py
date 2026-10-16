import hashlib
import json
import quopri
import time
from http.client import RemoteDisconnected
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import ProxyHandler, Request, build_opener


BASE_URL = "http://127.0.0.1:8080"
MAILHOG_URL = "http://127.0.0.1:8025"
LOCAL_OPENER = build_opener(ProxyHandler({}))


def request(path, method="GET", payload=None, base_url=BASE_URL):
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    req = Request(f"{base_url}{path}", data=body, headers=headers, method=method)
    with LOCAL_OPENER.open(req, timeout=5) as response:
        content_type = response.headers.get("Content-Type", "")
        result = response.read()
        if "json" in content_type.lower():
            return json.loads(result)
        return result.decode("utf-8")


def message_links_for_run(run_id):
    messages = request("/api/v2/messages?limit=100", base_url=MAILHOG_URL)
    links = {}
    expected_prefix = f"{BASE_URL}/training/click?"
    for message in messages["items"]:
        content = message["Content"]
        body = content["Body"]
        transfer_encoding = content.get("Headers", {}).get(
            "Content-Transfer-Encoding", [""]
        )[0]
        if transfer_encoding.lower() == "quoted-printable":
            body = quopri.decodestring(body.encode("utf-8")).decode("utf-8")
        for line in body.splitlines():
            link = line.strip()
            if not link.startswith(expected_prefix):
                continue
            parsed = urlsplit(link)
            query = parse_qs(parsed.query)
            if query.get("run") != [run_id] or len(query.get("user", [])) != 1:
                continue
            links[query["user"][0]] = f"{parsed.path}?{parsed.query}"
    return links


def click_training_link(path):
    result = request(path)
    if "Event status: <strong>recorded</strong>" not in result:
        raise AssertionError("Synthetic MailHog link did not record a training click")


def derive_flag(challenge_id, material):
    number = challenge_id.rsplit("-", 1)[-1]
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:12]
    return f"HHL{{{number}_{digest}}}"


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
    if (
        "Enviar campaña sintética" not in page
        or "Buscar en fuentes sintéticas" not in page
        or "Analizar ejemplo" not in page
        or "Actualizar métricas agregadas" not in page
        or "Registrar triage" not in page
        or "Confirmar alcance local" not in page
        or "Ruta curricular integrada" not in page
    ):
        raise AssertionError("Dashboard page is missing its campaign workflow")

    scenarios = request("/api/red-team/scenarios")
    if len(scenarios) != 1 or scenarios[0]["campaign_id"] != "HHL02-A":
        raise AssertionError("Expected the single preauthorized synthetic Red Team scenario")
    if not scenarios[0]["stop_conditions"] or not scenarios[0]["prohibited_actions"]:
        raise AssertionError("Red Team scenario is missing safety boundaries")

    curriculum = request("/api/curriculum/path")
    curriculum_ids = {module["id"] for module in curriculum["modules"]}
    if curriculum["progress_mode"] != "local_self_reported" or len(curriculum_ids) != 10:
        raise AssertionError("Expected the complete integrated self-reported learning path")

    appsec_modules = request("/api/appsec/modules")
    if len(appsec_modules) != 3:
        raise AssertionError("Expected all three bundled AppSec code examples")
    sql_review = request("/api/appsec/analyze?id=APPSEC-01")
    if [finding["rule_id"] for finding in sql_review["findings"]] != ["APPSEC-R001"]:
        raise AssertionError("AppSec did not identify the interpolated SQL fixture")
    fixed_review = request("/api/appsec/analyze?id=APPSEC-03")
    if not fixed_review["secure"] or fixed_review["findings"]:
        raise AssertionError("Remediated AppSec fixture should pass static rules")

    osint_search = request("/api/osint/search?q=analyst-amber")
    if osint_search["result_count"] != 3:
        raise AssertionError("Synthetic OSINT search did not return correlated sources")
    if any(source["confidence"] != "SIMULATED" for source in osint_search["results"]):
        raise AssertionError("OSINT results must be marked as simulated")

    campaigns = request("/api/campaigns")
    if not campaigns or campaigns[0]["id"] != "HHL02-A":
        raise AssertionError("Expected the configured synthetic campaign")

    challenges = request("/api/ctf/challenges")
    challenge_ids = [challenge["id"] for challenge in challenges]
    if challenge_ids != ["HHL-CTF-01", "HHL-CTF-02", "HHL-CTF-03", "HHL-CTF-04"]:
        raise AssertionError("Expected all four CTF challenges")

    sent = request("/api/campaigns/HHL02-A/send", method="POST")
    if sent["delivered"] != 5:
        raise AssertionError("Expected all five synthetic campaign messages")

    links = message_links_for_run(sent["run_id"])
    if len(links) != sent["delivered"]:
        raise AssertionError("MailHog did not expose one local training link per user")

    for link in links.values():
        click_training_link(link)
    repeated_user = sorted(links)[0]
    for _ in range(3):
        click_training_link(links[repeated_user])

    events = request("/api/campaigns/HHL02-A/events")
    run_events = [
        event for event in events["events"]
        if event["correlation_id"] == sent["run_id"]
    ]
    if not any(event["event_type"] == "delivered" for event in run_events):
        raise AssertionError("Campaign delivery was not recorded in telemetry")
    clicks = [event for event in run_events if event["event_type"] == "clicked"]
    clicks_by_user = {}
    for event in clicks:
        clicks_by_user.setdefault(event["user_id"], []).append(event["event_id"])
    if len(clicks_by_user) < 5 or len(clicks_by_user[repeated_user]) <= 3:
        raise AssertionError("Synthetic clicks did not satisfy both detection thresholds")

    hrm_summary = request("/api/hrm/summary?campaign=HHL02-A")
    current_hrm_run = next(
        run for run in hrm_summary["runs"]
        if run["correlation_id"] == sent["run_id"]
    )
    if current_hrm_run["participant_count"] != 5 or current_hrm_run["click_rate_pct"] != 100.0:
        raise AssertionError("HRM summary should expose only aggregate synthetic metrics")
    if "user_id" in json.dumps(hrm_summary) or "U001" in json.dumps(hrm_summary):
        raise AssertionError("HRM summary must not expose person-level identifiers")

    hunts = request("/api/hunts?campaign=HHL02-A")["hypotheses"]
    compound_hunt = next(hunt for hunt in hunts if hunt["hunt_id"] == "HHL-H003")
    if not any(match["correlation_id"] == sent["run_id"] for match in compound_hunt["matches"]):
        raise AssertionError("Threat hunt did not find the compound synthetic incident")

    timeline = request(f"/api/timeline?run={sent['run_id']}")
    if timeline["event_count"] != 13 or len(timeline["events"]) != 13:
        raise AssertionError("DFIR timeline is missing the campaign and click events")
    timestamps = [event["timestamp"] for event in timeline["events"]]
    if timestamps != sorted(timestamps):
        raise AssertionError("DFIR timeline is not chronological")

    alerts = request("/api/alerts?campaign=HHL02-A")["alerts"]
    alert_rules = {alert["rule_id"] for alert in alerts
                   if alert["correlation_id"] == sent["run_id"]}
    if not {"HHL-D001", "HHL-D002"}.issubset(alert_rules):
        raise AssertionError("Expected both deterministic detection rules to alert")

    current_alerts = [
        alert for alert in alerts if alert["correlation_id"] == sent["run_id"]
    ]
    if any(not alert.get("evidence_event_ids") for alert in current_alerts):
        raise AssertionError("Blue Team alerts must carry supporting event IDs")
    for alert in current_alerts:
        triage = request(
            "/api/triage",
            method="POST",
            payload={
                "campaign_id": alert["campaign_id"],
                "alert_id": alert["alert_id"],
                "decision": "VALIDATED_SYNTHETIC_ACTIVITY",
            },
        )
        if triage["status"] != "recorded":
            raise AssertionError("Blue Team triage disposition was not recorded")
    triage_records = request("/api/triage?campaign=HHL02-A")["records"]
    current_triage = [
        record for record in triage_records
        if record["correlation_id"] == sent["run_id"]
    ]
    if len(current_triage) != len(current_alerts) or any(
        not record["evidence_event_ids"] for record in current_triage
    ):
        raise AssertionError("Blue Team triage history is missing alert evidence")

    player_id = f"CI-{sent['run_id'].replace('-', '')[:24]}"
    if request(f"/api/ctf/score?player={player_id}")["score"] != 0:
        raise AssertionError("New smoke-test player should start with zero points")

    repeated_candidates = sorted(
        (user_id, event_ids)
        for user_id, event_ids in clicks_by_user.items()
        if len(event_ids) > 3
    )
    unique_users = sorted(clicks_by_user)
    all_click_ids = sorted(event["event_id"] for event in clicks)
    materials = [
        sent["run_id"],
        f"{sent['run_id']}|{repeated_candidates[0][0]}|"
        f"{','.join(sorted(repeated_candidates[0][1]))}",
        f"{sent['run_id']}|{','.join(unique_users)}",
        f"{sent['run_id']}|{','.join(all_click_ids)}",
    ]
    for challenge_id, material in zip(challenge_ids, materials):
        result = request(
            "/api/ctf/submit",
            method="POST",
            payload={
                "player_id": player_id,
                "challenge_id": challenge_id,
                "flag": derive_flag(challenge_id, material),
            },
        )
        if result["status"] != "accepted":
            raise AssertionError(f"CTF challenge was not accepted: {challenge_id}")
    score = request(f"/api/ctf/score?player={player_id}")
    if score["score"] != 700 or len(score["completed"]) != 4:
        raise AssertionError("Smoke-test learner did not complete all CTF challenges")

    assessment_id = f"ASM-CI-{sent['run_id'][:16]}"
    assessment = request(f"/api/assessment?id={assessment_id}")
    if assessment["assessment_id"] != assessment_id:
        raise AssertionError("Assessment endpoint returned an unexpected ID")
    if not {
        "HHL-F001", "HHL-F002"
    }.issubset({finding["template_id"] for finding in assessment["findings"]}):
        raise AssertionError("Assessment did not derive both evidence-backed findings")

    for finding in assessment["findings"]:
        for action_type, status in (
            ("REMEDIATION", "PLANNED"),
            ("REMEDIATION", "VERIFIED"),
            ("RETEST", "VERIFIED"),
        ):
            action = request(
                "/api/actions",
                method="POST",
                payload={
                    "finding_id": finding["finding_id"],
                    "action_type": action_type,
                    "status": status,
                    "description": f"CI synthetic {action_type.lower()} evidence",
                    "evidence": {"source": "local-smoke", "status": status},
                },
            )
            if action["status"] != "recorded":
                raise AssertionError("Assessment action was not persisted")

    report = request(f"/api/report?id={assessment_id}")
    if report["assessment_id"] != assessment_id:
        raise AssertionError("Report endpoint returned an unexpected ID")
    if len(report["remediation_tracking"]) != len(assessment["findings"]) * 3:
        raise AssertionError("Report is missing the synthetic remediation/retest history")

    verification = request(f"/api/verify?id={assessment_id}")
    if verification["status"] != "PASS":
        raise AssertionError(f"Fresh synthetic assessment did not pass: {verification}")
    if any(check["status"] != "PASS" for check in verification["checks"]):
        raise AssertionError("Verification contains a failed control")

    print(
        "Dashboard smoke test passed: local campaign and MailHog clicks, "
        "detection, Blue Team triage and threat hunts, DFIR timeline, "
        "OSINT, AppSec, HRM, all CTF challenges, "
        "assessment actions, report and verification."
    )


if __name__ == "__main__":
    main()
