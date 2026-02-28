# Architecture Prévisionnelle

## Top-Level Modules

/frontend
/backend
/db
/integration
/tests
/docs

---

## Frontend

Technologie :
React + Tailwind

Composants principaux :
- SidebarSources
- EditorWindow
- Toolbar
- AIHelperPanel
- UploadModal
- URLDownloadModal

Flux :
Utilisateur → Upload → Backend → Extraction → Affichage source → Interaction éditeur

---

## Backend

Framework :
FastAPI

Endpoints :

POST /upload
POST /download-from-url
POST /extract
POST /video-to-text
POST /ai-assist

Responsabilités :
- Parsing fichiers
- Extraction texte/images
- Conversion vidéo en texte
- Proxy API IA

---

## DB

MVP :
SQLite local

Stocke :
- Métadonnées fichier
- Historique extraction
- Projets simples

---

## Integration

- pdfplumber
- python-docx
- openpyxl
- pytesseract (optionnel)
- whisper pour vidéo
- OpenAI API (clé utilisateur)

---

## Prévisions Évolutives

- Mode cloud
- Collaboration
- Plugin navigateur
- Marketplace extensions

---

## Flux de données

Upload → Parse → Extract → Store meta → Return JSON → Render UI
Voici exactement comment implémenter les contrats JSON dans le code pour que :

Le backend valide automatiquement chaque requête

L’API expose des schémas JSON réutilisables

Codex/LLMs puissent raisonner à partir d’un schéma strict et stable

La documentation OpenAPI/Swagger soit générée automatiquement

🧱 1. Définir les modèles Pydantic (contrats JSON)

Dans FastAPI, tu déclare un modèle Pydantic pour chaque schéma JSON attendu ou retourné. Pydantic va :

générer le schema JSON

valider automatiquement l’entrée

générer de la doc Swagger/OpenAPI

servir de référence pour Codex ou générateurs de code front

👉 FastAPI + Pydantic fait tout ça automatiquement.

Exemple de modèle

Imaginons ton contrat type :

from pydantic import BaseModel
from typing import Optional, Any, Dict

class BaseResponse(BaseModel):
    type: str
    version: int
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None

Celui-ci est un contrat global pour toutes les réponses.

Ensuite, pour /upload, par exemple :

class UploadData(BaseModel):
    file_id: str
    file_name: str
    file_type: str
    stored: bool

class UploadResponse(BaseResponse):
    data: UploadData

Ce schéma décrit précisément le JSON que l’API doit retourner.

🚀 2. Utiliser ces modèles dans FastAPI

Tu les utilises directement dans les endpoints :

from fastapi import FastAPI
from models import UploadResponse

app = FastAPI()

@app.post("/upload", response_model=UploadResponse)
async def upload_file():
    return UploadResponse(
        type="upload_response",
        version=1,
        success=True,
        data={
            "file_id": "uuid123",
            "file_name": "doc.pdf",
            "file_type": "pdf",
            "stored": True
        },
        error=None
    )

⚡ Résultat :

FastAPI valide la structure de retour

FastAPI expose le schéma JSON dans la doc /docs

Codex peut lire ce schéma automatiquement pour générer ou comprendre du code

C’est le cœur de l’implémentation de contrats JSON.

📈 3. Validation automatique des requêtes

Quand tu attends un JSON en entrée, tu fais pareil :

class ExtractRequest(BaseModel):
    file_id: str
    mode: str

@app.post("/extract", response_model=ExtractResponse)
async def extract(request: ExtractRequest):
    # FastAPI aura déjà validé `request.file_id` et `request.mode`
    ...

FastAPI va :

Lire le body JSON

Transformer en objet ExtractRequest

Valider les types

Répondre avec ExtractResponse

Si le JSON ne correspond pas, tu auras une erreur claire (422).

📜 4. Génération automatique de la documentation

En déclarant les modèles, tu obtiens :

👉 Une API auto-documentée à /docs
👉 Une spec OpenAPI standard (exploitable par Builder, Codex…)
👉 Un schéma JSON clair que Codex peut lire sans ambiguïté

Cette documentation est un schéma JSON vivant de ton API !

📌 Ce que ça donne concrètement
Exemple global :

models.py

from pydantic import BaseModel
from typing import Dict, Any, Optional

class BaseResponse(BaseModel):
    type: str
    version: int
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None

class UploadData(BaseModel):
    file_id: str
    file_name: str
    file_type: str
    stored: bool

class UploadResponse(BaseResponse):
    data: UploadData

main.py

from fastapi import FastAPI
from models import UploadResponse

app = FastAPI()

@app.post("/upload", response_model=UploadResponse)
async def upload_file():
    return UploadResponse(
        type="upload_response",
        version=1,
        success=True,
        data={
            "file_id": "uuid123",
            "file_name": "doc.pdf",
            "file_type": "pdf",
            "stored": True
        }
    )



🎁 Bonus : conversions JSON → modèles front

Avec le schéma OpenAPI généré, tu peux :

Générer automatiquement les types TypeScript Phaser/React

Construire les formulaires UI automatiquement dans Builder.io

Générer des tests e2e

## Implémentation MVP (état courant)

- `backend/models.py` : modèles Pydantic de requête/réponse.
- `backend/main.py` : service FastAPI et endpoints contractuels.
- `tests/test_api.py` : tests de contrat (`BaseResponse`) et validation d’entrée.

- Stockage temporaire en mémoire (`SOURCES`) pour relier upload/download à extraction.
- Téléchargement URL MVP avec prévisualisation de contenu texte (bornée) et erreur contractuelle.

- Endpoints additionnels MVP de support UI: `GET /sources`, `GET /source/{file_id}`.

- Backend implémenté en modules: `api/v1`, `services`, `repositories`, `db` (SQLAlchemy SQLite).

- Versionnement API actif via préfixe `/api/v1`.

- Gestion des erreurs centralisée dans `main.py` (handlers globaux) pour homogénéité du contrat API.

- Middlewares backend: correlation ID (`x-request-id`) + limite de concurrence (retour `over_capacity`).

- Couche frontend d'intégration: `frontend/src/api`, `frontend/src/services`, `frontend/src/state` (séparation API/état/UI).


- Product Domain layer ajoutée: `projects`, `documents`, `batch_runs`, `batch_items` avec orchestration service dédiée.

- Opérations: CI/CD avec jobs qualité (tests + build Docker), staging branch deploy, production tag/main deploy.

- Sécurité plateforme: middleware rate limit + headers sécurité + dépendances auth JWT/RBAC sur endpoints Product Layer.
- Observabilité: endpoint `/metrics` Prometheus et métriques de latence/erreurs/extraction/batch.
