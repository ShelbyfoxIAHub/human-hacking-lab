# HHL-05 — CTF: Telemetry to Incident Timeline

## Objective

Practice turning synthetic telemetry and detection evidence into reproducible challenge flags.

## Scope

- Target: local Human Hacking Lab containers only.
- Identities: synthetic.
- Data: synthetic.
- Network: isolated Docker network.
- External messaging: prohibited.
- Credential collection: prohibited.

## Start

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

Verify:

```bash
curl http://127.0.0.1:8092/health
curl http://127.0.0.1:8092/challenges
```

Use a synthetic player ID such as `student-01`.

## Challenge 01

Start a fresh campaign:

```bash
curl -X POST http://127.0.0.1:8090/campaigns/HHL02-A/send
```

Inspect telemetry and identify the run correlation ID. Build the CTF-01 flag from that value.

## Challenge 02

Using the training links in MailHog, make one synthetic user click more than three times in the same run. Then inspect:

```bash
curl 'http://127.0.0.1:8090/campaigns/HHL02-A/events?limit=500'
curl 'http://127.0.0.1:8091/alerts?campaign=HHL02-A'
```

Trace the D001-equivalent evidence and derive CTF-02.

## Challenge 03

Make at least five distinct synthetic users click in the same run. Verify the D002 alert and derive CTF-03.

## Challenge 04

Keep the same run and satisfy both conditions:

1. one user has more than three clicks;
2. at least five distinct users have clicked.

Reconstruct the complete click-event timeline and derive CTF-04.

## Submit

```bash
curl -X POST http://127.0.0.1:8092/submit \
  -H 'Content-Type: application/json' \
  -d '{"player_id":"student-01","challenge_id":"HHL-CTF-01","flag":"HHL{01_...}"}'
```

Check score:

```bash
curl 'http://127.0.0.1:8092/score?player=student-01'
```

## Expected evidence

For each solved challenge record:

- challenge ID;
- synthetic player ID;
- run correlation ID;
- relevant event IDs;
- detection rule, when applicable;
- flag derivation material;
- score response;
- limitations.

Do not record or submit real credentials, personal data or third-party information.

## Instructor validation

A valid run should be reproducible from:

1. a fresh synthetic campaign;
2. controlled local clicks;
3. Phase 03 telemetry;
4. Phase 04 deterministic detection;
5. Phase 05 flag derivation;
6. one-time scoring per challenge.
