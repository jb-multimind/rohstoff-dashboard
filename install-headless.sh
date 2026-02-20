#!/bin/bash
#
# Rohstoff-Dashboard Installation für Raspberry Pi (Headless)
# Installiert nur X11 + Chromium ohne Desktop-Umgebung
# Ausführen: sudo ./install-headless.sh
#

set -e

echo "========================================"
echo "  Rohstoff-Dashboard (Headless)"
echo "========================================"
echo ""

# Prüfe ob Root
if [ "$EUID" -ne 0 ]; then 
    echo "Bitte als root ausführen: sudo ./install-headless.sh"
    exit 1
fi

# Pfade
INSTALL_DIR="/opt/rohstoff-dashboard"
USER="pi"

echo "[1/6] Minimal X11 + Chromium installieren..."
apt-get update
apt-get install -y \
    xserver-xorg \
    xinit \
    x11-xserver-utils \
    chromium \
    unclutter \
    python3

echo "[2/6] Dateien kopieren..."
mkdir -p "$INSTALL_DIR"
cp -r dashboard data crawler.py start-kiosk-headless.sh config.json README.md "$INSTALL_DIR/" 2>/dev/null || \
cp -r dashboard data crawler.py start-kiosk-headless.sh config.json "$INSTALL_DIR/"
chown -R "$USER:$USER" "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/crawler.py"
chmod +x "$INSTALL_DIR/start-kiosk-headless.sh"

echo "[3/6] Cronjob einrichten..."
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

echo "[4/6] Auto-Login konfigurieren..."
# Systemd Auto-Login für getty@tty1
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat > /etc/systemd/system/getty@tty1.service.d/autologin.conf << EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $USER --noclear %I \$TERM
EOF

echo "[5/6] Auto-Start X11 einrichten..."
# .bash_profile startet X beim Login auf tty1
cat > /home/$USER/.bash_profile << 'EOF'
# Starte X automatisch auf tty1
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    exec startx -- -nocursor
fi
EOF

# .xinitrc startet das Dashboard
cat > /home/$USER/.xinitrc << EOF
#!/bin/sh
# Bildschirmschoner aus
xset s off
xset -dpms
xset s noblank

# Mauszeiger verstecken
unclutter -idle 0.5 -root &

# Warte auf Display
sleep 2

# Dashboard im Kiosk-Modus
exec $INSTALL_DIR/start-kiosk-headless.sh
EOF

chmod +x /home/$USER/.xinitrc
chown $USER:$USER /home/$USER/.bash_profile /home/$USER/.xinitrc

echo "[6/6] Erster Datenabruf..."
cd "$INSTALL_DIR"
sudo -u "$USER" python3 crawler.py || echo "  Hinweis: Datenabruf fehlgeschlagen - wird beim nächsten Cronjob wiederholt"

echo ""
echo "========================================"
echo "  Installation abgeschlossen!"
echo "========================================"
echo ""
echo "Headless-Setup:"
echo "  - Kein Desktop installiert"
echo "  - Auto-Login + X11 beim Boot"
echo "  - Dashboard startet automatisch"
echo ""
echo "Jetzt neu starten:"
echo "  sudo reboot"
echo ""
echo "Manueller Start (nach Reboot unnötig):"
echo "  sudo -u $USER startx"
echo ""
