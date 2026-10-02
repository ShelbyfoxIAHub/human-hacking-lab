# Human Hacking Lab

Open-source laboratory for ethical social engineering, Human Risk Management, Red Team, Blue Team, OSINT, phishing awareness, detection, CTF and cybersecurity training.

> **Safety first:** every exercise is designed for synthetic identities, synthetic data and isolated lab infrastructure. Do not use real credentials, personal data, third-party targets or external messaging infrastructure.

## Phase 05 — CTF Engine

Phase 05 adds a deterministic Capture-the-Flag layer over the Phase 03 telemetry and Phase 04 detection evidence:

- progressive forensic challenges
- synthetic flags derived from lab evidence
- one-time per-player scoring
- local leaderboard
- read-only access to telemetry
- separate persistent score database
- no credential collection

CTF API:

```bash
curl http://127.0.0.1:8092/health
curl http://127.0.0.1:8092/challenges
curl http://127.0.0.1:8092/challenges/HHL-CTF-01/hint
curl 'http://127.0.0.1:8092/score?player=student-01'
curl http://127.0.0.1:8092/leaderboard
```

See [docs/CTF-RULES.md](docs/CTF-RULES.md) and [exercises/phase-05/HHL-05.md](exercises/phase-05/HHL-05.md).

## Quick start

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

The complete lab remains local-only through loopback-bound ports.

## Training flow

```text
Synthetic Campaign
      |
      v
Telemetry
      |
      v
Detection
      |
      v
CTF Evidence
      |
      v
Flag Validation
      |
      v
Score / Leaderboard
```

Phase 06 will extend this evidence chain into formal assessment, remediation, retest and residual-risk reporting.
