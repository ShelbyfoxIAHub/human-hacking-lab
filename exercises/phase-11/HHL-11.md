# HHL-11 — Synthetic OSINT Correlation

## Objective

Find and correlate synthetic public-footprint artifacts while documenting
source provenance and keeping observations separate from inference.

## Scope and safety

- Search only through the local Human Hacking Lab catalog.
- All organizations, handles, domains and records are fabricated.
- `.invalid` hostnames are fixtures and must not be treated as live targets.
- Do not browse to a result, run DNS lookups, contact a platform or add real
  personal data.

## Exercise

1. Search for `analyst-amber` in the dashboard's OSINT section.
2. Record the source IDs, observation timestamps, collection methods and
   related synthetic entity IDs.
3. Search for `staging.northstar-lab.invalid`; compare the simulated DNS and
   repository records.
4. Search for `northstar-lab.invalid` and identify additional records tied to
   the synthetic organization.
5. Write a short finding that separates catalog observations from your
   inference, includes source provenance and describes one data-minimization
   control that would reduce unnecessary public exposure.

## Expected evidence

- Correlated source records that share `SYN-PERSON-001` or `SYN-ORG-001`.
- Source IDs, timestamps and collection methods supporting each observation.
- A bounded conclusion that does not treat simulated records as live
  intelligence.

## Completion criteria

- Every claim in the finding cites at least one source ID.
- Observations and inferences are clearly distinguished.
- The investigation uses no external lookups or real personal data.
