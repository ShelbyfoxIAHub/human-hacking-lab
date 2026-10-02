# Detection Rules v1

Phase 04 introduces deterministic, explainable detection over synthetic telemetry.

| Rule | Condition | Severity | Evidence |
|---|---|---|---|
| HHL-D001 | >3 clicks by one synthetic user in one campaign run | MEDIUM | event IDs + user + correlation ID |
| HHL-D002 | >=5 synthetic users click in one campaign run | MEDIUM | user IDs + correlation ID |

## Design principles

- Rules operate only on lab telemetry.
- Every alert references concrete event evidence.
- No inference about real people.
- Severity is a training classification, not a production risk score.
- Rules are deterministic and reproducible.

## API

```bash
curl http://127.0.0.1:8091/rules
curl http://127.0.0.1:8091/alerts
curl 'http://127.0.0.1:8091/alerts?campaign=HHL02-A'
```

## Detection workflow

Telemetry → rule evaluation → alert → analyst investigation → response exercise.
