#!/bin/bash
set -e

SERVICE_NAME="service_media"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true
sudo systemctl disable "$SERVICE_NAME" 2>/dev/null || true

if [ -f "$SERVICE_FILE" ]; then
    sudo rm "$SERVICE_FILE"
fi

sudo systemctl daemon-reload
sudo systemctl reset-failed

echo "Servico $SERVICE_NAME removido."
