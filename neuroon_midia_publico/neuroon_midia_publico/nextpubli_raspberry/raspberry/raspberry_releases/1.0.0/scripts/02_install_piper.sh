#!/bin/bash
set -e

PIPER_VENV="$HOME/piper-venv"
PIPER_DATA_DIR="$HOME/piper-voices"
PIPER_MODEL="pt_BR-faber-medium"

if [ ! -x "$PIPER_VENV/bin/python" ]; then
  python3 -m venv "$PIPER_VENV"
fi

"$PIPER_VENV/bin/python" -m pip install --upgrade pip
"$PIPER_VENV/bin/pip" install --upgrade piper-tts

mkdir -p "$PIPER_DATA_DIR"

if ! find "$PIPER_DATA_DIR" -name "${PIPER_MODEL}*.onnx" -print -quit | grep -q .; then
  "$PIPER_VENV/bin/python" -m piper.download_voices "$PIPER_MODEL" --data-dir "$PIPER_DATA_DIR"
fi

test -x "$PIPER_VENV/bin/python"
test -d "$PIPER_DATA_DIR"
command -v aplay >/dev/null

