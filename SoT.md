# Statement of Truth (SoT)

## Vision & Objectif

- Problème à résoudre :
Les créateurs de contenu (étudiants, blogueurs, copywriters, journalistes indépendants)
perdent du temps à jongler entre plusieurs outils pour :
  - importer des documents
  - extraire du contenu
  - structurer leurs sources
  - rédiger
  - reformuler
  - convertir audio/vidéo en texte

Il n’existe pas d’interface unique simple, type ChatGPT,
permettant de centraliser sources + rédaction + extraction + assistance IA optionnelle.

- Utilisateur cible :
Créateurs solo (étudiants, blogueurs, copywriters débutants/intermédiaires),
qui veulent produire du contenu plus vite et potentiellement générer des revenus.

- Mesure de succès :
  - 1ère validation : 50 utilisateurs actifs test MVP
  - Temps moyen de création réduit d’au moins 30%
  - Activation clé API IA > 20% des utilisateurs

- Ce qui est explicitement exclu :
  - CMS complet
  - Gestion SEO avancée
  - Publication automatique
  - Génération de contenu long 100% automatique
  - Fonctionnalités enterprise

---

## Roadmap Produit

### Prototype

Objectif minimal viable :
- Import PDF
- Extraction texte
- Affichage parallèle source + éditeur
- Copie manuelle vers zone rédaction

Fonction démontrée :
Un utilisateur peut importer un PDF et rédiger à partir de celui-ci dans la même interface.

---

### V1 — MVP

- Endpoints API contractuels :
  - POST /upload
  - POST /download-from-url
  - POST /extract
  - POST /video-to-text
  - POST /ai-assist

- Interfaces frontend :
  - Dashboard minimal
  - Liste des sources (sidebar)
  - Zone rédaction principale
  - Barre d’outils (copie/coupe/lien/extraction)
  - Activation clé API

- Validation & tests minimaux :
  - Extraction correcte PDF/DOCX/TXT
  - Téléchargement HTTP valide
  - Injection IA fonctionnelle si clé valide

---

### Fullstack / Stabilisation

- Mini système de projets
- Historique local (SQLite)
- Batch multi-documents
- UI stabilisée
- Tests unitaires extraction + parsing
- Build Desktop via Tauri

---

## Workflow de Développement

1. Définir contrats JSON
2. Implémenter extraction PDF
3. Implémenter éditeur
4. Test → Correction → Commit
5. Documentation mise à jour
6. Ajouter modules progressivement

---

### Interdits / Anti-pattern

- Refactor global en phase instable
- Ajouter IA complexe avant stabilisation extraction
- Changer architecture sans mise à jour SoT
- Multiplier formats sans tests

---

## Indicateurs & QA

- Validation JSON automatique
- Tests extraction minimum 3 formats
- Test échec téléchargement HTTP
- Pas de build sans validation endpoint

## Statut d’implémentation actuel

- Backend MVP FastAPI initialisé avec endpoints contractuels : `/upload`, `/download-from-url`, `/extract`, `/video-to-text`, `/ai-assist` + `/health`.
- Contrat de réponse unifié `BaseResponse` appliqué à tous les endpoints.
- Tests API de base ajoutés pour validation de contrat et gestion d’erreur 422.

- Le flux MVP couvre maintenant upload -> stockage mémoire -> extraction avec gestion d’erreur structurée (`success=false`).
- Endpoint `/ai-assist` gère explicitement les cas clé API désactivée via contrat JSON stable.

- Plan d'exécution détaillé maintenu dans `implementation_plan.md` pour suivi des phases backend.

- Backend stabilisé en architecture modulaire (routers/services/repository) avec persistance SQLite pour le MVP.

- Stabilisation backend orientée intégration frontend: contrat erreur unifié et documentation API backend dédiée.

- Backend prêt intégration fullstack contrôlée: observabilité structurée, request ID, et protection surcharge configurable.

- Intégration frontend-backend renforcée via couche client API v1 centralisée et mapping d'erreurs contractuel.


- Product Layer introduite (Project/Document/Batch) en alignement strict avec la roadmap Fullstack/Stabilisation, sans rupture du contrat API v1.


## Operational Governance

- Environnements séparés et explicités : `local`, `staging`, `production`.
- Configuration pilotée par variables d’environnement validées strictement.
- Local = SQLite ; staging/production = PostgreSQL.
- CI/CD bloque toute intégration si tests backend/frontend échouent.
- Déploiement staging via branche `staging`; production via `main` ou tag versionné.
- Migration DB non destructive et traçable via Alembic (révisions additives).

- Operational hardening ajouté: JWT+RBAC, rate limiting, métriques Prometheus, gouvernance Alembic sans rupture API v1.

- Foundations multi-tenant/audit/worker/feature-flags ajoutées de façon additive (flags désactivés par défaut).

- Session security avancée démarrée en mode additif: endpoints `/auth/refresh` et `/auth/revoke` + rotation contrôlée par configuration, sans rupture du contrat `BaseResponse`.

- Rate limiting distribué avancé: backend Redis opérationnel avec fallback mémoire sans rupture API v1.
