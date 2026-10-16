from __future__ import annotations

import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", "8096"))
SOURCES_PATH = Path(__file__).with_name("sources.json")
SEARCH_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._@-]{0,79}$")
SOURCE_CATALOG = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))


def valid_search_query(query: str) -> bool:
    return isinstance(query, str) and SEARCH_PATTERN.fullmatch(query) is not None


def search_sources(query: str):
    if not valid_search_query(query):
        raise ValueError("invalid_query")

    needle = query.casefold()
    results = []
    for source in SOURCE_CATALOG["sources"]:
        searchable = " ".join(
            [
                source["source_id"],
                source["source_type"],
                source["title"],
                source["uri"],
                source["summary"],
                *source["indicators"],
                *source["entity_ids"],
            ]
        )
        if needle not in searchable.casefold():
            continue
        results.append({
            "source_id": source["source_id"],
            "source_type": source["source_type"],
            "title": source["title"],
            "uri": source["uri"],
            "observed_at": source["observed_at"],
            "confidence": source["confidence"],
            "summary": source["summary"],
            "indicators": source["indicators"],
            "related_entity_ids": source["entity_ids"],
            "collection_method": source["collection_method"],
        })

    return {
        "dataset_id": SOURCE_CATALOG["dataset_id"],
        "classification": SOURCE_CATALOG["classification"],
        "query": query,
        "result_count": len(results),
        "results": sorted(results, key=lambda result: result["source_id"]),
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
                200, {"status": "ok", "service": "hhl-osint", "mode": "synthetic-only"}
            )
        if parsed.path != "/search":
            return self.json_response(404, {"error": "not_found"})

        queries = parse_qs(parsed.query, keep_blank_values=True).get("q", [])
        if len(queries) != 1:
            return self.json_response(400, {"error": "invalid_query"})
        try:
            results = search_sources(queries[0])
        except ValueError as exc:
            return self.json_response(400, {"error": str(exc)})
        return self.json_response(200, results)

    def log_message(self, fmt, *args):
        return


if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
