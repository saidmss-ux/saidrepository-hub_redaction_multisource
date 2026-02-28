# Implementation Plan (MVP Backend)

## Source of Truth
- Product scope and milestones: `SoT.md`
- JSON contract and endpoint constraints: `architecture.md`
- Non-regression and governance rules: `normative.md`
- Agent behavior constraints: `skill.md`

## Current status
- [x] Contract-first FastAPI app bootstrapped.
- [x] Required MVP endpoints implemented (`/upload`, `/download-from-url`, `/extract`, `/video-to-text`, `/ai-assist`) + `/health`.
- [x] Unified `BaseResponse` envelope used for success and functional error paths.
- [x] Basic tests for contract and core flows.

## Phase 1 — Contract hardening (current PR)
- [x] Enforce strict extract modes (`text`, `summary`) via schema validation.
- [x] Add source inspection endpoint for UI integration (`GET /source/{file_id}`).
- [x] Add source listing endpoint for dashboard/sidebar (`GET /sources`).
- [x] Expand tests for mode validation and new endpoints.

## Phase 2 — Persistence alignment (next)
- [ ] Replace in-memory `SOURCES` store with SQLite persistence.
- [ ] Add migration/bootstrap script for local DB.
- [ ] Keep endpoint contracts stable while changing storage implementation.

## Phase 3 — Extraction quality (next)
- [ ] Add parser adapters for PDF/DOCX/TXT behind deterministic interface.
- [ ] Add regression tests with fixtures for multi-format extraction.
- [ ] Add explicit error mapping for unsupported formats.

## Non-goals in MVP
- No enterprise auth/roles.
- No auto-publishing/CMS features.
- No long-form autonomous generation.

- [x] Migration du stockage mémoire vers SQLite SQLAlchemy + repository pattern.

- [x] Préfixe API `/api/v1` appliqué sur les endpoints contractuels.

- [x] Centralisation des erreurs métier via handler global `ServiceError` et contrat BaseResponse unique.

- [x] Durcissement validation upload (type + taille) et documentation backend prête frontend (`backend/README.md`).

- [x] Freeze contrat v1 (`/api/v1`) et préparation explicite du namespace `v2` sans rupture.

- [x] Observabilité production: logs structurés JSON + `x-request-id` + métriques de durée extraction.

- [x] Résilience: garde de concurrence configurable et erreur contractuelle `over_capacity`.

- [x] Couche frontend d'intégration API v1 ajoutée (client centralisé, service façade, état contractuel, retry over_capacity).


## Evolution rationale
- Added Product Layer to align with SoT Fullstack/Stabilisation roadmap (projects + batch multi-documents) while preserving API v1 contract freeze.
- Data model extended safely (additive tables only) with controlled bootstrap migration marker (`schema_migrations`).
- Service orchestration added for project batch extraction without changing existing endpoint behaviors.

- [x] Gouvernance opérationnelle ajoutée: stratégie environnements + CI/CD + rollback documenté.

- [x] Security hardening: JWT/RBAC + rate limiting + headers sécurité en middleware.
- [x] Observability level-up: endpoint `/metrics` + métriques contractuelles Prometheus.
- [x] Migration governance: base Alembic + contrôle de drift intégré en CI.

## Evolution rationale (security/observability)
- Added stateless auth and RBAC only on additive product endpoints to preserve existing v1 behavior compatibility.
- Added operational safeguards (rate limits, security headers) as middleware-level controls configurable per environment.
- Added Prometheus metrics and Alembic governance to improve production observability and schema safety.


## Phase roadmap_deployment alignment
- [x] Phase A foundations: abstractions/config knobs added (tenancy, audit, worker, distributed rate limit, feature flags).
- [x] Phase B initial additive schema: tenant columns + governance tables (`audit_events`, `refresh_tokens`, `background_jobs`, `feature_flags`).
- [x] Tenant-aware auth context and repository filtering introduced with `TENANCY_ENFORCED=false` default for safe rollout.


## Phase G roadmap_deployment
- [x] Endpoint additif `/auth/refresh` pour rotation refresh token tenant-aware.
- [x] Endpoint additif `/auth/revoke` (admin) pour révocation de sessions.
- [x] Audit auth basique ajouté (`issue/refresh/revoke`) et tests unitaires dédiés.


## Phase F roadmap_deployment
- [x] Distributed rate limit backend implémenté avec mode `redis` (counter + TTL) et fallback mémoire contrôlé.
- [x] Tests unitaires ajoutés pour voie redis (succès, blocage, fallback).
- [x] Contrat d’erreur `rate_limited` conservé via `ServiceError` + handler global.


## Phase D/E roadmap_deployment
- [x] Service feature flags implémenté (scope `tenant|global`) + endpoint admin additif `/admin/feature-flags`.
- [x] Batch orchestration branchée sur flag `batch.async.enabled` + knobs worker existants.
- [x] En mode activé, extraction batch retourne état `queued` contractuel sans casser `BaseResponse`.
