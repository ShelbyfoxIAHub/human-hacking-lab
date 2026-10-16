# Blue Team Alert Triage

Phase 15 adds evidence-linked triage for deterministic synthetic detections.
The triage service queries the detection API, verifies that an alert exists,
and stores only a fixed training disposition and the alert's supporting event
IDs.

## Safety and data boundaries

- Detection reads telemetry from the isolated simulation database.
- Campaign-wide HHL-D002 alerts include the contributing event IDs.
- Triage records are stored in a separate append-only SQLite database.
- The triage service does not modify telemetry or execute containment actions.
- Decisions are a closed set: validate synthetic activity, recommend rule
  review, or escalate to the instructor.
- No free-text analyst notes or real-person identifiers are accepted.

## Dashboard workflow

1. Generate enough synthetic clicks to trigger one or both detection rules.
2. Refresh telemetry and alerts.
3. Review each alert's campaign, correlation ID and event IDs.
4. Select a bounded training disposition and record it.
5. Confirm the append-only triage history references the same alert and
   evidence.

## API

```bash
curl 'http://127.0.0.1:8091/alerts?campaign=HHL02-A'
curl 'http://127.0.0.1:8099/records?campaign=HHL02-A'
```

Triage submission uses `POST /records` with a campaign ID, alert ID and one of
the listed dispositions. The service looks up the alert itself and derives
the evidence event IDs; callers cannot submit arbitrary evidence or target
URLs.

Triage is an educational workflow, not incident response against a real
environment.
