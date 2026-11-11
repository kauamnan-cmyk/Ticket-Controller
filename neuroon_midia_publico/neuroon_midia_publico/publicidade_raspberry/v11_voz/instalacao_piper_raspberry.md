# Instalacao do Piper TTS no Raspberry

Este projeto usa o Piper em uma venv separada da aplicacao principal. O `main.py` chama o interpretador da venv diretamente, entao nao precisa ativar a venv no `systemd`, nem criar outro `.sh`.

Configuracao esperada pelo `main.py`:

- Python do Piper: `~/piper-venv/bin/python`
- Pasta das vozes: `~/piper-voices`
- Modelo padrao: `pt_BR-faber-medium`
- Player de audio: `aplay`

## 1. Instalar dependencias do sistema

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip alsa-utils ffmpeg
```

`alsa-utils` fornece o `aplay`, usado para tocar o WAV gerado pelo Piper.

## 2. Criar a venv do Piper

```bash
python3 -m venv ~/piper-venv
~/piper-venv/bin/python -m pip install --upgrade pip
~/piper-venv/bin/pip install piper-tts
```

## 3. Baixar uma voz pt-BR

```bash
mkdir -p ~/piper-voices
~/piper-venv/bin/python -m piper.download_voices pt_BR-faber-medium --data-dir ~/piper-voices
```

Vozes pt-BR que podemos testar depois:

- `pt_BR-faber-medium`
- `pt_BR-cadu-medium`
- `pt_BR-jeff-medium`
- `pt_BR-edresson-low`

Para trocar a voz, baixe outro modelo e altere `PIPER_MODEL` no `main.py`.

## 4. Testar geracao e reproducao

```bash
~/piper-venv/bin/python -m piper \
  -m pt_BR-faber-medium \
  --data-dir ~/piper-voices \
  -f /tmp/senha.wav \
  -- "Maria Oliveira, senha vinte e tres."

aplay /tmp/senha.wav
```

Se o audio sair baixo ou mudo, ajuste o volume:

```bash
alsamixer
```

## 5. Como o boot funciona

O servico atual continua iniciando a aplicacao normalmente. Quando uma senha nova chega, o `main.py` executa:

```bash
~/piper-venv/bin/python -m piper ...
aplay /tmp/senha_chamada_x.wav
```

Portanto, a venv nao precisa ser ativada no boot. Ela so precisa existir no caminho esperado.

## 6. Reinstalar ou atualizar a voz

```bash
~/piper-venv/bin/pip install --upgrade piper-tts
~/piper-venv/bin/python -m piper.download_voices pt_BR-faber-medium --data-dir ~/piper-voices
```

## 7. Validacao rapida antes de rodar a aplicacao

```bash
test -x ~/piper-venv/bin/python && echo "Piper Python OK"
test -d ~/piper-voices && echo "Piper voices OK"
command -v aplay && echo "aplay OK"
```

Depois dessa instalacao unica, a aplicacao `v11_voz` deve conseguir falar as chamadas sem alterar o instalador do servico.