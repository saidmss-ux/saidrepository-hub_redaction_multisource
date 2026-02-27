#!/usr/bin/env bash
set -e

echo "=== DOCUHUB CODEX ENV BOOTSTRAP START ==="

# -----------------------------
# 1. Vérification outils système
# -----------------------------
command -v python3 >/dev/null 2>&1 || { echo "Python3 requis"; exit 1; }
command -v pip >/dev/null 2>&1 || { echo "pip requis"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node requis"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "npm requis"; exit 1; }

# -----------------------------
# 2. Backend Setup
# -----------------------------
echo ">>> Setup Backend"

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip wheel setuptools

# Téléchargement offline des wheels
mkdir -p .offline_packages
pip download -r requirements.txt -d .offline_packages

# Installation depuis cache local
pip install --no-index --find-links=.offline_packages -r requirements.txt

# Vérification
pip check

# -----------------------------
# 3. Frontend Setup
# -----------------------------
echo ">>> Setup Frontend"

cd frontend

# Installation complète + lock
npm install

# Préparer cache offline npm
npm config set prefer-offline true
npm config set offline true

cd ..

# -----------------------------
# 4. Tests Init
# -----------------------------
echo ">>> Running Sanity Tests"

source .venv/bin/activate
pytest || echo "Tests backend non bloquants"

cd frontend
npm run build || echo "Build frontend non bloquant"
cd ..

# -----------------------------
# 5. Verrouillage environnement
# -----------------------------
echo ">>> Locking environment"

pip freeze > requirements.lock.txt
npm list --depth=0 > frontend.lock.txt

echo "ENVIRONMENT_READY=true" > .env.codex

echo "=== BOOTSTRAP COMPLETE ==="