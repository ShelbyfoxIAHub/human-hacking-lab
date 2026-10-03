# HHL-07 — Reporting and Governance

## Scope
Local synthetic Human Hacking Lab only. Do not use real credentials, personal data, third-party targets or external messaging.

## Objective
Produce an evidence-backed assessment report and governance trail without inventing evidence.

## Procedure
1. Start: `docker compose -f infra/docker-compose.yml up -d --build`
2. Verify: `curl http://127.0.0.1:8094/health`
3. Create or reuse a Phase 06 assessment: `curl 'http://127.0.0.1:8093/assessments?id=ASM-STUDENT-01'`
4. Generate: `curl 'http://127.0.0.1:8094/reports?id=ASM-STUDENT-01'`
5. Inspect evidence: `curl 'http://127.0.0.1:8094/evidence?id=ASM-STUDENT-01'`
6. Inspect residual risk: `curl 'http://127.0.0.1:8094/residual-risk?id=ASM-STUDENT-01'`
7. Inspect audit: `curl 'http://127.0.0.1:8094/audit?id=ASM-STUDENT-01'`

## Deliverable
- scope and limitations
- executive summary
- findings with source rule and evidence
- evidence index
- remediation/retest tracking
- residual-risk register
- audit trail
- generated Markdown and JSON artifact identifiers

## Analyst questions
- Which statements are directly observed versus derived?
- Which event IDs support each finding?
- Which remediation actions are VERIFIED?
- Which retest actions exist, and what do they prove?
- What remains unknown?
- What evidence would invalidate or change the finding?
