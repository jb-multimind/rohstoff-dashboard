# Rohstoff-Dashboard (Headless)

Minimal-Installation für Raspberry Pi **ohne Desktop-Umgebung**.

Installiert nur X11 + Chromium, kein LXDE/GNOME/etc.

## Unterschiede zur Standard-Version

| Feature | Standard | Headless |
|---------|----------|----------|
| Desktop-Umgebung | LXDE/Raspbian Desktop | Keine |
| Speicherverbrauch | ~400 MB RAM | ~150 MB RAM |
| Installation | `install.sh` | `install-headless.sh` |
| Auto-Start | Desktop Autostart | Auto-Login + startx |
| Pakete | Desktop-Abhängigkeiten | Nur X11 + Chromium |

## Installation

```bash
# ZIP entpacken
tar -xzf rohstoff-dashboard-headless.tar.gz
cd rohstoff-dashboard

# Installation als root
sudo ./install-headless.sh

# Neu starten
sudo reboot
```

## Was wird installiert?

- **X11** (xserver-xorg, xinit) - Minimaler Display-Server
- **Chromium** - Browser für das Dashboard
- **unclutter** - Versteckt Mauszeiger
- **Python3** - Für Crawler
- **Auto-Login** - User `pi` auf tty1
- **startx** - Startet automatisch beim Login

## Funktionsweise

1. Pi bootet → Auto-Login als `pi` auf tty1
2. `.bash_profile` startet `startx`
3. `.xinitrc` startet Chromium im Kiosk-Modus
4. Dashboard wird angezeigt (ohne Window Manager)

## Voraussetzungen

- **Raspberry Pi OS Lite** (empfohlen) oder Standard
- Frische Installation bevorzugt
- HDMI-Verbindung zum TV
- Internetverbindung für Datenabruf

## Manueller Start (falls nötig)

Normalerweise nicht nötig da Auto-Start.

```bash
# Als User pi:
startx

# Oder via SSH:
sudo -u pi startx
```

## Beenden

```bash
# Via SSH:
sudo systemctl restart getty@tty1

# Oder:
sudo reboot
```

## Speicherverbrauch

Typisch nach Start:

- X11: ~30 MB
- Chromium: ~120 MB
- System: ~50 MB
- **Gesamt: ~200 MB** (vs. ~500 MB mit Desktop)

## Problembehandlung

**Bildschirm bleibt schwarz:**
```bash
# Logs prüfen:
journalctl -u getty@tty1 -b
cat ~/.xsession-errors
```

**Dashboard lädt nicht:**
```bash
# Crawler manuell testen:
cd /opt/rohstoff-dashboard
python3 crawler.py
```

**X11 startet nicht:**
```bash
# X11-Pakete neu installieren:
sudo apt install --reinstall xserver-xorg xinit
```

## Konfiguration

Gleiche `config.json` wie Standard-Version:

- `defaultPeriod` - Anzeigezeitraum
- `crawler.schedule` - Cronjob-Uhrzeit
- `display` - Währung/Einheiten

## Zurück zu Standard-Version

Falls du doch einen Desktop brauchst:

```bash
sudo apt install raspberrypi-ui-mods
sudo raspi-config
# System Options → Boot/Auto-Login → Desktop Auto-Login
```

Dann `install.sh` (Standard-Version) verwenden.

---

**Empfehlung:** Headless für dedizierte Display-Systeme. Standard-Version wenn du den Pi auch für andere Sachen nutzt.
