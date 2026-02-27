#!/usr/bin/env bash
set -e

echo "=== ENV CONFIGURATION START ==="

# Backend: Python venv + installation offline
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip wheel setuptools

# Téléchargement des packages dans cache local
pip download -r requirements.txt -d .offline_packages

# Installation offline depuis le cache
pip install --no-index --find-links=.offline_packages -r requirements.txt

# Frontend: installer dépendances une fois
cd frontend
npm install

echo "=== ENV CONFIGURATION COMPLETE ==="