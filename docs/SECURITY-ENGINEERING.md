# Security Engineering and Lab Isolation

Phase 14 turns the lab's local-only rule into an infrastructure control and a
continuous-integration regression gate.

## Network controls

- Docker Compose defines `hhl-isolated` as an internal bridge network for
  service-to-service lab traffic.
- Only the dashboard and MailHog join `hhl-host-access`, a second bridge with
  IP masquerading disabled, so the host can reach their explicitly published
  loopback ports.
- Disabling masquerading reduces outbound reachability but is not a formal
  guarantee that a container cannot route traffic outside the lab. Use host
  firewall egress rules if a strict no-egress guarantee is required.
- Published service ports must bind to `127.0.0.1`; they are not exposed on
  other host interfaces.
- Service-to-service communication stays on the internal Compose network.
- Each image uses its application directory as the build context; the simulator
  receives only the synthetic user-data directory as an additional context.
- Build definitions are inline in Compose and use each application's directory
  as context, avoiding external Dockerfile reads and broad repository-root
  contexts.
- CI validates the Compose model before starting the end-to-end smoke test.
- Regression tests reject host-network mode and any non-loopback port binding.

## Reproduce the checks

```bash
docker compose -f infra/docker-compose.yml config --quiet
python -m unittest discover -s tests -p "test_*.py"
```

CI runs these checks before starting the local training stack. The integration
smoke then validates the synthetic campaign, OSINT/AppSec/HRM modules,
detections, threat hunts, DFIR timeline, CTF, assessment, report and
verification workflow.

## Limitations and response

These controls reduce accidental external access; they do not replace host
firewall policy, Docker daemon security, endpoint protections or review of
future Compose changes. If traffic leaves the lab, if any port is no longer
loopback-bound, or if the non-masquerading access network is widened beyond
the dashboard and MailHog, stop the exercise and restore the intended
configuration before continuing.
