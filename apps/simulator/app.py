from __future__ import annotations

import csv
import json
import logging
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

from telemetry import EVENT_TYPES, emit_log, hash_token, new_id, sanitize_metadata, utc_now

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
LOGGER = logging.getLogger("hhl.simulator")


def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(
        """CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            campaign_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            token TEXT,
            timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            correlation_id TEXT,
            source TEXT NOT NULL DEFAULT 'simulator',
            metadata_json TEXT NOT NULL DEFAULT '{}',
            token_hash TEXT
        )"""
    )

    columns = {row[1] for row in conn.execute("PRAGMA table_info(events)")}
    migrations = {
        "correlation_id": "ALTER TABLE events ADD COLUMN correlation_id TEXT",
        "source": "ALTER TABLE events ADD COLUMN source TEXT NOT NULL DEFAULT 'simulator'",
        "metadata_json": "ALTER TABLE events ADD COLUMN metadata_json TEXT NOT NULL DEFAULT '{}'",
        "token_hash": "ALTER TABLE events ADD COLUMN token_hash TEXT",
    }
    for name, statement in migrations.items():
        if name not in columns:
            conn.execute(statement)

    # Phase 02 persisted raw training tokens. Hash them during the first
    # Phase 03 startup and remove the plaintext value from the database.
    rows = conn.execute(
        "SELECT id, token FROM events WHERE token IS NOT NULL AND token_hash IS NULL"
    ).fetchall()
    for event_id, token in rows:
        conn.execute(
            "UPDATE events SET token_hash=?, token=NULL WHERE id=?",
            (hash_token(token), event_id),
        )

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_events_campaign_type "
        "ON events(campaign_id, event_type)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_events_correlation "
        "ON events(correlation_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_events_token_hash "
        "ON events(token_hash)"
    )
    conn.commit()
    return conn


CONN = db()


def load_users():
    with USERS_FILE.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_campaigns():
    return json.loads(CAMPAIGNS_FILE.read_text(encoding="utf-8"))


def record_event(campaign_id, user_id, event_type, token, correlation_id,
                 source="simulator", metadata=None):
    if event_type not in EVENT_TYPES:
        raise ValueError("unsupported event_type")
    if not token:
        raise ValueError("token_required")

    event_id = new_id()
    event = {
        "event_id": event_id,
        "campaign_id": campaign_id,
        "user_id": user_id,
        "event_type": event_type,
        "timestamp": utc_now(),
        "correlation_id": correlation_id,
        "source": source,
        "metadata": sanitize_metadata(metadata),
    }

    with DB_LOCK:
        CONN.execute(
            """INSERT INTO events(
                id,campaign_id,user_id,event_type,timestamp,
                correlation_id,source,metadata_json,token_hash
            ) VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                event_id,
                campaign_id,
                user_id,
                event_type,
                event["timestamp"],
                correlation_id,
                source,
                json.dumps(event["metadata"], separators=(",", ":")),
                hash_token(token),
            ),
        )
        CONN.commit()

    emit_log(event)
    return event


def valid_token(campaign_id, user_id, token):
    token_hash = hash_token(token)
    with DB_LOCK:
        row = CONN.execute(
            """SELECT 1 FROM events
               WHERE campaign_id=? AND user_id=? AND token_hash=?
               LIMIT 1""",
            (campaign_id, user_id, token_hash),
        ).fetchone()
    return row is not None


def campaign_summary(campaign_id):
    with DB_LOCK:
        rows = CONN.execute(
            """SELECT event_type, COUNT(*) FROM events
               WHERE campaign_id=? GROUP BY event_type ORDER BY event_type""",
            (campaign_id,),
        ).fetchall()
    return {event: count for event, count in rows}


def campaign_events(campaign_id, limit=100):
    with DB_LOCK:
        rows = CONN.execute(
            """SELECT id,campaign_id,user_id,event_type,timestamp,
                      correlation_id,source,metadata_json
               FROM events
               WHERE campaign_id=?
               ORDER BY timestamp ASC LIMIT ?""",
            (campaign_id, limit),
        ).fetchall()

    events = []
    for row in rows:
        events.append({
            "event_id": row[0],
            "campaign_id": row[1],
            "user_id": row[2],
            "event_type": row[3],
            "timestamp": row[4],
            "correlation_id": row[5],
            "source": row[6],
            "metadata": json.loads(row[7] or "{}"),
        })
    return events


def send_campaign(campaign_id):
    campaign = next((c for c in load_campaigns() if c["id"] == campaign_id), None)
    if campaign is None:
        raise ValueError("unknown campaign")

    users = load_users()
    sender = campaign["sender"]
    subject = campaign["subject"]
    run_id = str(uuid.uuid4())
    sent = 0

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
        for user in users:
            token = secrets.token_urlsafe(18)
            click_url = (
                f"{PUBLIC_BASE_URL}/training/click?"
                f"campaign={campaign_id}&user={user['id']}"
                f"&run={run_id}&token={token}"
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

            record_event(
                campaign_id,
                user["id"],
                "delivered",
                token,
                run_id,
                source="smtp",
                metadata={"transport": "mailhog"},
            )
            sent += 1

    return sent, run_id


class Handler(BaseHTTPRequestHandler):
    def _json(self, status, payload):
        raw = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/health":
            with DB_LOCK:
                CONN.execute("SELECT 1").fetchone()
            return self._json(200, {
                "status": "ok",
                "service": "hhl-simulator",
                "telemetry": "v1",
            })

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

        if path.startswith("/campaigns/") and path.endswith("/events"):
            campaign_id = path.split("/")[2]
            query = parse_qs(parsed.query)
            try:
                limit = min(max(int(query.get("limit", ["100"])[0]), 1), 500)
            except ValueError:
                return self._json(400, {"error": "invalid_limit"})
            return self._json(200, {
                "campaign_id": campaign_id,
                "events": campaign_events(campaign_id, limit),
            })

        return self._json(404, {"error": "not_found"})

    def do_POST(self):
        path = urlparse(self.path).path

        if path.startswith("/campaigns/") and path.endswith("/send"):
            campaign_id = path.split("/")[2]
            try:
                sent, run_id = send_campaign(campaign_id)
                return self._json(202, {
                    "campaign_id": campaign_id,
                    "run_id": run_id,
                    "delivered": sent,
                    "note": "Messages remain inside the local MailHog sink.",
                })
            except ValueError as exc:
                return self._json(404, {"error": str(exc)})
            except (OSError, smtplib.SMTPException) as exc:
                return self._json(503, {"error": f"smtp_unavailable: {exc}"})

        if path == "/events":
            length = min(int(self.headers.get("Content-Length", "0")), 16384)
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
                campaign_id = payload["campaign_id"]
                user_id = payload["user_id"]
                token = payload["token"]
                event_type = payload["event_type"]
                correlation_id = payload["correlation_id"]

                if event_type not in {"opened", "clicked", "reported"}:
                    raise ValueError("unsupported_event_type")
                if not valid_token(campaign_id, user_id, token):
                    return self._json(403, {"error": "invalid_training_token"})

                event = record_event(
                    campaign_id,
                    user_id,
                    event_type,
                    token,
                    correlation_id,
                    source=payload.get("source", "training"),
                    metadata=payload.get("metadata"),
                )
                return self._json(201, {"status": "recorded", "event": event})
            except (KeyError, ValueError, json.JSONDecodeError) as exc:
                return self._json(400, {"error": str(exc)})
            except OverflowError:
                return self._json(413, {"error": "payload_too_large"})

        return self._json(404, {"error": "not_found"})

    def log_message(self, fmt, *args):
        LOGGER.info("%s - %s", self.address_string(), fmt % args)


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(message)s",
    )
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
