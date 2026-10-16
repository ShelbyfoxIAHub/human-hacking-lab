from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8099"))
DB_PATH = os.getenv("TRIAGE_DB_PATH", "/data/hhl-blue-team.db")
DETECTION_URL = os.getenv("DETECTION_URL", "http://detection:8091")
CAMPAIGN_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
ALERT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,160}$")
MAX_REQUEST_BYTES = 8_192
MAX_RESPONSE_BYTES = 1_048_576
DECISIONS = {
    "VALIDATED_SYNTHETIC_ACTIVITY",
    "RULE_REVIEW_RECOMMENDED",
    "ESCALATED_TO_INSTRUCTOR",
}
LOCK = threading.Lock()
LOGGER = logging.getLogger("hhl-blue-team")


class DetectionServiceError(Exception):
    def __init__(self, status, code):
        self.status = status
        self.code = code
        super().__init__(code)


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def initialize_database(conn):
    conn.execute(
        """CREATE TABLE IF NOT EXISTS triage_records (
            record_id TEXT PRIMARY KEY,
            alert_id TEXT NOT NULL,
            campaign_id TEXT NOT NULL,
            correlation_id TEXT NOT NULL,
            rule_id TEXT NOT NULL,
            decision TEXT NOT NULL,
            evidence_event_ids_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )"""
    )
    conn.execute(
        """CREATE TRIGGER IF NOT EXISTS triage_records_no_update
           BEFORE UPDATE ON triage_records
           BEGIN SELECT RAISE(ABORT,'triage_records_append_only'); END"""
    )
    conn.execute(
        """CREATE TRIGGER IF NOT EXISTS triage_records_no_delete
           BEFORE DELETE ON triage_records
           BEGIN SELECT RAISE(ABORT,'triage_records_append_only'); END"""
    )
    conn.commit()
    return conn


def init_database(path=DB_PATH):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    return initialize_database(conn)


def fetch_alerts(campaign_id):
    request = Request(
        f"{DETECTION_URL}/alerts?{urlencode({'campaign': campaign_id})}",
        headers={"Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=5) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        LOGGER.error("Detection service rejected triage lookup: %s", exc.code)
        raise DetectionServiceError(502, "detection_request_failed") from exc
    except (URLError, TimeoutError) as exc:
        LOGGER.error("Detection service unavailable for triage: %s", exc)
        raise DetectionServiceError(503, "detection_unavailable") from exc

    if len(raw) > MAX_RESPONSE_BYTES:
        raise DetectionServiceError(502, "detection_response_too_large")
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DetectionServiceError(502, "invalid_detection_response") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("alerts"), list):
        raise DetectionServiceError(502, "invalid_detection_response")
    return payload["alerts"]


def persist_triage(conn, alert, decision):
    if not isinstance(decision, str) or decision not in DECISIONS:
        raise ValueError("invalid_decision")
    event_ids = alert.get("evidence_event_ids")
    if not isinstance(event_ids, list) or not event_ids:
        raise ValueError("alert_evidence_missing")

    record = {
        "record_id": f"TRI-{uuid.uuid4().hex[:12]}",
        "alert_id": alert["alert_id"],
        "campaign_id": alert["campaign_id"],
        "correlation_id": alert["correlation_id"],
        "rule_id": alert["rule_id"],
        "decision": decision,
        "evidence_event_ids": sorted(set(event_ids)),
        "created_at": utc_now(),
    }
    with LOCK:
        conn.execute(
            """INSERT INTO triage_records(
                   record_id,alert_id,campaign_id,correlation_id,rule_id,
                   decision,evidence_event_ids_json,created_at
               ) VALUES(?,?,?,?,?,?,?,?)""",
            (
                record["record_id"],
                record["alert_id"],
                record["campaign_id"],
                record["correlation_id"],
                record["rule_id"],
                record["decision"],
                json.dumps(record["evidence_event_ids"], separators=(",", ":")),
                record["created_at"],
            ),
        )
        conn.commit()
    return record


def records_for_campaign(conn, campaign_id):
    with LOCK:
        rows = conn.execute(
            """SELECT record_id,alert_id,campaign_id,correlation_id,rule_id,
                      decision,evidence_event_ids_json,created_at
               FROM triage_records WHERE campaign_id=?
               ORDER BY created_at ASC,record_id ASC""",
            (campaign_id,),
        ).fetchall()
    return [
        {
            "record_id": row[0],
            "alert_id": row[1],
            "campaign_id": row[2],
            "correlation_id": row[3],
            "rule_id": row[4],
            "decision": row[5],
            "evidence_event_ids": json.loads(row[6]),
            "created_at": row[7],
        }
        for row in rows
    ]


class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, db=None, **kwargs):
        self.db = db
        super().__init__(*args, **kwargs)

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
            with LOCK:
                self.db.execute("SELECT 1").fetchone()
            return self.json_response(
                200, {"status": "ok", "service": "hhl-blue-team"}
            )
        if parsed.path != "/records":
            return self.json_response(404, {"error": "not_found"})

        campaigns = parse_qs(parsed.query, keep_blank_values=True).get("campaign", [])
        if len(campaigns) != 1 or not CAMPAIGN_PATTERN.fullmatch(campaigns[0]):
            return self.json_response(400, {"error": "invalid_campaign"})
        return self.json_response(
            200,
            {
                "campaign_id": campaigns[0],
                "records": records_for_campaign(self.db, campaigns[0]),
            },
        )

    def do_POST(self):
        if urlparse(self.path).path != "/records":
            return self.json_response(404, {"error": "not_found"})

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.json_response(400, {"error": "invalid_content_length"})
        if content_length < 0 or content_length > MAX_REQUEST_BYTES:
            return self.json_response(413, {"error": "payload_too_large"})
        try:
            payload = json.loads(self.rfile.read(content_length) or b"{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self.json_response(400, {"error": "invalid_json"})
        if not isinstance(payload, dict):
            return self.json_response(400, {"error": "invalid_payload"})

        campaign_id = payload.get("campaign_id")
        alert_id = payload.get("alert_id")
        decision = payload.get("decision")
        if (
            not isinstance(campaign_id, str)
            or not CAMPAIGN_PATTERN.fullmatch(campaign_id)
            or not isinstance(alert_id, str)
            or not ALERT_PATTERN.fullmatch(alert_id)
            or not isinstance(decision, str)
            or decision not in DECISIONS
        ):
            return self.json_response(400, {"error": "invalid_triage_request"})

        try:
            alerts = fetch_alerts(campaign_id)
        except DetectionServiceError as exc:
            return self.json_response(exc.status, {"error": exc.code})
        alert = next(
            (
                candidate
                for candidate in alerts
                if candidate.get("alert_id") == alert_id
                and candidate.get("campaign_id") == campaign_id
            ),
            None,
        )
        if alert is None:
            return self.json_response(404, {"error": "alert_not_found"})
        try:
            record = persist_triage(self.db, alert, decision)
        except ValueError as exc:
            return self.json_response(409, {"error": str(exc)})
        return self.json_response(201, {"status": "recorded", "record": record})

    def log_message(self, fmt, *args):
        return


def make_handler(db):
    return lambda *args, **kwargs: Handler(*args, db=db, **kwargs)


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    database = init_database()
    ThreadingHTTPServer((HOST, PORT), make_handler(database)).serve_forever()
