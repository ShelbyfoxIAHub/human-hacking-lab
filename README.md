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

## Phase 01 — Foundation

The first release provides:

- Docker-based isolated lab network
- Educational web application
- Local SMTP capture with MailHog
- Synthetic user dataset
- Rules of Engagement
- Initial practical exercises
- Reproducible local deployment

### Quick start

```bash
git clone https://github.com/ShelbyfoxIAHub/human-hacking-lab.git
cd human-hacking-lab
docker compose -f infra/docker-compose.yml up -d --build
```

Open:

- Lab portal: http://127.0.0.1:8080
- MailHog: http://127.0.0.1:8025

Stop the lab:

```bash
docker compose -f infra/docker-compose.yml down
```

## Repository structure

```text
human-hacking-lab/
├── .github/workflows/   # CI
├── apps/                # Lab applications
├── infra/               # Docker/infrastructure
├── scenarios/           # Synthetic identities and scenarios
├── exercises/           # Student exercises
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
