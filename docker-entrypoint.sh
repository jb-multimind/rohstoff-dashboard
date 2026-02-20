#!/bin/bash
set -e

# Start cron in background
cron

# Start simple HTTP server
echo "Starting web server on port 8080..."
exec python3 /app/server.py
