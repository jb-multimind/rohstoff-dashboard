#!/bin/bash
# Schnelles Update (ohne kompletten Rebuild)
# Nutze das für normale Code-Änderungen (nicht Dockerfile)

set -e

echo "=== Quick Update (mit Cache) ==="
echo ""

git pull origin main
docker-compose down
docker-compose up -d --build

echo ""
echo "✅ Fertig!"
