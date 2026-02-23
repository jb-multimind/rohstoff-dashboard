# Rohstoff-Dashboard - Docker Deployment

Web-Service für 8 Rohstoff-Preise mit automatischem Crawler.

## 🎯 Features

- **8 Rohstoffe**: Weizen, Roggen, Zucker, Kaffee, Kakao, Butter, Käse, Milch
- **Auto-Crawler**: Täglich um 6:00 UTC
- **Live-Dashboard**: Responsive Web-UI mit Charts
- **Docker**: Production-ready Container
- **Production-Ready**: ~650 MB Image (inkl. Playwright/Chromium für echtes Weizen-Scraping)

## 🚀 Schnellstart

### Voraussetzungen
- Docker & Docker Compose installiert
- Port 8080 frei

### Installation

```bash
# Repository klonen
git clone https://github.com/jb-multimind/rohstoff-dashboard
cd rohstoff-dashboard

# Container bauen und starten
docker-compose up -d

# Logs ansehen
docker-compose logs -f
```

Dashboard läuft jetzt auf: **http://localhost:8080/dashboard/**

## 🤖 Google Gemini Vision (Optional)

Das Dashboard kann **Google Gemini Vision** für robustere Preis-Erkennung nutzen:

### Vorteile
- ✅ **Robuster** gegen HTML-Änderungen
- ✅ **1500 Anfragen/Tag kostenlos**
- ✅ **Fallback auf alte Methode** bei Fehler

### Setup
1. **API Key holen**: https://aistudio.google.com/app/apikey
2. **Im Dashboard**: Klick auf ⚙️ (Settings)
3. **API Key eingeben** und speichern
4. **Crawler neu starten**: `docker-compose restart`

### Funktionsweise
1. Crawler macht Screenshot von finanzen.net
2. Screenshot wird an Gemini geschickt
3. Gemini extrahiert Preis aus Bild
4. Bei Fehler: Fallback auf alte Selector-Methode

### Test
```bash
# Crawler manuell ausführen (im Container)
docker-compose exec rohstoff-dashboard python3 /app/crawler.py

# Gemini-Logs prüfen
docker-compose logs | grep Gemini
```

## 🛠️ Konfiguration

### Port ändern

In `docker-compose.yml`:
```yaml
ports:
  - "3000:8080"  # Extern Port 3000, intern 8080
```

### Crawler-Zeitplan ändern

In `Dockerfile`, Zeile mit `cron.d`:
```dockerfile
RUN echo "0 6 * * * ..." # 6:00 UTC
RUN echo "0 */4 * * * ..." # Alle 4 Stunden
```

### Crawler manuell starten

```bash
docker-compose exec rohstoff-dashboard python3 /app/crawler.py
```

## 📊 Datenquellen

| Rohstoff | Quelle | Einheit |
|----------|--------|---------|
| Weizen | finanzen.net (Matif) | EUR/t |
| Roggen | Weizen-Proxy | EUR/t |
| Zucker | Yahoo Finance (NYBOT) | EUR/t |
| Kaffee | Yahoo Finance (ICE) | EUR/t |
| Kakao | Yahoo Finance (ICE) | EUR/t |
| Butter | CLAL.it (Kempten) | EUR/t |
| Käse | CLAL.it (Cheddar) | EUR/t |
| Milch | CLAL.it (EU Farm-Gate) | EUR/t |

## 🔧 Hostinger VPS Deployment

### 1. Docker installieren (Ubuntu/Debian)

```bash
# Docker Engine
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

### 2. Repository klonen

```bash
cd /opt
git clone https://github.com/jb-multimind/rohstoff-dashboard
cd rohstoff-dashboard
```

### 3. Container starten

```bash
# Build & Start
docker-compose up -d

# Status prüfen
docker-compose ps
docker-compose logs -f
```

### 4. Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name rohstoffe.example.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 5. Auto-Start bei Reboot

```bash
# Systemd Service
sudo nano /etc/systemd/system/rohstoff-dashboard.service
```

```ini
[Unit]
Description=Rohstoff Dashboard
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/rohstoff-dashboard
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable rohstoff-dashboard
sudo systemctl start rohstoff-dashboard
```

## 🔄 Updates

### Via SSH (empfohlen)

**Option 1: Schnelles Update** (normale Code-Änderungen)
```bash
cd /opt/rohstoff-dashboard
./quick-update.sh
```

**Option 2: Vollständiges Update** (Dockerfile-Änderungen, neue Dependencies)
```bash
cd /opt/rohstoff-dashboard
./update.sh
```

**Option 3: Manuell**
```bash
cd /opt/rohstoff-dashboard
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**Wann welches Update?**
- `quick-update.sh` → Dashboard, Crawler, Config-Änderungen (1-2 Min)
- `update.sh` → Dockerfile, neue Dependencies, Playwright (5-10 Min)

## 📱 Pi Kiosk-Modus

Auf dem Raspberry Pi zeigt Chromium die URL an:

```bash
# In start-kiosk.sh auf dem Pi
chromium-browser --kiosk --noerrdialogs \
  --disable-infobars \
  http://ihre-domain.de/dashboard/
```

## 🐛 Troubleshooting

### Container startet nicht

```bash
docker-compose logs rohstoff-dashboard
docker ps -a
```

### Crawler läuft nicht

```bash
# Logs prüfen
docker-compose exec rohstoff-dashboard cat /var/log/cron.log

# Manuell testen
docker-compose exec rohstoff-dashboard python3 /app/crawler.py
```

### Keine Daten sichtbar

```bash
# data/ Verzeichnis prüfen
docker-compose exec rohstoff-dashboard ls -la /app/data/

# Crawler manuell starten
docker-compose exec rohstoff-dashboard python3 /app/crawler.py
```

### Port bereits belegt

```bash
# In docker-compose.yml Port ändern
ports:
  - "3000:8080"
```

## 📦 Image-Größe

**Standard (mit Playwright):**
- Größe: ~650 MB
- Weizen-Preise: Live von finanzen.net (Browser-Scraping)
- Alle anderen Rohstoffe: API-basiert

**Warum Playwright?**
- finanzen.net hat keine öffentliche API
- Playwright rendert die Website und extrahiert den aktuellen Preis
- Zuverlässiger als einfaches HTML-Parsing (Website-Updates brechen es nicht)

## 🔒 Sicherheit

- **Keine Secrets**: Alle Datenquellen sind öffentlich
- **Read-Only**: Dashboard ist statisch (kein User-Input)
- **Firewall**: Nur Port 8080 exponieren
- **Updates**: Regelmäßig `git pull` + rebuild

## 📄 Lizenz

MIT License - Free to use and modify.

## 🆘 Support

Bei Fragen oder Problemen:
1. Logs prüfen: `docker-compose logs -f`
2. GitHub Issues: https://github.com/jb-multimind/rohstoff-dashboard/issues
