# HHL-09 — Guided Training Dashboard

## Objective

Complete a synthetic training run from the local dashboard: deliver a campaign to
MailHog, generate telemetry, review detections, progress through the CTF,
record assessment actions, generate a report and run the verification gate.

## Scope and safety

- Use only the synthetic identities and campaign shipped with the lab.
- Campaign messages remain inside the local MailHog sink.
- Do not enter real credentials, personal data or external targets.
- Dashboard PASS/FAIL describes only the defined controls and synthetic records.

## Exercise

1. Open `http://127.0.0.1:8080` and select the configured synthetic campaign.
2. Start the campaign and open MailHog at `http://127.0.0.1:8025`.
3. Open the synthetic message links. For the campaign-wide detection, links for
   at least five distinct synthetic users must be opened. Reopening one user's
   training link more than three times produces the repeated-interaction signal.
4. Return to the dashboard and refresh telemetry and alerts.
5. Use the dashboard's CTF hints and the displayed synthetic evidence to derive
   and submit flags in prerequisite order.
6. Load the assessment, record remediation/retest actions with evidence notes,
   generate the report and run verification.

## Expected evidence

- A simulator campaign run and correlated synthetic click events.
- Detection results for any satisfied deterministic rule thresholds.
- CTF score and completed challenge records for the selected student ID.
- Assessment findings and append-only action records where matching evidence
  exists.
- A generated report and a persisted verification run with its control results.

## Completion criteria

- The workflow is completed through the browser without calling backend APIs
  manually.
- The MailHog UI is reachable only at the local loopback address.
- The report and verification results refer to the same assessment ID.
- A PASS is reported as a control result only, not as a security certification.
