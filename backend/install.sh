#!/bin/bash

echo "📦 Création environnement virtuel..."
python3 -m venv venv

echo "🔁 Activation environnement..."
source venv/bin/activate

echo "⬆️ Upgrade pip..."
pip install --upgrade pip

echo "📚 Installation dépendances..."
pip install fastapi
pip install uvicorn[standard]
pip install sqlalchemy
pip install pydantic
pip install python-multipart
pip install aiohttp
pip install pytest
pip install pytest-asyncio
pip install httpx

echo "💾 Gel des dépendances..."
pip freeze > requirements.txt

echo "✅ Backend prêt."