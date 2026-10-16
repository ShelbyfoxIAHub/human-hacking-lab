# HHL-10 — Threat Hunting and DFIR

## Objective

Investigate a synthetic campaign by testing deterministic hunt hypotheses and
reconstructing its event timeline from evidence.

## Scope and safety

- Use only the shipped synthetic identities, campaign and local MailHog sink.
- Do not introduce real accounts, personal data, credentials or external
  targets.
- Hunt matches are bounded training hypotheses, not incident declarations.
- The timeline is read-only and contains only sanitized synthetic telemetry.

## Exercise

1. From the local dashboard, send the configured synthetic campaign.
2. Open one training link for each of the five synthetic users in MailHog.
   Open one user's link three more times to satisfy the repeated-activity
   hypothesis.
3. Return to the dashboard and refresh events and alerts.
4. Review HHL-H001, HHL-H002 and HHL-H003. Record which runs match, which
   synthetic users are involved and the supporting event IDs.
5. Select the matching run in **Reconstrucción temporal DFIR**.
6. Describe the ordering of delivery and click events, then state which
   hypotheses are supported by the timeline evidence.

## Expected evidence

- A campaign run identified by its correlation ID.
- Evidence-linked matches for repeated-user and campaign-wide activity.
- A compound hunt match when both conditions occur in the same run.
- A chronological timeline containing only events from the selected run.

## Completion criteria

- Conclusions cite event IDs and are consistent with the selected timeline.
- The exercise remains within the synthetic, loopback-bound lab.
- No hunt result is described as proof about a real person or external system.
- The learner distinguishes an evidence-backed hypothesis from an
  independently confirmed incident.
