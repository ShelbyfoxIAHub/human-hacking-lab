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

## Temporary Docker compatibility adjustments

The local Docker Desktop validation environment used Docker Compose v5.6.0 and
Buildx v0.37.2. In that combination, Compose/Bake requested extra
`fs.read` permissions for local Dockerfiles and stopped the build. This
matches [Compose issue #14285](https://github.com/docker/compose/issues/14285);
the fix was merged in [PR #14325](https://github.com/docker/compose/pull/14325)
but was not in the stable Compose release available during validation on
2026-10-16.

Until a released Compose version includes that fix, `infra/docker-compose.yml`
uses `dockerfile_inline` and keeps each build context scoped to its service
directory. The simulator receives only `scenarios/` as an additional context.
This avoids separate Dockerfile path reads without disabling BuildKit
permission checks or granting broader repository access. Compose is currently
the canonical build definition.

The `host-access` network is also an operational adjustment: a fully internal
Docker network did not publish ports to the Windows host. Only the dashboard
and MailHog join the extra bridge, and their published ports remain bound to
loopback. IP masquerading is disabled to reduce outbound reachability; this
must not be described as a guarantee of zero egress.

### Revisit after updating Docker tools

After installing a stable Compose release that includes PR #14325:

1. Confirm the version with `docker compose version`.
2. Restore standalone Dockerfiles under the service directories and point each
   Compose build at its in-context `Dockerfile`; keep the per-service contexts
   and the simulator's narrow `scenarios/` additional context.
3. Run `docker compose -f infra/docker-compose.yml config --quiet`,
   `python -m unittest discover -s tests -p "test_*.py"` and
   `python tests/smoke_dashboard.py` against a freshly started stack.
4. Keep the host-access network only if local host ports still require it;
   preserve loopback bindings and review the egress caveat independently.

Do not remove the inline workaround until the standard build path passes these
checks. Do not disable filesystem-entitlement checks globally as a substitute.

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
