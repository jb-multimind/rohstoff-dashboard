#!/bin/bash
# Rohstoff-Dashboard Update Script
# Holt neueste Changes von GitHub und baut Container neu

set -e

echo "=== Rohstoff-Dashboard Update ==="
echo ""

# Git pull
echo "1. Hole neueste Änderungen von GitHub..."
git pull origin main

# Container stoppen
echo "2. Stoppe Container..."
docker-compose down

# Rebuild ohne Cache (wichtig für Dockerfile-Änderungen!)
echo "3. Baue Container neu (ohne Cache)..."
docker-compose build --no-cache

# Container starten
echo "4. Starte Container..."
docker-compose up -d

echo ""
echo "✅ Update abgeschlossen!"
echo "Dashboard: http://$(hostname -I | awk '{print $1}'):8080/dashboard/"
