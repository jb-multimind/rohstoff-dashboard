#!/bin/bash
#
# Rohstoff-Dashboard Installation für Raspberry Pi (mit Desktop)
# Inkl. Playwright für Browser-Scraping
# Ausführen: sudo ./install.sh
#

set -e

echo "========================================"
echo "  Rohstoff-Dashboard Installation"
echo "========================================"
echo ""

# Prüfe ob Root
if [ "$EUID" -ne 0 ]; then 
    echo "Bitte als root ausführen: sudo ./install.sh"
    exit 1
fi

# Pfade
INSTALL_DIR="/opt/rohstoff-dashboard"
USER="${SUDO_USER:-pi}"

echo "[1/6] System-Pakete installieren..."
apt-get update
apt-get install -y python3 python3-pip chromium unclutter

echo "[2/6] Python-Pakete (Playwright) installieren..."
pip3 install playwright --break-system-packages 2>/dev/null || pip3 install playwright

echo "[3/6] Playwright Browser installieren..."
sudo -u "$USER" python3 -m playwright install chromium

echo "[4/6] Dateien kopieren..."
mkdir -p "$INSTALL_DIR"
cp -r dashboard data crawler.py start-kiosk.sh config.json README.md ARCHITECTURE.md "$INSTALL_DIR/" 2>/dev/null || \
cp -r dashboard data crawler.py start-kiosk.sh config.json "$INSTALL_DIR/"

# Musswessels-Version als Standard setzen
if [ -f "$INSTALL_DIR/dashboard/index-musswessels.html" ]; then
    cp "$INSTALL_DIR/dashboard/index-musswessels.html" "$INSTALL_DIR/dashboard/index.html"
    echo "  Musswessels-Branding aktiviert"
fi

# Dateirechte setzen
chown -R "$USER:$USER" "$INSTALL_DIR"
find "$INSTALL_DIR" -type d -exec chmod 755 {} \;
find "$INSTALL_DIR" -type f -exec chmod 644 {} \;
chmod 755 "$INSTALL_DIR/crawler.py"
chmod 755 "$INSTALL_DIR/start-kiosk.sh"

echo "[5/6] Cronjob einrichten..."
CRON_TIME=$(python3 -c "
import json
try:
    with open('$INSTALL_DIR/config.json') as f:
        cfg = json.load(f)
    h = cfg.get('crawler', {}).get('schedule', {}).get('hour', 6)
    m = cfg.get('crawler', {}).get('schedule', {}).get('minute', 0)
    print(f'{m} {h}')
except:
    print('0 6')
")
CRON_CMD="$CRON_TIME * * * cd $INSTALL_DIR && python3 crawler.py >> /var/log/rohstoff-crawler.log 2>&1"
(crontab -u "$USER" -l 2>/dev/null | grep -v "rohstoff"; echo "$CRON_CMD") | crontab -u "$USER" -
echo "  Crawler läuft täglich um $(echo $CRON_TIME | awk '{print $2}'):$(printf '%02d' $(echo $CRON_TIME | awk '{print $1}')) Uhr"

echo "[6/6] Autostart einrichten..."
AUTOSTART_DIR="/home/$USER/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

cat > "$AUTOSTART_DIR/rohstoff-dashboard.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Rohstoff Dashboard
Exec=$INSTALL_DIR/start-kiosk.sh
X-GNOME-Autostart-enabled=true
EOF

chown -R "$USER:$USER" "$AUTOSTART_DIR"

# Erster Datenabruf
echo ""
echo "Erster Datenabruf (kann 30 Sekunden dauern)..."
cd "$INSTALL_DIR"
sudo -u "$USER" python3 crawler.py || echo "  Hinweis: Datenabruf fehlgeschlagen - wird beim nächsten Cronjob wiederholt"

echo ""
echo "========================================"
echo "  ✓ Installation abgeschlossen!"
echo "========================================"
echo ""
echo "DASHBOARD STARTEN:"
echo ""
echo "  Als User '$USER':"
echo "    $INSTALL_DIR/start-kiosk.sh"
echo ""
echo "  Oder direkt vom Terminal:"
echo "    cd $INSTALL_DIR && ./start-kiosk.sh"
echo ""
echo "AUTOSTART:"
echo "  Das Dashboard startet automatisch nach"
echo "  dem nächsten Neustart:"
echo "    sudo reboot"
echo ""
echo "DATEN-UPDATE:"
echo "  Täglich um $(echo $CRON_TIME | awk '{print $2}'):$(printf '%02d' $(echo $CRON_TIME | awk '{print $1}')) Uhr via Cronjob"
echo "  Manuell: cd $INSTALL_DIR && python3 crawler.py"
echo ""
echo "LOG-DATEI:"
echo "  /var/log/rohstoff-crawler.log"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
