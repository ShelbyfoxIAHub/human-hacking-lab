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

The current Compose build and host-access network compatibility notes, including
the safe migration criteria after Docker Compose updates, are documented in
[docs/SECURITY-ENGINEERING.md](./docs/SECURITY-ENGINEERING.md).

## Phase status

Phase 01 Foundation ✓
Phase 02 Simulation Engine ✓
Phase 03 Telemetry ✓
Phase 04 Detection Engineering ✓
Phase 05 CTF ✓
Phase 06 Assessment ✓
Phase 07 Reporting / Governance ✓
Phase 08 Control Verification / Regression Gate ✓
Phase 09 Guided Instructor / Learner Dashboard — in progress
Phase 10 Threat Hunting / DFIR — in progress
Phase 11 Synthetic OSINT — in progress
Phase 12 Secure AppSec Review — in progress
Phase 13 Privacy-Safe Human Risk Management — in progress
Phase 14 Security Engineering / Lab Isolation — in progress
Phase 15 Blue Team Alert Triage — in progress
Phase 16 Controlled Red Team Scenario — in progress
Phase 17 Integrated Curriculum — in progress

See docs/THREAT-HUNTING-DFIR.md and exercises/phase-10/HHL-10.md for the hunt
and incident reconstruction workflow; see docs/OSINT.md and
exercises/phase-11/HHL-11.md for the synthetic OSINT workflow; see
docs/APPSEC.md and exercises/phase-12/HHL-12.md for static secure-code review;
see docs/HRM.md and exercises/phase-13/HHL-13.md for aggregate-only HRM; see
docs/SECURITY-ENGINEERING.md and exercises/phase-14/HHL-14.md for the isolation
and CI guardrails; see docs/BLUE-TEAM.md and exercises/phase-15/HHL-15.md for
evidence-linked alert triage; see docs/RED-TEAM.md and
exercises/phase-16/HHL-16.md for the preauthorized simulation scenario; see
docs/CURRICULUM.md and exercises/phase-17/HHL-17.md for integrated learning
paths and progress.

Phase 08 PASS means only that the defined verification controls passed against the available synthetic records at verification time. It is not a declaration that the lab or any external system is secure.
