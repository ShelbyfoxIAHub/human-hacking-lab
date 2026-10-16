from __future__ import annotations

import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8097"))
MODULES_PATH = Path(__file__).with_name("modules.json")
MODULE_CATALOG = json.loads(MODULES_PATH.read_text(encoding="utf-8"))
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
RULES = [
    {
        "rule_id": "APPSEC-R001",
        "title": "Interpolated SQL query",
        "severity": "HIGH",
        "description": "SQL is constructed with a formatted string instead of bound parameters.",
        "pattern": re.compile(r"\.execute\s*\(\s*f['\"]"),
        "remediation": "Use a parameterized query and pass values separately to the database driver.",
    },
    {
        "rule_id": "APPSEC-R002",
        "title": "Untrusted value assigned to an HTML sink",
        "severity": "HIGH",
        "description": "A display value is assigned to innerHTML, which parses it as markup.",
        "pattern": re.compile(r"\.innerHTML\s*="),
        "remediation": "Use textContent for plain text, or a reviewed sanitizer when rich HTML is required.",
    },
]


def list_modules():
    return [
        {
            "id": module["id"],
            "title": module["title"],
            "objective": module["objective"],
        }
        for module in MODULE_CATALOG["modules"]
    ]


def analyze_module(module_id: str):
    if not isinstance(module_id, str) or not ID_PATTERN.fullmatch(module_id):
        raise ValueError("invalid_module_id")
    module = next(
        (item for item in MODULE_CATALOG["modules"] if item["id"] == module_id),
        None,
    )
    if module is None:
        raise KeyError("unknown_module")

    findings = []
    for rule in RULES:
        for line_number, line in enumerate(module["source_code"].splitlines(), 1):
            if rule["pattern"].search(line):
                findings.append({
                    "rule_id": rule["rule_id"],
                    "title": rule["title"],
                    "severity": rule["severity"],
                    "description": rule["description"],
                    "line": line_number,
                    "remediation": rule["remediation"],
                })

    return {
        "module_id": module["id"],
        "title": module["title"],
        "objective": module["objective"],
        "source_code": module["source_code"],
        "findings": findings,
        "remediated_code": module["remediated_code"],
        "secure": not findings,
        "analysis_mode": "static analysis of bundled educational fixture; code is never executed",
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
                200, {"status": "ok", "service": "hhl-appsec", "mode": "static-only"}
            )
        if parsed.path == "/modules":
            return self.json_response(200, list_modules())
        if parsed.path != "/analyze":
            return self.json_response(404, {"error": "not_found"})

        module_ids = parse_qs(parsed.query, keep_blank_values=True).get("id", [])
        if len(module_ids) != 1:
            return self.json_response(400, {"error": "invalid_module_id"})
        try:
            result = analyze_module(module_ids[0])
        except ValueError as exc:
            return self.json_response(400, {"error": str(exc)})
        except KeyError as exc:
            return self.json_response(404, {"error": str(exc)})
        return self.json_response(200, result)

    def log_message(self, fmt, *args):
        return


if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
