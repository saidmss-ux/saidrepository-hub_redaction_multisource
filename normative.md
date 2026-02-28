# Normative — Règles Immuables

## Contrats Techniques Obligatoires

- Tous endpoints doivent retourner JSON structuré
- Aucun module ne peut être ajouté sans documentation
- Structure dossiers immuable sauf mise à jour ici

---

## Comportement IA

- Ne peut modifier vision sans validation humaine
- Ne peut ajouter dépendance non documentée
- Toute suggestion doit être tracée

---

## Workflow Conformité

- Test → Correction → Commit obligatoire
- Refactor global interdit sans plan validé
- Feature interdite pendant correction bug

---

## Documentation

Toute modification technique doit être reflétée dans :
- SoT.md
- architecture.md
- normative.md

---

## Versioning & Validation

- Version obligatoire pour chaque release
- Tests unitaires avant merge
- Build interdit si contrat JSON non respecté

## Traçabilité des changements

- Toute évolution backend doit préserver `BaseResponse` comme contrat de sortie standard.
- Les endpoints ajoutés/modifiés doivent être couverts par des tests API minimaux.

- Les erreurs fonctionnelles doivent rester contractuelles (`success=false`, `error` explicite) au lieu de réponses non structurées.

- Le fichier `implementation_plan.md` doit être mis à jour à chaque avancée majeure d'implémentation.

- Les routers ne doivent contenir aucune logique SQL directe; accès DB uniquement via repository + services.

- Toute erreur métier doit remonter via `ServiceError` puis être sérialisée en `BaseResponse` par handler global.

- Le contrat `BaseResponse` doit aussi s'appliquer aux erreurs de surcharge (`over_capacity`) et aux erreurs globales non prévues.

- Le frontend doit consommer uniquement des réponses enveloppées `BaseResponse` via un client API centralisé.


- Toute évolution de modèle doit être additive et traçable (migration contrôlée) pour éviter rupture de compatibilité.

- Les paramètres runtime doivent être environment-driven et validés; aucune valeur critique hardcodée hors fallback local.

- Toute nouvelle route métier sensible doit appliquer auth JWT + RBAC sans modifier le contrat BaseResponse existant.
- Les évolutions de schéma passent par Alembic avec contrôle de drift en CI.
