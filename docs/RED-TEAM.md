# Controlled Red Team Scenario

Phase 16 packages the existing synthetic campaign as a bounded, preauthorized
Red Team exercise. It does not add exploit execution, arbitrary targets or
external delivery.

## Scenario HHL-RT-01

- Objective: validate correlated synthetic delivery, click and detection
  evidence.
- Scope: the five bundled synthetic identities, the preconfigured HHL02-A
  message and local MailHog.
- Permitted: send that message, open its local training links and review the
  resulting telemetry.
- Prohibited: real people, credential collection, external targets or
  infrastructure, arbitrary templates and exploit execution.
- Stop conditions: any real identity or credential appears, traffic leaves
  the isolated lab network, or messages are not contained by MailHog.

The dashboard displays this scenario and requires the learner to acknowledge
the scope before enabling its campaign button. This is a training hold point;
the actual safety boundary is enforced by the fixed simulator configuration,
loopback bindings and internal Docker network.

## Reproduce

1. Review `/api/red-team/scenarios` or the campaign panel.
2. Acknowledge the synthetic-only scope.
3. Launch the configured campaign and keep delivery inside local MailHog.
4. Confirm the resulting campaign correlation ID and expected detection
   evidence.
5. Stop immediately if any stated stop condition occurs.

The simulation does not accept credentials, arbitrary email content or
external target parameters.
