# Threat Hunting and DFIR

Phase 10 adds deterministic threat-hunting hypotheses and incident timeline
reconstruction over the lab's synthetic telemetry. It does not access external
systems or infer behavior about real people.

## Safety and evidence boundary

- The detection service reads the simulator database in read-only mode.
- Queries use synthetic campaign IDs and correlation IDs.
- Timeline output contains only the sanitized telemetry fields: event ID,
  campaign, synthetic user ID, event type, UTC timestamp, correlation ID,
  source and allow-listed metadata.
- Tokens, message bodies, credentials and personal data are never returned.
- Hunt matches are training hypotheses, not proof of a real compromise.

## Hunt hypotheses

| ID | Hypothesis | Match condition |
|---|---|---|
| HHL-H001 | Repeated synthetic-user activity | More than three clicks by one user in one run |
| HHL-H002 | Campaign-wide click burst | At least five distinct users click in one run |
| HHL-H003 | Compound incident reconstruction | One run satisfies both HHL-H001 and HHL-H002 |

Each match includes the campaign, correlation ID, relevant synthetic users,
and event IDs so an analyst can pivot to the timeline.

## API

```bash
curl 'http://127.0.0.1:8091/hunts?campaign=HHL02-A'
curl 'http://127.0.0.1:8091/timeline?run=<RUN_ID>'
```

The same evidence is available in the local dashboard under **Búsqueda de
amenazas** and **Reconstrucción temporal DFIR**. The timeline is ordered by UTC
timestamp and event ID.

## Reproducible investigation

1. Start a fresh synthetic campaign from the dashboard and open its messages
   only in local MailHog.
2. Click once for each of the five synthetic users; click one user's link three
   additional times.
3. Refresh events and alerts, inspect the three hunt hypotheses, and note the
   correlation ID and supporting event IDs.
4. Select that run in the DFIR timeline and verify that delivery events precede
   the corresponding synthetic clicks.
5. Explain which evidence supports or does not support each hypothesis. Keep
   conclusions within the synthetic exercise scope.

The detector and timeline are deterministic for a fixed event set. New
campaign runs create new correlation IDs and do not change the evidence for
earlier runs.
