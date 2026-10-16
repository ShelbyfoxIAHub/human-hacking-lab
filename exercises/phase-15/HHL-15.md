# HHL-15 — Blue Team Alert Triage

## Objective

Investigate synthetic alerts, verify their event evidence and record a
bounded training disposition in an append-only case history.

## Scope and safety

- Work only with alerts generated from the synthetic campaign.
- Do not perform containment, account changes or actions against real systems.
- Choose one of the predefined training dispositions; do not enter free-text
  personal information.
- Triage history is separate from the read-only telemetry store.

## Exercise

1. Generate enough synthetic activity to trigger HHL-D001 and HHL-D002.
2. Review each alert's campaign ID, run correlation ID and supporting event
   IDs.
3. Choose a disposition that matches the synthetic evidence.
4. Record the triage and confirm the resulting history entry contains the
   alert ID, rule ID, run ID, disposition and evidence event IDs.
5. Explain why a valid synthetic alert is not, by itself, evidence of
   malicious intent by a real person.

## Expected evidence

- HHL-D001 and/or HHL-D002 with supporting event IDs.
- A persisted triage record linked to the exact alert and campaign run.
- No user profile, free-text note or live response action in the record.

## Completion criteria

- The chosen disposition is consistent with the evidence.
- The record is append-only and stored separately from telemetry.
- Conclusions remain limited to the synthetic exercise.
