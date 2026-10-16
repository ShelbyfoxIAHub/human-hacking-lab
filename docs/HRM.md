# Privacy-Safe Human Risk Management

Phase 13 provides aggregate metrics for synthetic training campaigns. It is
designed to help improve training content and organizational controls, not to
measure or rank individual people.

## Privacy boundary

- The service reads simulator telemetry in SQLite read-only mode.
- Only aggregate campaign-run metrics are returned; no user IDs, profiles or
  per-person scores are exposed.
- Runs with fewer than five distinct delivered synthetic participants are
  suppressed, including their run identifiers and rates.
- Synthetic click, open and report rates describe events only. They do not
  measure learning, competence, culpability or human risk.
- Use results to improve the exercise, reporting paths and protective
  controls; do not use them for personnel decisions.

## Metrics

- Delivered synthetic participants and delivery events.
- Synthetic click-event count and distinct clicker rate.
- Distinct reporter and opener rates when those events exist.
- Suppressed-run count where a run does not meet the minimum cohort size.

No individual event sequence or user identifier is included in this service's
response.

## Dashboard workflow

1. Run the synthetic campaign and create training interactions in local
   MailHog.
2. Open **Métricas agregadas de Human Risk Management** in the dashboard.
3. Review the cohort size and aggregate rates for each eligible run.
4. Propose a change to training content or reporting controls; do not infer
   that a click rate measures an individual's knowledge or risk.

## API

```bash
curl http://127.0.0.1:8098/health
curl 'http://127.0.0.1:8098/summary?campaign=HHL02-A'
```

The same-origin dashboard route is `/api/hrm/summary?campaign=HHL02-A`.
