from __future__ import annotations

import json
import os
import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", "/data/hhl-simulation.db")
HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8091"))
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")

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

HUNT_DEFINITIONS = [
    {
        "hunt_id": "HHL-H001",
        "title": "Repeated synthetic-user activity",
        "hypothesis": "One synthetic user generated more than three clicks in a campaign run.",
    },
    {
        "hunt_id": "HHL-H002",
        "title": "Campaign-wide click burst",
        "hypothesis": "At least five distinct synthetic users clicked in one campaign run.",
    },
    {
        "hunt_id": "HHL-H003",
        "title": "Compound incident reconstruction",
        "hypothesis": "A campaign run contains both repeated-user activity and a campaign-wide click burst.",
    },
]


def db():
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)


def load_events(campaign_id: str | None = None, correlation_id: str | None = None):
    conn = db()
    try:
        query = """SELECT id,campaign_id,user_id,event_type,timestamp,
                          correlation_id,source,metadata_json
                   FROM events"""
        args = []
        conditions = []
        if campaign_id:
            conditions.append("campaign_id=?")
            args.append(campaign_id)
        if correlation_id:
            conditions.append("correlation_id=?")
            args.append(correlation_id)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY timestamp ASC,id ASC"
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


def hunt_hypotheses(events):
    clicks_by_run = defaultdict(list)
    for event in events:
        if event["event_type"] == "clicked":
            clicks_by_run[(event["campaign_id"], event["correlation_id"])].append(event)

    matches = {definition["hunt_id"]: [] for definition in HUNT_DEFINITIONS}
    for (campaign_id, correlation_id), clicks in sorted(clicks_by_run.items()):
        by_user = defaultdict(list)
        for event in clicks:
            by_user[event["user_id"]].append(event)

        click_ids = sorted(event["event_id"] for event in clicks)
        repeated_users = sorted(
            user_id for user_id, user_clicks in by_user.items()
            if len(user_clicks) > 3
        )
        user_ids = sorted(by_user)

        for user_id in repeated_users:
            matches["HHL-H001"].append({
                "campaign_id": campaign_id,
                "correlation_id": correlation_id,
                "user_id": user_id,
                "click_count": len(by_user[user_id]),
                "event_ids": sorted(event["event_id"] for event in by_user[user_id]),
            })

        if len(user_ids) >= 5:
            matches["HHL-H002"].append({
                "campaign_id": campaign_id,
                "correlation_id": correlation_id,
                "user_count": len(user_ids),
                "user_ids": user_ids,
                "event_ids": click_ids,
            })

        if repeated_users and len(user_ids) >= 5:
            matches["HHL-H003"].append({
                "campaign_id": campaign_id,
                "correlation_id": correlation_id,
                "user_count": len(user_ids),
                "user_ids": user_ids,
                "repeated_users": repeated_users,
                "event_ids": click_ids,
            })

    return [
        {
            **definition,
            "matches": matches[definition["hunt_id"]],
        }
        for definition in HUNT_DEFINITIONS
    ]


def incident_timeline(events, correlation_id):
    return sorted(
        (event for event in events if event["correlation_id"] == correlation_id),
        key=lambda event: (event["timestamp"], event["event_id"]),
    )


def detect(campaign_id: str | None = None):
    events = load_events(campaign_id)
    clicks_by_user = defaultdict(list)
    users_by_run = defaultdict(set)
    clicks_by_run = defaultdict(list)

    for event in events:
        if event["event_type"] != "clicked":
            continue
        key = (event["campaign_id"], event["correlation_id"])
        clicks_by_user[(key, event["user_id"])].append(event)
        users_by_run[key].add(event["user_id"])
        clicks_by_run[key].append(event)

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
                "evidence_event_ids": sorted(
                    event["event_id"]
                    for event in clicks_by_run[(campaign, correlation_id)]
                ),
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
        path = parsed.path

        if parsed.path == "/health":
            return http_json(self, 200, {"status": "ok", "service": "hhl-detection"})

        if parsed.path == "/rules":
            return http_json(self, 200, RULES)

        if parsed.path == "/alerts":
            campaign = parse_qs(parsed.query).get("campaign", [None])[0]
            return http_json(self, 200, {"alerts": detect(campaign)})

        if path == "/hunts":
            query = parse_qs(parsed.query, keep_blank_values=True)
            campaigns = query.get("campaign", [])
            if len(campaigns) != 1 or not RUN_ID_PATTERN.fullmatch(campaigns[0]):
                return http_json(self, 400, {"error": "invalid_campaign"})
            events = load_events(campaign_id=campaigns[0])
            return http_json(self, 200, {
                "campaign_id": campaigns[0],
                "hypotheses": hunt_hypotheses(events),
            })

        if path == "/timeline":
            query = parse_qs(parsed.query, keep_blank_values=True)
            run_ids = query.get("run", [])
            if len(run_ids) != 1 or not RUN_ID_PATTERN.fullmatch(run_ids[0]):
                return http_json(self, 400, {"error": "invalid_run_id"})
            events = load_events(correlation_id=run_ids[0])
            timeline = incident_timeline(events, run_ids[0])
            return http_json(self, 200, {
                "correlation_id": run_ids[0],
                "event_count": len(timeline),
                "events": timeline,
            })

        return http_json(self, 404, {"error": "not_found"})

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
