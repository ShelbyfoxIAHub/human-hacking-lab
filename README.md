# Human Hacking Lab

Open-source laboratory for ethical social engineering, Human Risk Management, Red Team, Blue Team, OSINT, phishing awareness, detection, CTF and cybersecurity training.

> Safety first: every exercise uses synthetic identities, synthetic data and isolated lab infrastructure. Do not use real credentials, personal data, third-party targets or external messaging infrastructure.

## Current training pipeline

Synthetic Campaign -> Telemetry -> Detection -> CTF Evidence -> Findings -> Remediation -> Retest -> Residual Risk -> Reporting / Governance -> Control Verification / Regression Gate

Phase 08 Verification API:

```bash
curl http://127.0.0.1:8095/health
curl http://127.0.0.1:8095/controls
curl 'http://127.0.0.1:8095/verify?id=ASM-STUDENT-01'
curl 'http://127.0.0.1:8095/runs/<RUN_ID>'
```

See docs/ASSESSMENT.md, docs/REPORTING.md, docs/VERIFICATION.md and exercises/phase-08/HHL-08.md.

## Quick start

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

All exposed lab services remain loopback-bound.

## Phase status

Phase 01 Foundation ✓
Phase 02 Simulation Engine ✓
Phase 03 Telemetry ✓
Phase 04 Detection Engineering ✓
Phase 05 CTF ✓
Phase 06 Assessment ✓
Phase 07 Reporting / Governance ✓
Phase 08 Control Verification / Regression Gate ✓

Phase 08 PASS means only that the defined verification controls passed against the available synthetic records at verification time. It is not a declaration that the lab or any external system is secure.
