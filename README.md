# Human Hacking Lab

Open-source laboratory for ethical social engineering, Human Risk Management, Red Team, Blue Team, OSINT, phishing awareness, detection and cybersecurity training.

> **Safety first:** every exercise is designed for synthetic identities, synthetic data and isolated lab infrastructure. Do not use real credentials, personal data, third-party targets or external messaging infrastructure.

## What is this?

Human Hacking Lab (HHL) is a reproducible training environment for studying the human attack surface without targeting real people.

The project combines:

- Human-centric threat modeling
- OSINT using synthetic personas
- Phishing awareness and controlled simulation
- Pretexting and identity-verification exercises
- Blue Team detection and response
- Security telemetry
- MITRE ATT&CK mapping
- CTF-style defensive challenges

## Current release

### Phase 01 — Foundation

- Docker-based isolated lab network
- Educational web application
- Local SMTP capture with MailHog
- Synthetic user dataset
- Rules of Engagement
- Initial practical exercises

### Phase 02 — Simulation Engine

Phase 02 adds a deterministic, local-only campaign simulator:

- Synthetic campaign definitions
- Local SMTP delivery into MailHog
- Event model: `delivered`, `opened`, `clicked`, `reported`
- SQLite event persistence with a volume
- Controlled training landing page
- Campaign metrics API
- Automated artifact tests
- No credential collection

### Phase 03 — Telemetry

Phase 03 adds a stable telemetry contract for later SIEM integration:

- UTC event timestamps
- correlation IDs per campaign run
- structured JSON logs
- SQLite WAL mode for concurrent lab activity
- migration of Phase 02 plaintext tokens to SHA-256 hashes
- sanitized event API
- token/run binding for training interactions
- telemetry exercise

Inspect events with:

```bash
curl http://127.0.0.1:8090/campaigns/HHL02-A/events
```

Telemetry design is documented in [docs/TELEMETRY-SCHEMA.md](docs/TELEMETRY-SCHEMA.md).

### Quick start

```bash
git clone https://github.com/ShelbyfoxIAHub/human-hacking-lab.git
cd human-hacking-lab
docker compose -f infra/docker-compose.yml up -d --build
```

Open:

- Lab portal: http://127.0.0.1:8080
- MailHog: http://127.0.0.1:8025
- Simulation API: http://127.0.0.1:8090/health

Run the Phase 02 campaign:

```bash
curl -X POST http://127.0.0.1:8090/campaigns/HHL02-A/send
```

View metrics:

```bash
curl http://127.0.0.1:8090/campaigns/HHL02-A/summary
```

Stop the lab:

```bash
docker compose -f infra/docker-compose.yml down
```

Remove persisted simulation data:

```bash
docker compose -f infra/docker-compose.yml down -v
```

## Repository structure

```text
human-hacking-lab/
├── .github/workflows/   # CI
├── apps/                # Lab applications
├── infra/               # Docker/infrastructure
├── scenarios/           # Synthetic identities and scenarios
├── exercises/           # Student exercises
├── tests/               # Automated validation
├── docs/                # Lab documentation and ROE
└── evidence/            # Local evidence directory
```

## Learning path

1. Foundation
2. Simulation Engine
3. Telemetry
4. Blue Team
5. CTF
6. Assessment and retesting

## Rules of Engagement

Read [docs/ROE.md](docs/ROE.md) before performing any exercise.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md) for vulnerability reporting and safe-use requirements.

## License

MIT License. See [LICENSE](LICENSE).
