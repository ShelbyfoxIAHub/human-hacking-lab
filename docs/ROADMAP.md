# Roadmap

## Phase 01 — Foundation
- Docker Compose
- isolated network
- educational web portal
- local SMTP sink
- synthetic identities
- initial exercises

## Phase 02 — Simulation Engine
- synthetic campaigns
- local SMTP delivery
- controlled landing page
- event ingestion
- campaign metrics
- SQLite persistence
- automated artifact tests
- no credential collection

## Phase 03 — Telemetry
- versioned event schema
- UTC timestamps
- correlation IDs
- structured JSON logs
- SQLite WAL persistence
- token hashing and migration
- sanitized event API
- telemetry exercise
- CI validation

## Phase 04 — Blue Team / Detection Engineering
- deterministic detection service
- explainable detection rules
- alert evidence
- analyst investigation exercise
- isolated read-only telemetry access
- reproducible rule evaluation

## Phase 05 — CTF
- progressive forensic challenges
- synthetic flags derived from evidence
- deterministic flag validation
- one-time player scoring
- local leaderboard
- separate score persistence
- read-only telemetry boundary

## Phase 06 — Assessment
- evidence-derived findings
- contextual severity
- bounded risk calculation
- remediation records
- retest records
- residual-risk calculation
- separate assessment persistence
- read-only telemetry boundary

## Phase 07 — Reporting / Governance
- assessment report generation
- evidence index
- executive summary
- remediation tracking
- append-only audit trail
- JSON/Markdown export artifacts
- residual-risk register
- read-only assessment boundary

## Phase 08 — Control Verification / Regression Gate — current
- control verification service
- assessment/reporting read-only boundaries
- structured control evidence
- canonical verification content hash
- reproducible PASS/FAIL regression gate
- persisted verification runs
- synthetic audit-ready evidence

## Phase 09 — Guided Instructor / Learner Dashboard — in progress
- local browser dashboard for the complete synthetic training flow
- campaign launch through the simulator and local MailHog
- telemetry and detection review
- learner CTF progress, hints and flag submission
- assessment findings and evidence-backed remediation/retest actions
- report generation followed by control verification
- explicit service errors and same-origin, allowlisted API proxy
- browser flow remains local-only; no real credentials or external delivery
- Compose-stack smoke validation in CI for local OSINT, MailHog clicks, detection and hunt evidence, DFIR timeline, all CTF challenges, assessment actions, reporting and verification

## Phase 10 — Threat Hunting / DFIR — in progress
- deterministic hunt hypotheses over synthetic telemetry
- evidence-linked findings with run and event identifiers
- read-only incident timeline reconstruction by correlation ID
- local dashboard review for hunt matches and event sequences
- repeatable threshold-driven exercise and CI smoke validation

## Phase 11 — Synthetic OSINT — in progress
- offline synthetic source catalog using reserved `.invalid` domains
- bounded same-origin search with query allowlisting
- entity correlation with source provenance and confidence labels
- local learner workflow with no external lookups or real personal data
- repeatable catalog-search smoke coverage

## Phase 12 — Secure AppSec Review — in progress
- bundled static-analysis fixtures for common secure-coding issues
- deterministic findings with line numbers and remediation guidance
- paired fixed examples for regression comparison
- no arbitrary uploads, code execution or exposed vulnerable application
- local dashboard and CI validation of unsafe and remediated examples

## Phase 13 — Privacy-Safe Human Risk Management — in progress
- aggregate synthetic campaign metrics only
- minimum cohort size of five with suppression below threshold
- no learner profiles, individual scores or ranking
- explicit caveats separating behavior metrics from learning and risk
- read-only telemetry access and dashboard/CI validation

## Phase 14 — Security Engineering / Lab Isolation — in progress
- Docker lab network configured with external egress disabled
- all published lab ports regression-checked for loopback binding
- Compose configuration validation runs before the CI integration smoke
- safe-use and stop conditions documented for the network boundary

## Phase 15 — Blue Team Alert Triage — in progress
- evidence event IDs attached to campaign-wide alerts
- bounded synthetic triage dispositions with no live response actions
- separate append-only triage store; telemetry remains read-only
- dashboard review and CI smoke coverage for evidence-linked triage

## Phase 16 — Controlled Red Team Scenario — in progress
- fixed preauthorized scenario mapped to the bundled synthetic campaign
- explicit scope, permitted/prohibited actions and stop conditions
- dashboard scope acknowledgement before campaign launch
- MailHog-only delivery and no credential capture or external targets
- scenario metadata and safety boundary covered by CI

## Phase 17 — Integrated Curriculum — in progress
- ordered learning modules for all requested security tracks
- prerequisite graph validated against exercise artifacts
- visible expected evidence and completion criteria per module
- local learner progress keyed only by a synthetic learner ID
- progress explicitly labeled self-reported and not independently verified
