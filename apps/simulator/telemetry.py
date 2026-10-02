from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone

LOGGER = logging.getLogger("hhl.telemetry")
EVENT_TYPES = {"delivered", "opened", "clicked", "reported"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def new_id() -> str:
    return str(uuid.uuid4())


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def sanitize_metadata(metadata: dict | None) -> dict:
    if not metadata:
        return {}
    return {str(k): str(v) for k, v in metadata.items() if k not in {"password", "secret", "token"}}


def emit_log(event: dict) -> None:
    LOGGER.info(json.dumps(event, separators=(",", ":"), sort_keys=True))
