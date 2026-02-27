# saidrepository-hub_redaction_multisource# DocuHub — Documentation & Extraction Hub

DocuHub est une application web et desktop (via Tauri) qui centralise :
- l’importation de documents (PDF, Word, Excel, TXT)
- l’extraction de contenu texte, images, tableaux
- la structuration visuelle des sources
- un éditeur rédactionnel interactif (type ChatGPT)
- l’intégration de vidéos en texte
- une assistance IA optionnelle via clé API

Objectif : rendre la création de contenu documentaire rapide, fluide et productive.

---

## 🚀 Fonctionnalités principales

- **Import multi-format** : fichiers locaux ou téléchargés via URL  
- **Extraction intelligente** : texte, images, tableaux  
- **Éditeur visuel** : affichage parallèle des sources  
- **Barre outil interactive** : copier/couper, ajouter hyperliens  
- **Assistant IA intégré** (via clé API externe)
- **Video → texte** (module optionnel)

---

## 📦 Architecture

Le projet est structuré en modules clairs :
/backend
/frontend
/db
/integration
/tests
/docs


Le backend utilise FastAPI avec des contrats JSON stricts.  
Le frontend est basé sur React + TypeScript.  
La version desktop utilise Tauri.  

Tous les contrats JSON sont définis dans `architecture.md` et validés par des modèles Pydantic.

---

## 🛠️ Prérequis

- Python >= 3.10  
- Node.js >= 18  
- SQLite (pour MVP)  
- TanStack (React + TypeScript)  
- Tauri (pour builds desktop)

---

## 🔧 Installation

**Backend**

```bash
cd backend
poetry install
uvicorn main:app --reload

Frontend

cd frontend
npm install
npm run dev

Desktop Build (Tauri)

cd app
npm install
npm run tauri build
📘 Documentation

Tous les aspects architecturaux, fonctionnels et contractuels sont dans :

docs/SoT.md — Vision & Roadmap

docs/architecture.md — Architecture système

docs/normative.md — Règles immuables

docs/skill.md — Rôles IA & contraintes

docs/agent_environment.md — Environnement d’agent Codex

🧪 Tests

Les tests automatisés sont gérés via :

Backend

pytest

Frontend

npm run test

Chaque endpoint doit être validé contre les contrats JSON directement exposés en API.

📈 Processus de Contribution

Dupliquer le repository

Suivre docs/agent_environment.md

Respecter les contrats JSON dans architecture.md

Créer une branche dédiée pour chaque module

Ajouter tests unitaires avant merge

CR obligatoire avant merge

📬 License

DocuHub est open-source et distribué sous licence MIT.


---

✨ En résumé :

- **Modèle Codex conseillé : GPT-5.3-Codex** pour puissance et cohérence, avec **GPT-5.1-Codex-Max** comme excellent second choix. :contentReference[oaicite:4]{index=4}  
- Le README est écrit de façon professionnelle et directement exploitable pour guider développeurs, IA ou contributeurs humains.

Si tu veux, je peux maintenant générer **le prompt d’intégration Codex CLI ou API** prêt à coller dans un fichier `.codexrc` ou dans ton système de génération automatisée.
::contentReference[oaicite:5]{index=5}