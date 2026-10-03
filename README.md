# Human Hacking Lab

Open-source laboratory for ethical social engineering, Human Risk Management, Red Team, Blue Team, OSINT, phishing awareness, detection, CTF and cybersecurity training.

> Safety first: every exercise uses synthetic identities, synthetic data and isolated lab infrastructure. Do not use real credentials, personal data, third-party targets or external messaging infrastructure.

## Current training pipeline

Synthetic Campaign -> Telemetry -> Detection -> CTF Evidence -> Findings -> Remediation -> Retest -> Residual Risk -> Reporting / Governance

Assessment API:

```bash
curl http://127.0.0.1:8093/health
curl 'http://127.0.0.1:8093/assessments?id=ASM-STUDENT-01'
curl 'http://127.0.0.1:8093/risk?id=ASM-STUDENT-01'
```

Reporting / Governance API:

```bash
curl http://127.0.0.1:8094/health
curl 'http://127.0.0.1:8094/reports?id=ASM-STUDENT-01'
curl 'http://127.0.0.1:8094/evidence?id=ASM-STUDENT-01'
curl 'http://127.0.0.1:8094/residual-risk?id=ASM-STUDENT-01'
curl 'http://127.0.0.1:8094/audit?id=ASM-STUDENT-01'
```

See docs/ASSESSMENT.md, docs/REPORTING.md and exercises/phase-07/HHL-07.md.

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

Phase 07 does not declare the lab or any external system secure. Reports are bounded by synthetic evidence, configured assessment state, executed tests and explicit limitations.
