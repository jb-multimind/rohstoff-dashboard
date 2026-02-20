#!/bin/bash
#
# Startet das Dashboard im Kiosk-Modus (Headless-Variante)
# Wird automatisch von .xinitrc aufgerufen
#

INSTALL_DIR="/opt/rohstoff-dashboard"
DASHBOARD_URL="file://$INSTALL_DIR/dashboard/index.html"

# Chromium im Kiosk-Modus starten
# --no-sandbox nötig für X11 ohne Window Manager
exec chromium \
    --kiosk \
    --no-sandbox \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-restore-session-state \
    --no-first-run \
    --start-fullscreen \
    --autoplay-policy=no-user-gesture-required \
    "$DASHBOARD_URL"
