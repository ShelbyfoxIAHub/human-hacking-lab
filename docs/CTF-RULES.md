# Phase 05 — CTF Engine

Phase 05 adds a deterministic Capture-the-Flag layer over the isolated Human Hacking Lab.

## Safety boundary

- Only synthetic identities and telemetry are used.
- The CTF service is loopback-bound through Docker Compose.
- The CTF service reads simulator telemetry read-only.
- Score state is stored in a separate SQLite database.
- Flags are derived from synthetic lab evidence; no real secrets are required.
- There is no credential collection, external delivery or third-party target.

## Architecture

```
Synthetic Campaign
      |
      v
Telemetry (Phase 03)
      |
      v
Detection Evidence (Phase 04)
      |
      v
CTF Challenge State
      |
      +--> Flag validation
      +--> Player score
      +--> Leaderboard
```

## Challenge progression

| ID | Points | Evidence required |
|---|---:|---|
| HHL-CTF-01 | 100 | Latest synthetic campaign correlation ID |
| HHL-CTF-02 | 150 | One user with >3 clicks in the latest run (D001-equivalent) |
| HHL-CTF-03 | 200 | At least 5 distinct users clicked in the latest run (D002-equivalent) |
| HHL-CTF-04 | 250 | Same run satisfies both D001 and D002 |

The maximum score is **700**.

## API

```bash
curl http://127.0.0.1:8092/health
curl http://127.0.0.1:8092/challenges
curl http://127.0.0.1:8092/challenges/HHL-CTF-01/hint
curl 'http://127.0.0.1:8092/score?player=student-01'
curl http://127.0.0.1:8092/leaderboard
```

Submit a flag:

```bash
curl -X POST http://127.0.0.1:8092/submit \
  -H 'Content-Type: application/json' \
  -d '{"player_id":"student-01","challenge_id":"HHL-CTF-01","flag":"HHL{01_...}"}'
```

## Flag construction

All flags use SHA-256 and the first 12 hexadecimal characters.

- CTF-01: `HHL{01_<sha256(correlation_id)>}`
- CTF-02: `HHL{02_<sha256(correlation_id|user_id|sorted_click_event_ids)>}`
- CTF-03: `HHL{03_<sha256(correlation_id|sorted_distinct_user_ids)>}`
- CTF-04: `HHL{04_<sha256(correlation_id|sorted_click_event_ids)>}`

For CTF-02, CTF-03 and CTF-04, values are joined with a literal `|` between fields and commas inside the sorted list.

The service never exposes expected flags through the challenge listing or score endpoints.

## Reproducibility

Generate a fresh synthetic run:

```bash
curl -X POST http://127.0.0.1:8090/campaigns/HHL02-A/send
```

Use the returned `run_id` as the run correlation ID. Then create synthetic click activity only through the local training URLs or controlled lab tooling.

For CTF-02 and CTF-04, one synthetic user must click more than three times.

For CTF-03 and CTF-04, at least five distinct synthetic users must click.

Because the latest campaign run is used, generate the required clicks after starting the run you intend to solve.

## Scoring model

- A challenge is scored once per `player_id`.
- Challenges are sequential and require their prerequisite.
- Invalid flags never change score.
- The leaderboard contains only synthetic player IDs submitted to this local service.
- Scoring is a training mechanic, not a security or business risk rating.
