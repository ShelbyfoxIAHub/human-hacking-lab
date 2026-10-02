# HHL-06 — Assessment, Remediation and Retest

## Scope
Local synthetic Human Hacking Lab only. No real credentials, personal data, third-party targets or external messaging.

## Start
docker compose -f infra/docker-compose.yml up -d --build
curl http://127.0.0.1:8093/health

## Assessment
Generate a synthetic run that triggers HHL-D001 or HHL-D002, then:
curl 'http://127.0.0.1:8093/assessments?id=ASM-STUDENT-01'

For each finding record source rule, synthetic campaign/correlation ID, evidence IDs/users, observed condition, unknowns and contextual severity.

## Remediation
POST /actions with action_type=REMEDIATION. Do not mark VERIFIED without controlled evidence.

## Retest
Replay the synthetic scenario and record POST /actions with action_type=RETEST, documenting whether the condition reproduced.

## Deliverable
Scope, methodology, findings, evidence, risk context, remediation, retest, residual risk and limitations.
