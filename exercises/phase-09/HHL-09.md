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

1. Open `http://127.0.0.1:8080`, review the preauthorized Red Team scenario and
   select the configured synthetic campaign.
2. Confirm the scope acknowledgement, start the campaign and open MailHog at
   `http://127.0.0.1:8025`.
3. Open one link for each of the five synthetic users to produce the
   campaign-wide signal. Open one user's link three additional times (four
   clicks total for that user) to produce the repeated-interaction signal.
4. Return to the dashboard and refresh telemetry and alerts.
5. Triage each alert with its supporting event IDs and choose a bounded
   training disposition.
6. Use the dashboard's CTF hints and the displayed synthetic evidence to derive
   and submit flags in prerequisite order.
7. Load the assessment, record remediation/retest actions with evidence notes,
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

## Automated reproducibility check

The CI smoke test sends the configured campaign to MailHog, follows only the
current run's local training links, and generates enough synthetic clicks to
exercise both detection rules. It derives and submits the four CTF flags in
prerequisite order, records remediation and retest evidence for each finding,
then generates a report and requires every verification control to pass.
