#!/bin/bash
#
# Startet das Dashboard im Kiosk-Modus
#

INSTALL_DIR="/opt/rohstoff-dashboard"
DASHBOARD_URL="file://$INSTALL_DIR/dashboard/index.html"

# Bildschirmschoner deaktivieren
xset s off
xset -dpms 2>/dev/null || true
xset s noblank

# Mauszeiger verstecken nach 0.5 Sekunden Inaktivität
unclutter -idle 0.5 -root &

# Warte kurz auf Display
sleep 2

# Chromium im Kiosk-Modus starten
chromium \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-restore-session-state \
    --no-first-run \
    --start-fullscreen \
    --autoplay-policy=no-user-gesture-required \
    --allow-file-access-from-files \
    "$DASHBOARD_URL"
