# HHL-04 — Detection Engineering

## Objective

Build and investigate alerts generated from synthetic Human Hacking Lab telemetry.

## Start

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

Generate a synthetic campaign:

```bash
curl -X POST http://127.0.0.1:8090/campaigns/HHL02-A/send
```

Inspect rules:

```bash
curl http://127.0.0.1:8091/rules
```

Inspect alerts:

```bash
curl 'http://127.0.0.1:8091/alerts?campaign=HHL02-A'
```

## Student tasks

1. Identify the rule that generated an alert.
2. Trace every referenced event ID back to telemetry.
3. Validate the correlation ID.
4. State what evidence is present and what is missing.
5. Propose a containment action limited to the synthetic lab.
6. Write a false-positive hypothesis.

## Expected analyst output

- alert ID
- rule ID
- severity
- affected synthetic campaign
- correlation ID
- evidence
- hypothesis
- containment
- limitations

## Safety

This exercise uses synthetic identities, local services and non-production data.
