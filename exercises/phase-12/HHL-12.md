# HHL-12 — Secure AppSec Review

## Objective

Review fixed code examples, identify two common unsafe patterns and explain
how parameter binding and safe text rendering reduce risk.

## Scope and safety

- Review only the bundled source fixtures in the local dashboard.
- The service performs static pattern matching; it does not execute source.
- Do not upload code, credentials, real data or production snippets.
- The listed rules are illustrative and do not replace a full AppSec review.

## Exercise

1. Analyze `APPSEC-01` and record the rule ID, affected line and why the SQL
   value should be bound as a parameter.
2. Compare the original code with the remediated version.
3. Analyze `APPSEC-02` and explain why assigning a display value to
   `innerHTML` is unsafe.
4. Compare the `innerHTML` sink with the `textContent` remediation.
5. Analyze `APPSEC-03`. Confirm that the bundled rules report no findings,
   then state why this does not prove the sample is universally secure.

## Expected evidence

- APPSEC-R001 for the interpolated SQL example.
- APPSEC-R002 for the unsafe HTML sink.
- No findings for the remediated fixture under the bundled rules.
- A short explanation of the limits of deterministic static analysis.

## Completion criteria

- Findings cite the displayed rule IDs and line numbers.
- Remediation discussion matches the fixed code.
- The learner does not treat a clean scan as a security certification.
