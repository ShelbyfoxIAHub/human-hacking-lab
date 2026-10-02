# Human Hacking Lab

Open-source laboratory for ethical social engineering, Human Risk Management, Red Team, Blue Team, OSINT, phishing awareness, detection and cybersecurity training.

> **Safety first:** every exercise is designed for synthetic identities, synthetic data and isolated lab infrastructure. Do not use real credentials, personal data, third-party targets or external messaging infrastructure.

## Phase 04 — Detection Engineering

Phase 04 adds a deterministic Blue Team detection layer over Phase 03 telemetry:

- isolated read-only detection service
- explainable detection rules
- evidence-linked alerts
- correlation-aware analysis
- analyst investigation exercise

Detection API:

```bash
curl http://127.0.0.1:8091/health
curl http://127.0.0.1:8091/rules
curl http://127.0.0.1:8091/alerts
```

See [docs/DETECTION-RULES.md](docs/DETECTION-RULES.md) and [exercises/phase-04/HHL-04.md](exercises/phase-04/HHL-04.md).

## Quick start

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

The complete lab remains local-only through loopback-bound ports.
