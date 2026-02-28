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
