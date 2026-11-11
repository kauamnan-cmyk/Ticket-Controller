# Instalacao para testes no Windows

Esta pasta `v11_voz_windows` e para testar o fluxo localmente no Windows. Aqui nao usamos os `.sh` de servico do Raspberry; basta criar uma venv, instalar os requirements e rodar o `main.py`.

No Windows, o audio usa `pyttsx3`, que e um motor TTS offline baseado nas vozes instaladas no sistema. Isso serve para validar o fluxo completo de chamadas: detectar senha nova, montar o texto, enfileirar audios e esperar uma fala terminar antes da proxima.

No Raspberry/Linux, a pasta `v11_voz` continua usando Piper TTS local.

## 1. Criar a venv

No PowerShell, dentro da pasta `v11_voz_windows`:

```powershell
cd C:/Users/USUARIO\Documents\GitHub\neuroon_midia\publicidade_raspberry\v11_voz_windows
py -3 -m venv .venv
```

Se `py` nao existir, tente:

```powershell
python -m venv .venv
```

## 2. Ativar a venv

```powershell
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear scripts, libere apenas para esta sessao:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. Instalar dependencias

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

O `requirements.txt` inclui:

- `PyQt5`, para a interface;
- `requests`, para chamadas HTTP;
- `pyttsx3`, para TTS offline no Windows.

## 4. Rodar o app no Windows

```powershell
python main.py
```

Nesta versao Windows, nao rode `config/instalar_servico.sh`. Esse script e para o Raspberry/Linux com systemd.

## 5. Como o audio funciona no teste

Quando uma senha nova chega:

1. `update_senhas_chamada` detecta a senha nova.
2. A chamada entra na fila do `SenhaSpeechManager`.
3. No Windows, o manager usa `pyttsx3` para falar o texto.
4. `engine.runAndWait()` so retorna quando a fala termina.
5. A proxima chamada da fila comeca apenas depois disso.

## 6. Problemas comuns

Se nao sair audio:

```powershell
python -c "import pyttsx3; e=pyttsx3.init(); e.say('Teste de audio'); e.runAndWait()"
```

Se esse teste tambem nao falar, confira o volume do Windows e as vozes instaladas em:

```text
Configuracoes > Hora e idioma > Fala
```

Se a aplicacao abrir mas nao tiver dados reais da API, isso e esperado em alguns ambientes de rede. O teste principal aqui e validar que, quando uma senha entra no fluxo, a fila e o TTS funcionam.