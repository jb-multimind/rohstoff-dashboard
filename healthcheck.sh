#!/bin/bash
# Healthcheck Script - prüft ob Server antwortet

URL="http://localhost:8080/dashboard/"
TIMEOUT=5

# Teste HTTP Request
if curl -f -s --max-time $TIMEOUT "$URL" > /dev/null; then
    echo "✓ Server OK"
    exit 0
else
    echo "✗ Server nicht erreichbar"
    exit 1
fi
