# Rohstoff-Dashboard

Zeigt aktuelle Preise für 8 Rohstoffe auf einem Raspberry Pi im Kiosk-Modus oder als Web-Service.

## Features

- **8 Rohstoffe**: Weizen, Roggen, Zucker, Kaffee, Kakao, Butter, Käse, Milch
- 4x2 Grid-Layout (optimiert für 1920x1080 TV)
- Alle Preise in EUR/Tonne
- 3-Monats-Charts mit Min/Max/Durchschnitt
- Zeitraum wählbar: 1 Woche / 1 Monat / 3 Monate
- Tägliche automatische Aktualisierung (6:00 Uhr)
- Quellenangabe pro Rohstoff
- **Docker-ready** für Cloud/VPS Deployment

## Datenquellen

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

## 🐳 Docker Deployment (Cloud/VPS)

Für Web-Service Deployment siehe **[README-DOCKER.md](README-DOCKER.md)**

Schnellstart:
```bash
git clone https://github.com/jb-multimind/rohstoff-dashboard
cd rohstoff-dashboard
docker-compose up -d
```

Dashboard läuft auf: `http://localhost:8080/dashboard/`

---

## Installation auf Raspberry Pi

```bash
# ZIP entpacken
unzip rohstoff-dashboard.zip
cd rohstoff-dashboard

# Installation starten (als root)
sudo ./install.sh
```

Die Installation:
1. Installiert benötigte Pakete (Python3, Chromium, unclutter)
2. Kopiert Dateien nach `/opt/rohstoff-dashboard/`
3. Richtet täglichen Cronjob ein (6:00 Uhr)
4. Konfiguriert Autostart beim Booten

## Manuell starten

```bash
# Daten aktualisieren
cd /opt/rohstoff-dashboard
python3 crawler.py

# Dashboard starten
./start-kiosk.sh
```

## Dateien

```
rohstoff-dashboard/
├── dashboard/
│   └── index.html      # Das Dashboard
├── data/               # JSON-Preisdaten
├── crawler.py          # Holt aktuelle Preise
├── start-kiosk.sh      # Startet Chromium im Kiosk-Modus
├── install.sh          # Installationsscript
└── README.md
```

## Anforderungen

- Raspberry Pi (3/4/5) mit Raspberry Pi OS
- HDMI-Verbindung zum TV
- Internetverbindung für Datenabruf
