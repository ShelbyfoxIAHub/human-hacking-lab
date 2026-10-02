from __future__ import annotations

import csv
import json
import os
import secrets
import smtplib
import sqlite3
import threading
import uuid
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8090"))
DB_PATH = os.getenv("DB_PATH", "/tmp/hhl-simulation.db")
SMTP_HOST = os.getenv("SMTP_HOST", "mail")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8080")
USERS_FILE = Path(os.getenv("USERS_FILE", "/app/users.csv"))

ROOT = Path(__file__).parent
CAMPAIGNS_FILE = ROOT / "campaigns.json"
DB_LOCK = threading.Lock()


def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            campaign_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            token TEXT NOT NULL,
            timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    conn.execute(
        """CREATE INDEX IF NOT EXISTS idx_events_campaign
           ON events(campaign_id, event_type)"""
    )
    conn.commit()
    return conn


CONN = db()


def load_users():
    with USERS_FILE.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_campaigns():
    return json.loads(CAMPAIGNS_FILE.read_text(encoding="utf-8"))


def record_event(campaign_id, user_id, event_type, token):
    with DB_LOCK:
        CONN.execute(
            "INSERT INTO events(id,campaign_id,user_id,event_type,token) VALUES(?,?,?,?,?)",
            (str(uuid.uuid4()), campaign_id, user_id, event_type, token),
        )
        CONN.commit()


def campaign_summary(campaign_id):
    with DB_LOCK:
        rows = CONN.execute(
            """SELECT event_type, COUNT(*) FROM events
               WHERE campaign_id=? GROUP BY event_type ORDER BY event_type""",
            (campaign_id,),
        ).fetchall()
    return {event: count for event, count in rows}


def send_campaign(campaign_id):
    campaign = next((c for c in load_campaigns() if c["id"] == campaign_id), None)
    if campaign is None:
        raise ValueError("unknown campaign")

    users = load_users()
    sender = campaign["sender"]
    subject = campaign["subject"]
    sent = 0

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
        for user in users:
            token = secrets.token_urlsafe(18)
            click_url = (
                f"{PUBLIC_BASE_URL}/training/click?"
                f"campaign={campaign_id}&user={user['id']}&token={token}"
            )
            body = campaign["body"].format(
                name=user["name"],
                department=user["department"],
                click_url=click_url,
            )

            msg = EmailMessage()
            msg["From"] = sender
            msg["To"] = user["email"]
            msg["Subject"] = subject
            msg.set_content(body)
            smtp.send_message(msg)

            record_event(campaign_id, user["id"], "delivered", token)
            sent += 1

    return sent


class Handler(BaseHTTPRequestHandler):
    def _json(self, status, payload):
        raw = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/health":
            return self._json(200, {"status": "ok"})

        if path == "/campaigns":
            result = []
            for campaign in load_campaigns():
                result.append({
                    "id": campaign["id"],
                    "name": campaign["name"],
                    "summary": campaign_summary(campaign["id"]),
                })
            return self._json(200, result)

        if path.startswith("/campaigns/") and path.endswith("/summary"):
            campaign_id = path.split("/")[2]
            return self._json(200, {
                "campaign_id": campaign_id,
                "events": campaign_summary(campaign_id),
            })

        return self._json(404, {"error": "not_found"})

    def do_POST(self):
        path = urlparse(self.path).path

        if path.startswith("/campaigns/") and path.endswith("/send"):
            campaign_id = path.split("/")[2]
            try:
                sent = send_campaign(campaign_id)
                return self._json(202, {
                    "campaign_id": campaign_id,
                    "delivered": sent,
                    "note": "Messages remain inside the local MailHog sink.",
                })
            except ValueError as exc:
                return self._json(404, {"error": str(exc)})
            except (OSError, smtplib.SMTPException) as exc:
                return self._json(503, {"error": f"smtp_unavailable: {exc}"})

        if path == "/events":
            length = int(self.headers.get("Content-Length", "0"))
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
                event_type = payload["event_type"]
                if event_type not in {"opened", "clicked", "reported"}:
                    raise ValueError("unsupported event_type")
                record_event(
                    payload["campaign_id"],
                    payload["user_id"],
                    event_type,
                    payload["token"],
                )
                return self._json(201, {"status": "recorded"})
            except (KeyError, ValueError, json.JSONDecodeError) as exc:
                return self._json(400, {"error": str(exc)})

        return self._json(404, {"error": "not_found"})

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
