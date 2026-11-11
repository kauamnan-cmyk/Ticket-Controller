#!/bin/bash

SERVICE_NAME="service_media"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SECOND_SH="$HOME/start_media.sh"

echo "⛔ Parando serviço..."
sudo systemctl stop "$SERVICE_NAME"

echo "🧼 Desabilitando serviço do boot..."
sudo systemctl disable "$SERVICE_NAME"

if [ -f "$SERVICE_FILE" ]; then
    echo "🗑️ Removendo arquivo do serviço: $SERVICE_FILE"
    sudo rm "$SERVICE_FILE"
else
    echo "⚠️ Arquivo de serviço não encontrado: $SERVICE_FILE"
fi

echo "🔄 Recarregando systemd..."
sudo systemctl daemon-reload
sudo systemctl reset-failed

if [ -f "$SECOND_SH" ]; then
    echo "🗑️ Removendo script auxiliar: $SECOND_SH"
    rm "$SECOND_SH"
else
    echo "⚠️ Script auxiliar não encontrado: $SECOND_SH"
fi

echo "✅ Serviço $SERVICE_NAME removido com sucesso."
