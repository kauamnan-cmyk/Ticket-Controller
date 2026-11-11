# Plano: audio para chamada de senhas

## Decisao

Vamos usar Piper TTS local no Raspberry, em uma venv separada da aplicacao principal. O app nao precisa ativar a venv no boot: o `main.py` chama diretamente `~/piper-venv/bin/python -m piper` quando precisar gerar uma fala.

## Fluxo no codigo

- `SenhasChamadaApiThread` busca as senhas da API.
- `update_senhas_chamada` compara a lista anterior com a nova.
- Apenas senhas novas entram na fila de audio.
- `SenhaSpeechManager` consome a fila em uma thread separada.
- O proximo audio so comeca depois que o `aplay` do audio atual terminar.

## Texto falado

Formato base:

```text
{cliente_nome}, senha {senha_codigo}
```

Se o nome vier vazio, fala apenas:

```text
Senha {senha_codigo}
```

## Cuidados

- O nome usado no audio e o nome completo da API, nao o nome abreviado da tela.
- No Windows, o recurso fica em modo de teste e imprime `[AUDIO TESTE] ...`.
- No Raspberry, o recurso exige a instalacao descrita em `instalacao_piper_raspberry.md`.
- Se o Piper nao estiver instalado, a tela continua funcionando e o audio e desativado por log.