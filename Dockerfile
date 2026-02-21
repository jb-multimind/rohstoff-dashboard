FROM python:3.11-slim

WORKDIR /app

# System dependencies (inkl. Playwright/Chromium Dependencies)
RUN apt-get update && apt-get install -y \
    cron \
    curl \
    wget \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright + Chromium
RUN playwright install-deps chromium
RUN playwright install chromium

# Copy application
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Setup cron job (täglich um 6:00 UTC)
RUN echo "0 6 * * * cd /app && /usr/local/bin/python3 crawler.py >> /var/log/cron.log 2>&1" > /etc/cron.d/crawler-cron
RUN chmod 0644 /etc/cron.d/crawler-cron
RUN crontab /etc/cron.d/crawler-cron
RUN touch /var/log/cron.log

# Initial crawl beim Start
RUN python3 crawler.py || true

# Expose port
EXPOSE 8080

# Start script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

CMD ["docker-entrypoint.sh"]
