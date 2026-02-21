#!/bin/bash
set -e

# Initial data crawl on startup
echo "Running initial data crawl..."
python3 /app/crawler.py || echo "Initial crawl failed, continuing..."

# Start cron in background
cron

# Start simple HTTP server
echo "Starting web server on port 8080..."
exec python3 /app/server.py
