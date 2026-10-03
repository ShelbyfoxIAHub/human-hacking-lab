# HHL-08 — Control Verification / Regression Gate

## Scope
Local synthetic Human Hacking Lab only.

## Procedure
1. Start the lab with Docker Compose.
2. Verify `curl http://127.0.0.1:8095/health`.
3. Generate a Phase 06 assessment and Phase 07 report.
4. Run `curl 'http://127.0.0.1:8095/verify?id=ASM-STUDENT-01'`.
5. Record the run ID, control statuses, evidence and content hash.
6. Inspect the run through `/runs/<RUN_ID>`.

## Analyst questions
- Which controls are directly verified?
- Which records are the evidence source?
- What condition caused any FAIL?
- Does PASS mean security was proven, or only that the defined invariants passed?
- What regression would invalidate the gate?

## Deliverable
Produce a verification record containing scope, controls, evidence, status, limitations and residual unknowns.
