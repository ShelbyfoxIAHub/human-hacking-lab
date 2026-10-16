# Integrated Curriculum

Phase 17 connects the lab's existing exercises into a prerequisite-aware
learning path spanning Red Team, Blue Team, Detection Engineering, Threat
Hunting, DFIR, OSINT, AppSec, Human Risk Management, Security Engineering and
governance.

## Learning path

The bundled manifest is `apps/web/curriculum.json`. It defines modules,
prerequisites, exercise references and expected evidence. CI verifies that
every prerequisite exists, the graph is acyclic and every exercise reference
resolves to a repository artifact.

The dashboard only unlocks a module after its prerequisites are marked
complete. A learner's completion marks are:

- keyed by the synthetic learner ID already used by the CTF panel;
- stored in that browser's local storage only;
- labeled self-reported and not independently verified;
- removable with **Reiniciar progreso local**.

No progress is uploaded, shared with the services or used to calculate a
person-level risk score. Learners should mark a module complete only after
reviewing its exercise evidence criteria.

## Limitations

Local self-reported progress supports navigation, not certification. The
curriculum does not automatically verify evidence or authenticate a learner.
An instructor should separately review artifacts when formal assessment is
needed.

The manifest is available at `GET /api/curriculum/path` on the local
dashboard.
