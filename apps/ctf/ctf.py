from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8092"))
TELEMETRY_DB = os.getenv("TELEMETRY_DB_PATH", "/telemetry/hhl-simulation.db")
CTF_DB = os.getenv("CTF_DB_PATH", "/data/hhl-ctf.db")
CAMPAIGN_ID = "HHL02-A"
PLAYER_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,31}$")
DB_LOCK = threading.Lock()

CHALLENGES = {
    "HHL-CTF-01": {
        "title": "Trace the Synthetic Run",
        "points": 100,
        "prerequisite": None,
        "objective": "Find the correlation ID of the latest synthetic campaign run and derive its flag.",
        "hint": "SHA-256 material: correlation_id. Use the first 12 hexadecimal characters.",
    },
    "HHL-CTF-02": {
        "title": "Prove the Analyst Signal",
        "points": 150,
        "prerequisite": "HHL-CTF-01",
        "objective": "Identify a D001-equivalent user in the latest run and derive a flag from its evidence.",
        "hint": "Material: correlation_id|user_id|sorted click event IDs. Join event IDs with commas.",
    },
    "HHL-CTF-03": {
        "title": "Find the Campaign-Wide Signal",
        "points": 200,
        "prerequisite": "HHL-CTF-02",
        "objective": "Identify a D002-equivalent run with at least five distinct synthetic users clicking.",
        "hint": "Material: correlation_id|sorted distinct user IDs. Join user IDs with commas.",
    },
    "HHL-CTF-04": {
        "title": "Reconstruct the Incident Timeline",
        "points": 250,
        "prerequisite": "HHL-CTF-03",
        "objective": "Use the click evidence from a run that satisfies both D001 and D002.",
        "hint": "Material: correlation_id|sorted click event IDs. Join event IDs with commas.",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def normalize_player_id(value: str) -> str:
    value = (value or "").strip()
    if not PLAYER_RE.fullmatch(value):
        raise ValueError("invalid_player_id")
    return value


def flag_for(challenge_id: str, material: str) -> str:
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:12]
    number = challenge_id.rsplit("-", 1)[-1]
    return f"HHL{{{number}_{digest}}}"


def connect_telemetry():
    conn = sqlite3.connect(f"file:{TELEMETRY_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def latest_run(conn):
    row = conn.execute(
        """SELECT correlation_id, MAX(timestamp) AS latest
           FROM events
           WHERE campaign_id=? AND event_type='delivered'
             AND correlation_id IS NOT NULL
           GROUP BY correlation_id
           ORDER BY latest DESC LIMIT 1""",
        (CAMPAIGN_ID,),
    ).fetchone()
    return row["correlation_id"] if row else None


def clicks_for_run(conn, correlation_id):
    return conn.execute(
        """SELECT id, user_id, timestamp
           FROM events
           WHERE campaign_id=? AND correlation_id=? AND event_type='clicked'
           ORDER BY timestamp ASC, id ASC""",
        (CAMPAIGN_ID, correlation_id),
    ).fetchall()


def challenge_material(challenge_id: str, conn):
    run_id = latest_run(conn)
    if not run_id:
        return None

    clicks = clicks_for_run(conn, run_id)
    by_user = {}
    for row in clicks:
        by_user.setdefault(row["user_id"], []).append(row["id"])

    if challenge_id == "HHL-CTF-01":
        return run_id

    if challenge_id == "HHL-CTF-02":
        candidates = [
            (user_id, ids) for user_id, ids in by_user.items() if len(ids) > 3
        ]
        if not candidates:
            return None
        user_id, ids = sorted(candidates)[0]
        return f"{run_id}|{user_id}|{','.join(sorted(ids))}"

    if challenge_id == "HHL-CTF-03":
        if len(by_user) < 5:
            return None
        users = sorted(by_user)
        return f"{run_id}|{','.join(users)}"

    if challenge_id == "HHL-CTF-04":
        if len(by_user) < 5 or not any(len(ids) > 3 for ids in by_user.values()):
            return None
        ids = sorted(row["id"] for row in clicks)
        return f"{run_id}|{','.join(ids)}"

    raise KeyError("unknown_challenge")


def challenge_flag(challenge_id: str, conn):
    material = challenge_material(challenge_id, conn)
    return flag_for(challenge_id, material) if material else None


def init_score_db():
    conn = sqlite3.connect(CTF_DB, check_same_thread=False)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS submissions (
            player_id TEXT NOT NULL,
            challenge_id TEXT NOT NULL,
            accepted_at TEXT NOT NULL,
            PRIMARY KEY(player_id, challenge_id)
        )"""
    )
    conn.commit()
    return conn


def score_for(player_id: str, conn):
    row = conn.execute(
        """SELECT COALESCE(SUM(c.points), 0)
           FROM submissions s
           JOIN ctf_challenges c ON c.challenge_id=s.challenge_id
           WHERE s.player_id=?""",
        (player_id,),
    ).fetchone()
    return int(row[0] or 0)


def init_challenge_table(conn):
    conn.execute(
        """CREATE TABLE IF NOT EXISTS ctf_challenges (
            challenge_id TEXT PRIMARY KEY,
            points INTEGER NOT NULL
        )"""
    )
    conn.executemany(
        "INSERT OR IGNORE INTO ctf_challenges(challenge_id, points) VALUES(?,?)",
        [(cid, data["points"]) for cid, data in CHALLENGES.items()],
    )
    conn.commit()


def completed(player_id: str, challenge_id: str, conn):
    row = conn.execute(
        "SELECT 1 FROM submissions WHERE player_id=? AND challenge_id=?",
        (player_id, challenge_id),
    ).fetchone()
    return row is not None


def can_submit(player_id: str, challenge_id: str, conn):
    prerequisite = CHALLENGES[challenge_id]["prerequisite"]
    return prerequisite is None or completed(player_id, prerequisite, conn)


def submit(player_id: str, challenge_id: str, flag: str, telemetry_conn, score_conn):
    if challenge_id not in CHALLENGES:
        return 404, {"error": "unknown_challenge"}

    player_id = normalize_player_id(player_id)
    if completed(player_id, challenge_id, score_conn):
        return 409, {"error": "already_completed"}

    if not can_submit(player_id, challenge_id, score_conn):
        return 409, {"error": "prerequisite_not_completed"}

    expected = challenge_flag(challenge_id, telemetry_conn)
    if expected is None:
        return 409, {"error": "challenge_not_ready"}

    if flag.strip() != expected:
        return 403, {"error": "invalid_flag"}

    with DB_LOCK:
        score_conn.execute(
            "INSERT INTO submissions(player_id, challenge_id, accepted_at) VALUES(?,?,?)",
            (player_id, challenge_id, utc_now()),
        )
        score_conn.commit()

    return 201, {
        "status": "accepted",
        "player_id": player_id,
        "challenge_id": challenge_id,
        "points": CHALLENGES[challenge_id]["points"],
        "score": score_for(player_id, score_conn),
    }


class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, score_conn=None, **kwargs):
        self.score_conn = score_conn
        super().__init__(*args, **kwargs)

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

        if parsed.path == "/health":
            return self._json(200, {"status": "ok", "service": "hhl-ctf"})

        if parsed.path == "/challenges":
            return self._json(200, [
                {
                    "id": cid,
                    "title": data["title"],
                    "points": data["points"],
                    "prerequisite": data["prerequisite"],
                    "objective": data["objective"],
                }
                for cid, data in CHALLENGES.items()
            ])

        if parsed.path == "/score":
            query = parse_qs(parsed.query)
            try:
                player_id = normalize_player_id(query.get("player", [""])[0])
            except ValueError as exc:
                return self._json(400, {"error": str(exc)})
            rows = self.score_conn.execute(
                """SELECT challenge_id, accepted_at
                   FROM submissions WHERE player_id=? ORDER BY accepted_at ASC""",
                (player_id,),
            ).fetchall()
            return self._json(200, {
                "player_id": player_id,
                "score": score_for(player_id, self.score_conn),
                "completed": [
                    {"challenge_id": row[0], "accepted_at": row[1]} for row in rows
                ],
            })

        if parsed.path == "/leaderboard":
            rows = self.score_conn.execute(
                """SELECT player_id, COALESCE(SUM(c.points),0) AS score,
                          COUNT(*) AS completed
                   FROM submissions s
                   JOIN ctf_challenges c ON c.challenge_id=s.challenge_id
                   GROUP BY player_id
                   ORDER BY score DESC, player_id ASC
                   LIMIT 50"""
            ).fetchall()
            return self._json(200, [
                {"player_id": row[0], "score": int(row[1]), "completed": row[2]}
                for row in rows
            ])

        if parsed.path.startswith("/challenges/") and parsed.path.endswith("/hint"):
            challenge_id = parsed.path.split("/")[2]
            if challenge_id not in CHALLENGES:
                return self._json(404, {"error": "unknown_challenge"})
            return self._json(200, {
                "challenge_id": challenge_id,
                "hint": CHALLENGES[challenge_id]["hint"],
            })

        return self._json(404, {"error": "not_found"})

    def do_POST(self):
        if self.path != "/submit":
            return self._json(404, {"error": "not_found"})

        length = min(int(self.headers.get("Content-Length", "0")), 8192)
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
            player_id = payload["player_id"]
            challenge_id = payload["challenge_id"]
            flag = payload["flag"]
            with connect_telemetry() as telemetry_conn:
                status, response = submit(
                    player_id, challenge_id, flag, telemetry_conn, self.score_conn
                )
            return self._json(status, response)
        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            return self._json(400, {"error": str(exc)})
        except sqlite3.Error:
            return self._json(503, {"error": "ctf_storage_unavailable"})

    def log_message(self, fmt, *args):
        return


def make_handler(score_conn):
    return lambda *args, **kwargs: Handler(*args, score_conn=score_conn, **kwargs)


if __name__ == "__main__":
    score_conn = init_score_db()
    init_challenge_table(score_conn)
    server = ThreadingHTTPServer((HOST, PORT), make_handler(score_conn))
    server.serve_forever()
