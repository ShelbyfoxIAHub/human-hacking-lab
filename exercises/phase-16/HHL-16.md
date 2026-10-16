# HHL-16 — Preauthorized Red Team Simulation

## Objective

Plan and run a controlled social-engineering simulation against synthetic
identities, then confirm that the blue-team telemetry contains evidence for
the exercise.

## Scope and safety

- Use only scenario HHL-RT-01 and campaign HHL02-A.
- Delivery is restricted to the local MailHog sink.
- No real identities, credentials, external targets or arbitrary content.
- The dashboard scope acknowledgement is a training hold point; the
  configuration and isolated network enforce the technical boundary.
- Stop if a real identity or credential is introduced or traffic leaves the
  lab network.

## Exercise

1. Review HHL-RT-01's objective, scope, permitted actions, prohibited actions
   and stop conditions.
2. Confirm that the target set consists only of the five bundled synthetic
   identities.
3. Acknowledge the local-only scope in the dashboard and send the campaign.
4. Use local MailHog to follow the synthetic links needed to meet the
   HHL-D001 and HHL-D002 thresholds.
5. Correlate the run ID with the Blue Team alert evidence and record a
   training disposition.
6. Debrief whether the objective was met and whether any stop condition was
   approached.

## Expected evidence

- A preapproved scenario ID and campaign correlation ID.
- Delivery only to MailHog.
- Detection alerts with supporting event IDs and a linked triage record.
- A debrief that stays within the synthetic training scope.

## Completion criteria

- The engagement follows the defined scope and stop conditions.
- No credentials are requested or stored.
- Red Team success is measured by the agreed synthetic objective and evidence,
  not by real-world access or impact.
