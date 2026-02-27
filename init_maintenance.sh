#!/usr/bin/env bash
set -e

echo "=== ENV MAINTENANCE CHECK START ==="

# Vérifier existence de l'environnement Python
if [ ! -d ".venv" ]; then
    echo "ERROR: Python environment missing"
    exit 1
fi

source .venv/bin/activate
pip check || echo "Warning: Backend dependencies may be broken"

# Vérifier frontend
if [ ! -d "frontend/node_modules" ]; then
    echo "ERROR: Frontend dependencies missing"
    exit 1
fi

cd frontend
npm ls --depth=0 || echo "Warning: Frontend dependencies issues"
cd ..

echo "=== ENV MAINTENANCE CHECK COMPLETE ==="