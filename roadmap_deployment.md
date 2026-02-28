# Plan d’évolution architecturel — SaaS production-grade (référence phases à venir)

Voici un plan d’évolution architecturel (sans code) pour aller vers un SaaS production-grade, en respectant strictement SoT et le gel de contrat v1.

## Executive summary

Vous avez déjà une base solide (API v1 gelée, BaseResponse unifié, JWT/RBAC, observabilité, CI/CD, séparation env).
La prochaine étape doit introduire, de manière additive et non destructive :

- Isolation multi-tenant (tenant-aware partout côté data & auth)
- Audit trail complet (traçabilité sécurité/compliance)
- Vrai worker async externe (découplage API/traitement)
- Durcissement contraintes DB (intégrité forte + perf)
- Rate limiting distribué (remplacement du in-memory)
- Feature flags gouvernés (rollout contrôlé)
- Refresh token + rotation (session security renforcée)

Le plan ci-dessous est découpé en phases atomiques, avec stratégie de migration, rollback, rollout staging→prod et risques.

## Architecture deltas

### 1) Multi-tenancy isolation

#### Cible
- Introduire un identifiant `tenant_id` au niveau :
  - JWT claims (auth context)
  - Entités Product Layer (`projects`, `documents`, `batch_runs`, `batch_items`, et `sources` si partagé non autorisé)
  - Repository queries (filtrage systématique par tenant)
- Modèle recommandé : single database, shared schema, row-level isolation.

#### Principes
- Tous les accès métiers deviennent tenant-scoped par défaut.
- Les rôles (`admin`, `user`) deviennent tenant-scoped (pas globaux plateforme, sauf super-admin explicitement séparé).

### 2) Audit trail system

#### Cible
- Table append-only `audit_events` (ou partitionnée ultérieurement).
- Événements minimum :
  - auth (login token issue/refresh/revoke, forbidden attempts)
  - actions Product Layer (create/update/delete/logical changes)
  - actions sensibles (role change, feature flag override)
- Format événement : timestamp, actor, tenant, action, target_type/id, outcome, request_id, metadata JSON.

#### Principes
- Écriture audit best-effort contrôlée (jamais casser l’API métier pour un échec audit transitoire, sauf opérations compliance critiques).

### 3) True async worker separation

#### Cible
- Séparer API process et worker process via queue externe (Redis/RabbitMQ/SQS selon infra).
- Les batch extractions deviennent jobs asynchrones :
  - API crée job + retourne immédiatement état initial (en BaseResponse inchangé)
  - Worker consomme et met à jour statut/résultat.

#### Principes
- Garder endpoints v1 compatibles : comportement additif via nouveaux champs de data, pas de rupture payload.
- Idempotence job (clé métier/job_id).

### 4) Database constraint hardening

#### Cible
- Ajouter contraintes SQL :
  - FK explicites (déjà partiel)
  - unique composites (ex: nom projet unique par tenant si exigé)
  - check constraints (status enums, chars >= 0, etc.)
  - index composites (tenant_id + created_at, tenant_id + project_id, etc.)
- Uniformiser nullability et defaults explicites.

### 5) Distributed rate limiting

#### Cible
- Remplacer l’état in-memory par backend distribué (Redis recommandé).
- Clés de quota :
  - par IP (fallback)
  - par user_id
  - par tenant_id
  - par route sensible (`/auth/*`, batch endpoints)

#### Principes
- Policy configurable par environnement.
- Fallback contrôlé si Redis indisponible (mode dégradé explicite + alerte).

### 6) Feature flag system

#### Cible
- Provider de flags (DB + cache, ou service externe).
- Scope : global / tenant / user.
- Usage : activer progressivement worker async, nouveaux contrôles de sécurité, etc.

#### Principes
- Évaluation déterministe, auditée, observable.
- Flags non critiques avec valeurs par défaut sûres.

### 7) Refresh token & rotation strategy

#### Cible
- Access token court + refresh token long stocké côté serveur (hashé).
- Rotation à chaque refresh, détection reuse (token replay protection).
- Révocation par session/device.

#### Principes
- Endpoint refresh additif, sans casser auth actuelle.
- Journalisation/audit systématique.

## Invariant lock section (non négociable)

- API v1 reste backward compatible (`/api/v1` inchangé).
- BaseResponse inchangé : `success`, `data`, `error`.
- Tous les nouveaux comportements sont additifs.
- Global error handler reste l’unique point de sérialisation erreur.
- SoT.md prioritaire sur toute décision de design.
- Validation settings via Pydantic obligatoire.
- Observabilité : logs JSON structurés + métriques Prometheus conservées.
- Séparation env local/staging/prod maintenue strictement.

## Phase-by-phase roadmap (safe merge strategy)

### Phase A — Foundations (non-fonctionnel)
- Introduire modèles/configs sans activation :
  - tenant context abstrait
  - audit abstraction
  - distributed rate limiter abstraction
  - worker queue abstraction
  - feature flag abstraction
- Ajout derrière flags désactivés.
- Merge safe : aucun comportement v1 visible.

### Phase B — DB additive migrations
- Alembic : ajouter `tenant_id`, tables `audit_events`, `refresh_tokens`, `jobs` (si besoin), indexes/constraints.
- Backfill contrôlé pour données existantes (tenant default local).
- Merge safe : code lit ancien + nouveau schéma.

### Phase C — Tenant enforcement progressive
- Activer tenant propagation dans auth claims puis repositories.
- Ajouter guardrails : requête sans tenant => erreur contractuelle.
- Mode compat staging : dual-read assertions/logging avant enforcement strict.
- Merge safe : feature flag `TENANCY_ENFORCED=false` puis true.

### Phase D — Audit trail activation
- Brancher writes audit sur actions sensibles.
- Ajouter métriques audit write success/failure.
- Merge safe : échec audit non bloquant (sauf endpoints compliance si décidés).

### Phase E — Worker externalization
- Introduire queue + worker process en staging.
- Convertir batch extraction en flow async sous feature flag.
- Maintenir endpoint contract en retournant état job compatible data.
- Merge safe : fallback sync si worker indisponible au début.

### Phase F — Distributed rate limiting
- Activer Redis limiter en staging.
- Shadow mode (compute only) puis enforce mode.
- Merge safe : fallback in-memory temporaire configurable.

### Phase G — Refresh token rotation
- Ajouter endpoints/session tables + rotation policy.
- Déployer en opt-in (frontend canary).
- Enforce progressivement expiration plus courte access tokens.

### Phase H — Hardening final + cleanup
- Retirer fallback legacy quand métriques stables.
- Verrouiller normative + SoT + architecture + runbooks.

## Migration strategy (DB + runtime)

### DB
- Uniquement migrations Alembic additives.
- Chaque migration :
  - upgrade forward-safe
  - downgrade documenté (même si partiel pour data irreversibles)
- Backfill par lots, script idempotent.
- Vérification `alembic check` en CI.

### Runtime
- Stratégie expand → migrate/backfill → contract/enforce.
- Feature flags pour activer progressivement.
- Dual-mode temporaire (legacy + new path) si nécessaire.

## Rollback strategy per phase

- A/B (foundations/DB) : rollback code simple ; DB additive laissée en place (forward-compatible).
- C (tenancy) : désactiver flag enforcement, revenir mode permissif temporaire.
- D (audit) : désactiver emission audit via flag.
- E (worker) : repasser batch en sync via flag.
- F (rate limit distribué) : fallback in-memory.
- G (refresh rotation) : désactiver rotation stricte, accepter refresh legacy pendant fenêtre de transition.
- Toujours garder rollback via image tag précédent + migration policy documentée.

## New configuration knobs required

### Tenancy
- `TENANCY_ENFORCED`
- `DEFAULT_TENANT_ID` (migration transition)

### Audit
- `AUDIT_ENABLED`
- `AUDIT_STRICT_MODE`

### Worker
- `WORKER_ENABLED`
- `QUEUE_BACKEND_URL`
- `BATCH_ASYNC_ENABLED`

### Rate limit distribué
- `RATE_LIMIT_BACKEND` (`memory|redis`)
- `RATE_LIMIT_REDIS_URL`

### Feature flags
- `FEATURE_FLAGS_BACKEND`
- `FEATURE_FLAGS_CACHE_TTL`

### Auth refresh
- `ACCESS_TOKEN_TTL_S`
- `REFRESH_TOKEN_TTL_S`
- `REFRESH_ROTATION_ENABLED`
- `REFRESH_REUSE_DETECTION`

### Sécurité
- `SECURITY_HEADERS_STRICT`
- `CORS_ALLOWED_ORIGINS` (déjà existant, à durcir prod)

Tous validés dans Settings Pydantic.

## Security implications

### Multi-tenant
- risque d’exfiltration inter-tenant → requires mandatory tenant scoping + tests de fuite.

### Refresh rotation
- vol token/replay → hash DB + rotation + reuse detection + revoke all descendants.

### Worker
- injection queue/fake jobs → signer payloads internes ou ACL réseau stricte.

### Rate limit distribué
- spoof IP → prioriser user/tenant keys si auth présente.

### Feature flags
- élévation non autorisée → accès admin-only + audit.

## Cross-cutting concerns and coupling risks

- Tenant_id propagation touche auth, repo, services, métriques, audit.
- Async worker impacte UX status/latency et observabilité.
- Rate limiting couplé auth + infra Redis.
- Feature flags peut masquer des bugs si non testés en matrice.
- Alembic + runtime fallback : risque divergence code/schéma si ordre de déploiement non respecté.

Mitigation : rollout progressif, flags, tests contractuels, canary staging.

## Risk matrix

### High — fuite inter-tenant
- Mitigation : tests isolation systématiques, policy deny-by-default.

### High — casse auth avec refresh rotation
- Mitigation : dual support window + telemetry errors 401/403.

### Medium — saturation queue worker
- Mitigation : DLQ, retries bornés, circuit breaker fallback.

### Medium — faux positifs rate limiting
- Mitigation : shadow mode + tuning par env.

### Medium — drift schéma
- Mitigation : CI `alembic check`, release checklist migration.

### Low — coût stockage audit
- Mitigation : TTL/purge policy + partitionnement ultérieur.

## Governance updates (docs to update)

### SoT.md
- Ajouter vision “Multi-tenant SaaS governance”
- Ajouter section sécurité session (refresh rotation)
- Ajouter principe rollout additif v1.

### architecture.md
- Diagramme logique tenant-aware
- Worker external process + queue
- Audit store + feature flag service
- Rate limit distribué.

### normative.md
- Règle “tenant scope obligatoire sur accès métier”
- Règle “toute action sensible doit être auditée”
- Règle “migrations Alembic only”
- Règle “flags nécessaires pour toute activation progressive”.

### implementation_plan.md
- Phases A→H ci-dessus
- critères de go/no-go par phase
- rollback checklist.

## Deployment plan (staging → production)

### Staging Phase 1 (shadow)
- deploy code + migrations additives
- tenancy/audit/rate-limit/worker en shadow mode
- métriques + logs validées.

### Staging Phase 2 (partial enforce)
- activer tenancy enforcement sur subset tenants
- activer distributed rate limit enforce
- activer refresh rotation pour users canary.

### Production Canary
- 5–10% traffic/tenants
- monitor error codes (`auth_*`, `rate_limited`, `internal_error`)
- monitor batch latency, queue depth.

### Production Generalization
- montée progressive jusqu’à 100%
- retirer fallback legacy selon SLO atteints.

### Post-rollout
- freeze de stabilité
- rapport de non-régression contractuelle v1.

## Regression risks to monitor (explicit checklist)

- Hausse 401/403 inattendue après RBAC/refresh.
- Toute fuite inter-tenant (critical blocker).
- Hausse 500 sur endpoints product.
- Explosion `rate_limited` non corrélée au trafic réel.
- Latence P95/P99 sur `/extract` et batch.
- Queue backlog / retry storms.
- Drift Alembic (autogen non vide).
- Rupture parsing frontend BaseResponse (doit rester inchangé).
