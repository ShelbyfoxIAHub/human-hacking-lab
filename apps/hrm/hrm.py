from __future__ import annotations

import json
import os
import re
import sqlite3
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8098"))
DB_PATH = os.getenv("TELEMETRY_DB_PATH", "/telemetry/hhl-simulation.db")
CAMPAIGN_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
MINIMUM_COHORT_SIZE = 5
LIMITATIONS = [
    "Metrics describe synthetic campaign events, not individual people.",
    "Click and report rates are not measures of human risk, competence or learning.",
    "Use aggregate observations to improve training and controls; do not rank learners.",
]


def load_events(campaign_id: str):
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """SELECT id,campaign_id,user_id,event_type,timestamp,correlation_id
               FROM events WHERE campaign_id=? AND correlation_id IS NOT NULL
               ORDER BY timestamp ASC,id ASC""",
            (campaign_id,),
        ).fetchall()
        return [
            {
                "event_id": row["id"],
                "campaign_id": row["campaign_id"],
                "user_id": row["user_id"],
                "event_type": row["event_type"],
                "timestamp": row["timestamp"],
                "correlation_id": row["correlation_id"],
            }
            for row in rows
        ]
    finally:
        conn.close()


def summarize_events(events, campaign_id: str):
    by_run = defaultdict(list)
    for event in events:
        if event["campaign_id"] == campaign_id and event["correlation_id"]:
            by_run[event["correlation_id"]].append(event)

    runs = []
    suppressed_run_count = 0
    for correlation_id, run_events in sorted(by_run.items()):
        participants = {
            event["user_id"]
            for event in run_events
            if event["event_type"] == "delivered"
        }
        participant_count = len(participants)
        if participant_count < MINIMUM_COHORT_SIZE:
            suppressed_run_count += 1
            continue

        click_events = [
            event for event in run_events if event["event_type"] == "clicked"
        ]
        report_events = [
            event for event in run_events if event["event_type"] == "reported"
        ]
        open_events = [
            event for event in run_events if event["event_type"] == "opened"
        ]
        unique_clickers = len({event["user_id"] for event in click_events})
        unique_reporters = len({event["user_id"] for event in report_events})
        unique_openers = len({event["user_id"] for event in open_events})
        runs.append({
            "correlation_id": correlation_id,
            "participant_count": participant_count,
            "delivery_count": sum(
                event["event_type"] == "delivered" for event in run_events
            ),
            "click_event_count": len(click_events),
            "unique_clickers": unique_clickers,
            "click_rate_pct": round(100 * unique_clickers / participant_count, 1),
            "unique_reporters": unique_reporters,
            "report_rate_pct": round(100 * unique_reporters / participant_count, 1),
            "unique_openers": unique_openers,
            "open_rate_pct": round(100 * unique_openers / participant_count, 1),
        })

    return {
        "campaign_id": campaign_id,
        "privacy_mode": "aggregate_only",
        "minimum_cohort_size": MINIMUM_COHORT_SIZE,
        "suppressed_run_count": suppressed_run_count,
        "runs": runs,
        "limitations": LIMITATIONS,
    }


class Handler(BaseHTTPRequestHandler):
    def json_response(self, status, payload):
        raw = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            return self.json_response(
                200, {"status": "ok", "service": "hhl-hrm", "privacy_mode": "aggregate_only"}
            )
        if parsed.path != "/summary":
            return self.json_response(404, {"error": "not_found"})

        campaigns = parse_qs(parsed.query, keep_blank_values=True).get("campaign", [])
        if len(campaigns) != 1 or not CAMPAIGN_PATTERN.fullmatch(campaigns[0]):
            return self.json_response(400, {"error": "invalid_campaign"})
        events = load_events(campaigns[0])
        return self.json_response(200, summarize_events(events, campaigns[0]))

    def log_message(self, fmt, *args):
        return


if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
