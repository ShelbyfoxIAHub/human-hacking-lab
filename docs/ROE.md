# Rules of Engagement

## Scope

All exercises in this repository operate inside the Human Hacking Lab.

## Allowed

- Synthetic identities.
- Synthetic email addresses.
- `.invalid` domains and localhost.
- Lab-owned Docker containers.
- Test messages captured by the local SMTP sink.
- Synthetic telemetry and evidence.

## Prohibited

- Contacting real people.
- Sending simulated phishing messages to external recipients.
- Collecting real passwords or authentication tokens.
- Processing unnecessary personal data.
- Testing third-party infrastructure.
- Exfiltrating information outside the lab.

## Stop conditions

Stop immediately if:

- traffic leaves the intended lab network;
- a real identity or credential is introduced;
- a test could affect a system outside the authorized scope;
- the exercise becomes irreversible or destructive.

## Evidence principle

Record what was observed, how it was verified, what evidence exists, and what remains unknown. Never claim a control is secure solely because an exercise produced no finding.
