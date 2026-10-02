# Phase 06 — Assessment Engine

Phase 06 converts synthetic telemetry and detection evidence into a reproducible assessment workflow.

## Lifecycle
Telemetry -> Detection Evidence -> Findings -> Risk Context -> Remediation -> Retest -> Residual Risk

## Findings
HHL-F001 derives from HHL-D001: one synthetic user generated more than three clicks.
HHL-F002 derives from HHL-D002: at least five distinct synthetic users generated clicks.

Every finding contains an assessment ID, source template, campaign, correlation ID, severity, status and concrete synthetic evidence.

## Risk context
Weights: CRITICAL 10, HIGH 8, MEDIUM 5, LOW 2, INFO 0.
These values are training weights only. They are not CVSS, probability estimates, or production security scores.

Residual risk remains until a remediation action is explicitly recorded as VERIFIED.

## API
curl http://127.0.0.1:8093/health
curl http://127.0.0.1:8093/templates
curl 'http://127.0.0.1:8093/assessments?id=ASM-DEMO'
curl 'http://127.0.0.1:8093/risk?id=ASM-DEMO'

Record remediation/retest:
curl -X POST http://127.0.0.1:8093/actions -H 'Content-Type: application/json' -d '{"finding_id":"<ID>","action_type":"REMEDIATION","description":"Controlled lab change","status":"VERIFIED","evidence":{"test":"replay"}}'

A valid report must state observed evidence, verification method, unknowns, invalidating conditions, remediation evidence, retest evidence and residual risk. Never state that the overall system is secure.
