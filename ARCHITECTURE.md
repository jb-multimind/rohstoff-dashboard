# Rohstoff-Dashboard - Architektur & Entwicklerdokumentation

Diese Dokumentation beschreibt die technische Architektur des Projekts für Entwickler und KI-Assistenten (Claude, GPT, etc.).

## Projektübersicht

Ein Kiosk-Dashboard für Raspberry Pi, das Rohstoffpreise (Weizen, Zucker, Kaffee, Butter) als Liniendiagramme auf einem TV anzeigt.

**Zielplattform:** Raspberry Pi mit HDMI-TV (1920x1080, Landscape)
**Technologien:** Python 3 (Crawler), HTML/CSS/JavaScript (Dashboard), Chart.js

---

## Verzeichnisstruktur

```
rohstoff-dashboard/
├── config.json           # Zentrale Konfiguration (Zeitraum, Cronjob, Display)
├── crawler.py            # Python-Skript zum Abrufen der Preisdaten
├── install.sh            # Bash-Installationsskript für Raspberry Pi
├── start-kiosk.sh        # Startet Chromium im Vollbild-Kiosk-Modus
├── README.md             # Benutzeranleitung
├── ARCHITECTURE.md       # Diese Datei (technische Doku)
├── dashboard/
│   └── index.html        # Single-Page Dashboard (HTML + CSS + JS inline)
└── data/
    ├── weizen.json       # Preisdaten Weizen
    ├── zucker.json       # Preisdaten Zucker
    ├── kaffee.json       # Preisdaten Kaffee
    └── butter.json       # Preisdaten Butter
```

---

## Komponenten

### 1. config.json

Zentrale Konfigurationsdatei für alle anpassbaren Parameter.

```json
{
  "defaultPeriod": "3m",              // Standard-Zeitraum im Dropdown
  "periods": {                         // Verfügbare Zeiträume
    "1w": { "label": "1 Woche", "days": 7 },
    "1m": { "label": "1 Monat", "days": 30 },
    "3m": { "label": "3 Monate", "days": 90 }
  },
  "crawler": {
    "schedule": {
      "hour": 6,                       // Cronjob-Stunde (0-23)
      "minute": 0                      // Cronjob-Minute (0-59)
    }
  },
  "display": {
    "currency": "EUR",
    "currencySymbol": "€",
    "unit": "t",
    "refreshIntervalSeconds": 3600    // Auto-Refresh des Dashboards
  }
}
```

**Verwendung:**
- `crawler.schedule` → wird von `install.sh` gelesen für Cronjob
- `defaultPeriod` → wird vom Dashboard geladen
- `display` → derzeit teilweise implementiert

---

### 2. crawler.py

Python-Skript das Preisdaten von externen Quellen abruft und als JSON speichert.

**Datenquellen:**

| Rohstoff | Quelle | API/Methode |
|----------|--------|-------------|
| Weizen | finanzen.net | Browser-Scraping (Playwright) - Matif Weizen |
| Zucker | Yahoo Finance | HTTP API `query1.finance.yahoo.com` |
| Kaffee | Yahoo Finance | HTTP API `query1.finance.yahoo.com` |
| Butter | CLAL.it | HTML Scraping (Deutsche Markenbutter Kempten) |

**Datenfluss:**
1. EUR/USD Wechselkurs abrufen
2. US-Futures-Preise von Yahoo Finance holen (USD)
3. Preise in EUR umrechnen
4. Einheiten konvertieren (Bushel/lb → Tonne)
5. JSON-Dateien in `data/` speichern

**Ausgabeformat (data/*.json):**

```json
{
  "commodity": "Weizen",
  "unit": "EUR/t",
  "updated": "2024-01-15T06:00:00.000000",
  "stats": {
    "min": 215.50,
    "max": 242.30,
    "avg": 228.75
  },
  "prices": [
    { "date": "2024-01-01", "price": 220.50 },
    { "date": "2024-01-02", "price": 221.30 },
    ...
  ]
}
```

**Wichtige Funktionen:**
- `get_eur_usd_rate()` - Wechselkurs von Yahoo
- `fetch_yahoo_history(symbol)` - Historische Kurse
- `convert_prices(prices, eur_rate, to_ton_from)` - Einheitenkonvertierung
- `fetch_clal_butter()` - Scraping der Butterpreise
- `interpolate_to_daily(weekly)` - Wöchentliche → tägliche Werte

**Fehlerbehandlung:**
- Bei API-Fehlern: Fallback auf existierende Daten
- Bei Butter: Demo-Daten wenn Scraping fehlschlägt

---

### 3. dashboard/index.html

Single-Page-Application mit inline CSS und JavaScript.

**Struktur:**
- `<style>` - Alle CSS-Regeln (Dark Theme, Grid-Layout, Responsive)
- `<body>` - 4 Cards im 2x2 Grid
- `<script>` - Chart.js Initialisierung und Datenladung

**Hauptfunktionen (JavaScript):**

| Funktion | Beschreibung |
|----------|--------------|
| `formatPrice(price, withSymbol)` | Formatiert Preis mit Euro-Symbol |
| `createChart(canvasId, commodity)` | Erstellt Chart.js Liniendiagramm |
| `filterByPeriod(prices, period)` | Filtert Daten nach Zeitraum |
| `calculateStats(prices)` | Berechnet Min/Max/Durchschnitt |
| `updateChart(commodity, data, period)` | Aktualisiert ein Chart |
| `loadData()` | Lädt alle JSON-Dateien aus `data/` |
| `loadConfig()` | Lädt config.json für Default-Periode |

**Farben pro Rohstoff:**
- Weizen: `#f59e0b` (Orange)
- Zucker: `#ec4899` (Pink)
- Kaffee: `#8b5cf6` (Lila)
- Butter: `#06b6d4` (Cyan)

**Responsive Breakpoints:**
- `< 900px`: Single-Column Layout
- `min-aspect-ratio: 16/9`: Optimierungen für TV

---

### 4. install.sh

Bash-Skript für automatische Installation auf Raspberry Pi OS.

**Ablauf:**
1. Pakete installieren (python3, chromium, unclutter)
2. Dateien nach `/opt/rohstoff-dashboard/` kopieren
3. Cronjob einrichten (liest Uhrzeit aus config.json)
4. Autostart Desktop-Entry erstellen
5. Ersten Datenabruf durchführen

**Voraussetzungen:**
- Root-Rechte (`sudo`)
- Raspberry Pi OS mit Desktop
- Benutzer `pi` existiert

---

### 5. start-kiosk.sh

Startet Chromium im Kiosk-Modus.

**Features:**
- Bildschirmschoner deaktiviert (`xset`)
- Mauszeiger versteckt (`unclutter`)
- Chromium ohne UI-Elemente (`--kiosk --noerrdialogs`)

---

## Erweiterungspunkte

### Neue Rohstoffe hinzufügen

1. **crawler.py:** Neuen Eintrag in `COMMODITIES` Dict
2. **dashboard/index.html:** 
   - Neue Card im HTML
   - Farbe in `COLORS` Dict
   - Canvas-ID in Chart-Initialisierung

### Neue Datenquelle

1. Neue Fetch-Funktion in crawler.py schreiben
2. Im `main()` entsprechend aufrufen
3. Gleiches JSON-Format verwenden

### Konfiguration erweitern

1. Parameter in config.json hinzufügen
2. In crawler.py oder dashboard/index.html auslesen
3. Diese Doku aktualisieren

---

## Bekannte Limitierungen

1. **Yahoo Finance Rate-Limiting:** Bei zu vielen Requests → 429 Error. Lösung: Längere Pausen zwischen Requests oder Caching.

2. **CLAL.it Scraping:** HTML-Struktur kann sich ändern. Bei Fehlern Regex in `fetch_clal_butter()` anpassen.

3. **Offline-Betrieb:** Dashboard zeigt letzte gecachte Daten, aber keine Live-Updates.

4. **Keine Authentifizierung:** Dashboard ist lokal zugänglich ohne Login.

---

## Debugging

**Crawler testen:**
```bash
cd /opt/rohstoff-dashboard
python3 crawler.py
```

**Logs prüfen:**
```bash
cat /var/log/rohstoff-crawler.log
```

**Dashboard lokal testen:**
```bash
cd /opt/rohstoff-dashboard
python3 -m http.server 8080
# Browser: http://localhost:8080/dashboard/
```

---

## Kontakt / Changelog

Erstellt für: Jan-Bernd
Letzte Änderung: 2026-02-05
- Euro-Symbol vor Preisen
- Config für Cronjob-Uhrzeit
- Dokumentation für LLM-Kompatibilität
