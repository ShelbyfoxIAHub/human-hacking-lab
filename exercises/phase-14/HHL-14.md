# HHL-14 — Engineering the Lab Boundary

## Objective

Verify that the training stack is isolated by default and that its local-only
network assumptions are enforced by repeatable checks.

## Scope and safety

- Inspect only this repository's Docker Compose and CI configuration.
- Do not connect the lab to external targets or change host firewall settings.
- Do not stop or remove running containers or volumes as part of this exercise.
- If the network or port-binding controls fail, stop before running the lab.

## Exercise

1. Review the `lab` network in `infra/docker-compose.yml` and confirm that
   external egress is disabled.
2. Review every published port and confirm that it binds to `127.0.0.1`.
3. Run the Compose configuration validation and unit tests.
4. Review the CI workflow to confirm those gates run before the full Compose
   smoke test.
5. Explain how a future service should be added without weakening the network
   boundary or exposing a port to other host interfaces.

## Expected evidence

- Compose accepts the isolated network configuration.
- Regression tests confirm the network is internal and published ports are
  loopback-only.
- CI performs Compose validation before integration testing.
- The learner can state the stop condition for any egress or exposure failure.

## Completion criteria

- No external network target is contacted.
- The lab boundary remains unchanged during review.
- Conclusions distinguish these controls from a complete host or Docker
  security assessment.
