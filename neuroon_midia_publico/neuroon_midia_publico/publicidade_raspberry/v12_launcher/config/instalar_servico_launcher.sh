#!/bin/bash
set -e

SERVICE_NAME="service_media"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
LAUNCHER_DIR="$HOME/v12_launcher"
LAUNCHER_PATH="$LAUNCHER_DIR/launcher.py"
USER_NAME="$(whoami)"

if [ ! -f "$LAUNCHER_PATH" ]; then
    echo "Launcher nao encontrado: $LAUNCHER_PATH"
    echo "Copie a pasta v12_launcher para $HOME antes de instalar o servico."
    exit 1
fi

chmod +x "$LAUNCHER_PATH"
mkdir -p "$LAUNCHER_DIR/logs" "$LAUNCHER_DIR/state" "$LAUNCHER_DIR/runtime"

SERVICE_CONTENT="[Unit]
Description=Neuroon publicidade launcher
After=graphical.target
Wants=graphical.target

[Service]
ExecStart=/usr/bin/python3 $LAUNCHER_PATH
WorkingDirectory=$LAUNCHER_DIR
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/$USER_NAME/.Xauthority
StandardOutput=inherit
StandardError=inherit
Restart=on-failure
RestartSec=5
User=$USER_NAME

[Install]
WantedBy=graphical.target"

echo "$SERVICE_CONTENT" | sudo tee "$SERVICE_FILE" > /dev/null

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

echo "Servico $SERVICE_NAME instalado e iniciado."
