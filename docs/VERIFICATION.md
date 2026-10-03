# Phase 08 — Control Verification / Audit Gates

Phase 08 verifies governance invariants from Phases 06–07 and creates reproducible regression-gate evidence.

## Flow
Assessment -> Reporting -> Verification Controls -> Regression Gate -> Verification Run

## Controls
- HHL-V001: assessment evidence integrity.
- HHL-V002: remediation/retest linkage.
- HHL-V003: reporting audit integrity.
- HHL-V004: regression gate; PASS requires zero failed controls.

The service is read-only against Assessment and Reporting databases. Verification results are stored separately.

## API
```bash
curl http://127.0.0.1:8095/health
curl http://127.0.0.1:8095/controls
curl 'http://127.0.0.1:8095/verify?id=ASM-STUDENT-01'
curl 'http://127.0.0.1:8095/runs/<RUN_ID>'
```

A verification run is evidence, not a declaration that the lab is secure. PASS means only that the defined checks passed against the available synthetic records at verification time.

## Evidence
Each run stores a canonical content hash, individual control results and structured evidence. No credentials, external targets or external messaging are involved.
