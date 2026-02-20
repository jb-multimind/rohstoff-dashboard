# Rohstoff-Dashboard

Zeigt aktuelle Preise für Weizen, Zucker, Kaffee und Butter auf einem Raspberry Pi im Kiosk-Modus.

## Features

- 4 Rohstoffe im 2x2 Grid-Layout (optimiert für 1920x1080 TV)
- Alle Preise in EUR/Tonne
- 3-Monats-Charts mit Min/Max/Durchschnitt
- Zeitraum wählbar: 1 Woche / 1 Monat / 3 Monate
- Tägliche automatische Aktualisierung (6:00 Uhr)
- Quellenangabe pro Rohstoff

## Datenquellen

| Rohstoff | Quelle | Anmerkung |
|----------|--------|-----------|
| Weizen | finanzen.net | Matif Weizen (Euronext Paris), Browser-Scraping |
| Zucker | Yahoo Finance | US-Futures, umgerechnet in EUR/t |
| Kaffee | Yahoo Finance | US-Futures, umgerechnet in EUR/t |
| Butter | CLAL.it Kempten | Deutsche Markenbutter, EUR/t |

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
