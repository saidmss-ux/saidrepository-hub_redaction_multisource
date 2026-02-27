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
