# HHL-02 — Controlled Campaign Simulation

## Objective

Operate a synthetic campaign entirely inside the lab and analyze the resulting interaction telemetry.

## Start

From the repository root:

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

Send the predefined campaign to the local MailHog sink:

```bash
curl -X POST http://127.0.0.1:8090/campaigns/HHL02-A/send
```

Open MailHog:

```text
http://127.0.0.1:8025
```

## Tasks

1. Identify the synthetic recipient and campaign.
2. Inspect the message without submitting any credentials.
3. Follow the training link.
4. Observe the recorded `clicked` event.
5. Query campaign metrics:

```bash
curl http://127.0.0.1:8090/campaigns/HHL02-A/summary
```

6. Explain which telemetry is useful for a Blue Team.

## Event model

```text
delivered -> opened -> clicked -> reported
```

Only `delivered` and `clicked` are generated automatically in this phase. The remaining events are supported by the event API for later exercises.

## Safety

- All recipients are synthetic.
- Mail is captured by MailHog.
- No external SMTP service is used.
- The training page never accepts credentials.
