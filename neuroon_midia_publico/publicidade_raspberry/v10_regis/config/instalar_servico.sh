#!/bin/bash

# Nome do script Python
SCRIPT_NAME="main.py"

# Pasta onde está o script
SCRIPT_FOLDER="v9_foto"

# Caminho absoluto do script
SCRIPT_PATH="$HOME/$SCRIPT_FOLDER/$SCRIPT_NAME"

# Caminho para o segundo script shell que executará o Python
SECOND_SH="$HOME/start_media.sh"

# Nome e caminho do serviço systemd
SERVICE_NAME="service_media"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

# Usuário atual
USER_NAME=$(whoami)
HOME_DIR=$HOME

# ========== PASSO 1: Verifica se o script Python existe ==========
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ Script .py não encontrado no caminho: $SCRIPT_PATH"
    exit 1
fi

echo "✅ Caminho do script Python: $SCRIPT_PATH"

# ========== PASSO 2: Cria o segundo script shell ==========
echo "📄 Criando script de execução: $SECOND_SH"
cat <<EOF > "$SECOND_SH"
#!/bin/bash
export DISPLAY=:0
export XAUTHORITY=/home/$USER_NAME/.Xauthority
/usr/bin/python3 "$SCRIPT_PATH"
EOF

chmod +x "$SECOND_SH"

if [ -f "$SERVICE_FILE" ]; then
    echo "ℹ️ Serviço já existe: $SERVICE_FILE"

    STATUS_BOOT=$(systemctl is-enabled "$SERVICE_NAME" 2>/dev/null)

    if [ "$STATUS_BOOT" = "enabled" ]; then
        echo "✅ Serviço já está habilitado no boot"
    else
        echo "🔁 Habilitando serviço para iniciar no boot..."
        sudo systemctl enable "$SERVICE_NAME"
    fi

    echo "🚀 Iniciando o serviço..."
    sudo systemctl start "$SERVICE_NAME"
else
    echo "🛠️ Serviço não existe. Criando..."

    SERVICE_CONTENT="[Unit]
Description=Serviço para executar $SCRIPT_NAME no boot via start_media.sh
After=graphical.target
Wants=graphical.target

[Service]
ExecStart=$SECOND_SH
WorkingDirectory=$HOME_DIR
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

    echo "🔄 Recarregando daemon do systemd..."
    sudo systemctl daemon-reload

    echo "📌 Habilitando serviço para iniciar no boot..."
    sudo systemctl enable "$SERVICE_NAME"

    echo "🚀 Iniciando serviço agora..."
    sudo systemctl start "$SERVICE_NAME"

    echo "✅ Serviço criado, habilitado e iniciado com sucesso."
fi

