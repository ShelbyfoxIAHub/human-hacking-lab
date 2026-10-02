# Telemetry Schema v1

Phase 03 defines a stable internal event contract for later SIEM ingestion.

| Field | Type | Purpose |
|---|---|---|
| event_id | UUID | Unique event identifier |
| campaign_id | string | Synthetic campaign |
| user_id | string | Synthetic persona identifier |
| event_type | enum | delivered/opened/clicked/reported |
| timestamp | ISO-8601 UTC | Event time |
| correlation_id | UUID | Links events from one campaign run |
| source | string | Event producer |
| metadata | object | Small allow-listed context |

## Security requirements

- Never store plaintext training tokens.
- Never store passwords, secrets, authorization headers or message bodies.
- Keep synthetic user IDs only.
- Use UTC timestamps.
- Keep events append-oriented.
- Expose only sanitized event fields through the API.

## Future SIEM mapping

The schema can later be transformed into ECS-like or OCSF-like records without changing the lab's internal event contract.
