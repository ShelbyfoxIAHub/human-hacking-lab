# Secure AppSec Review

Phase 12 teaches secure-code review using fixed, bundled educational examples.
The local analyzer applies deterministic rules to source text and displays
evidence and a remediated version.

## Safety boundary

- The service analyzes only the three bundled examples.
- Learners cannot upload files, submit arbitrary source or execute code.
- No vulnerable application or externally reachable target is deployed.
- The examples contain no usable credentials, secrets or personal data.
- Findings are training signals from a small rule set, not a complete
  vulnerability assessment.

## Included rules

| Rule | Example | Remediation |
|---|---|---|
| APPSEC-R001 | Interpolated SQL query | Bind values as driver parameters |
| APPSEC-R002 | Untrusted value assigned to `innerHTML` | Render plain text with `textContent` or use an approved sanitizer |

The third example contains the remediated controls and should produce no
findings for the included rules.

## Dashboard workflow

1. Select an AppSec module in the local dashboard.
2. Review the static finding, affected line and remediation guidance.
3. Compare the original fixture with its remediated code.
4. Analyze `APPSEC-03` and confirm that the fixed sample passes these rules.
5. Explain why a clean result from a small rule set is not proof that software
   is free of vulnerabilities.

## API

```bash
curl http://127.0.0.1:8097/health
curl http://127.0.0.1:8097/modules
curl 'http://127.0.0.1:8097/analyze?id=APPSEC-01'
```

Only known module IDs are accepted. The dashboard uses a same-origin,
allowlisted proxy, and the service is bound to the local lab stack.
