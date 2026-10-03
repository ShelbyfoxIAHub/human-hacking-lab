# Phase 07 — Reporting / Governance

Phase 07 converts Phase 06 assessment state into reproducible governance artifacts.

## Flow
Assessment -> Report -> Evidence Index -> Remediation Tracking -> Residual-Risk Register -> Audit Trail -> JSON/Markdown Artifacts

## Scope
The service is local-only and consumes synthetic lab records. It does not contact external systems, identities, credentials or messaging infrastructure.

## Data boundaries
- Assessment DB: read-only.
- Telemetry DB: not modified and not queried directly by the reporting service; evidence references originate from the assessment DB.
- Reporting DB: separate writable persistence for report metadata and append-only audit records.
- Export directory: dedicated writable volume.

## API
```bash
curl http://127.0.0.1:8094/health
curl 'http://127.0.0.1:8094/reports?id=ASM-STUDENT-01'
curl 'http://127.0.0.1:8094/evidence?id=ASM-STUDENT-01'
curl 'http://127.0.0.1:8094/residual-risk?id=ASM-STUDENT-01'
curl 'http://127.0.0.1:8094/audit?id=ASM-STUDENT-01'
```

The report identifier is derived from report content. JSON and Markdown exports are written to a dedicated report volume.

## Evidence model
The report retains synthetic telemetry event IDs, campaign IDs, correlation IDs, synthetic user identifiers, remediation/retest action IDs and recorded action evidence. Unknowns and limitations remain explicit.

## Audit trail
Audit records are append-only at the database layer. UPDATE and DELETE operations on the audit table are rejected by SQLite triggers.

## Residual risk
The register mirrors Phase 06 semantics: residual weight is reduced by VERIFIED remediation or CLOSED finding status. Retest evidence is tracked but does not independently reduce residual risk in the current Phase 06 implementation.

Training weights are contextual only and are not CVSS, probability estimates or production security scores.
