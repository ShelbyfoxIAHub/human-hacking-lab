from __future__ import annotations

import json
import os
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", "/data/hhl-simulation.db")
HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8091"))

RULES = [
    {
        "id": "HHL-D001",
        "name": "Repeated campaign interactions",
        "description": "More than three clicks by one synthetic user in a campaign run.",
        "severity": "MEDIUM",
        "event_type": "clicked",
        "threshold": 3,
    },
    {
        "id": "HHL-D002",
        "name": "Campaign click burst",
        "description": "At least five synthetic users clicked in one campaign run.",
        "severity": "MEDIUM",
        "event_type": "clicked",
        "threshold": 5,
    },
]


def db():
    return sqlite3.connect(DB_PATH)


def load_events(campaign_id: str | None = None):
    conn = db()
    try:
        query = """SELECT id,campaign_id,user_id,event_type,timestamp,
                          correlation_id,source,metadata_json
                   FROM events"""
        args = []
        if campaign_id:
            query += " WHERE campaign_id=?"
            args.append(campaign_id)
        query += " ORDER BY timestamp ASC"
        rows = conn.execute(query, args).fetchall()
    finally:
        conn.close()

    events = []
    for r in rows:
        events.append({
            "event_id": r[0],
            "campaign_id": r[1],
            "user_id": r[2],
            "event_type": r[3],
            "timestamp": r[4],
            "correlation_id": r[5],
            "source": r[6],
            "metadata": json.loads(r[7] or "{}"),
        })
    return events


def detect(campaign_id: str | None = None):
    events = load_events(campaign_id)
    clicks_by_user = defaultdict(list)
    users_by_run = defaultdict(set)

    for event in events:
        if event["event_type"] != "clicked":
            continue
        key = (event["campaign_id"], event["correlation_id"])
        clicks_by_user[(key, event["user_id"])].append(event)
        users_by_run[key].add(event["user_id"])

    alerts = []

    for (campaign_run, user_id), clicks in clicks_by_user.items():
        if len(clicks) > 3:
            campaign, correlation_id = campaign_run
            alerts.append({
                "alert_id": f"HHL-D001-{campaign}-{user_id}-{correlation_id}",
                "rule_id": "HHL-D001",
                "severity": "MEDIUM",
                "campaign_id": campaign,
                "correlation_id": correlation_id,
                "user_id": user_id,
                "title": "Repeated campaign interactions",
                "evidence_count": len(clicks),
                "evidence_event_ids": [e["event_id"] for e in clicks],
            })

    for (campaign, correlation_id), users in users_by_run.items():
        if len(users) >= 5:
            alerts.append({
                "alert_id": f"HHL-D002-{campaign}-{correlation_id}",
                "rule_id": "HHL-D002",
                "severity": "MEDIUM",
                "campaign_id": campaign,
                "correlation_id": correlation_id,
                "title": "Campaign click burst",
                "evidence_count": len(users),
                "evidence_users": sorted(users),
            })

    return alerts


def http_json(handler, status, payload):
    raw = json.dumps(payload, separators=(",", ":")).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            return http_json(self, 200, {"status": "ok", "service": "hhl-detection"})

        if parsed.path == "/rules":
            return http_json(self, 200, RULES)

        if parsed.path == "/alerts":
            campaign = parse_qs(parsed.query).get("campaign", [None])[0]
            return http_json(self, 200, {"alerts": detect(campaign)})

        return http_json(self, 404, {"error": "not_found"})

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
