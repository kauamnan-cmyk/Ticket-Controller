# Neuroon Publicidade Launcher

Este launcher fica instalado uma unica vez no Raspberry. O servico Linux passa a iniciar o launcher, e o launcher decide qual versao do player baixar e executar.

## Estrutura esperada

No Raspberry, copie esta pasta para:

```bash
~/v12_launcher
```

Estrutura em uso:

```text
~/v12_launcher/
  launcher.py
  config/
    device_config.json
    instalar_servico_launcher.sh
    remover_servico_launcher.sh
  runtime/
    releases/
    scripts/
    tmp/
  state/
    current_release.json
  logs/
    launcher.log
```

O launcher limpa somente `runtime/releases`, `runtime/scripts` e `runtime/tmp` quando instala uma nova versao. Ele nao apaga `config`, `state` nem `logs`.

## Configuracao do dispositivo

Edite:

```bash
nano ~/v12_launcher/config/device_config.json
```

Campos principais:

```json
{
  "id_local": 2,
  "api_base_url": "https://example.com/nextpubli/api/raspberry",
  "release_endpoint": "get_launcher_release.php"
}
```

O endpoint chamado sera:

```text
https://example.com/nextpubli/api/raspberry/get_launcher_release.php?id_local=2
```

## Instalar o servico

```bash
cd ~/v12_launcher/config
chmod +x instalar_servico_launcher.sh
./instalar_servico_launcher.sh
```

O servico criado continua se chamando `service_media`.

## Remover o servico

```bash
cd ~/v12_launcher/config
chmod +x remover_servico_launcher.sh
./remover_servico_launcher.sh
```

## Resposta esperada da API

```json
{
  "success": true,
  "id_local": 2,
  "version": "v11_voz",
  "package_url": "https://example.com/nextpubli/releases/v11_voz.zip",
  "entrypoint": "main.py",
  "scripts": [
    {
      "name": "install_system.sh",
      "url": "https://example.com/nextpubli/releases/v11_voz/install_system.sh",
      "run_as": "sudo"
    },
    {
      "name": "install_app.sh",
      "url": "https://example.com/nextpubli/releases/v11_voz/install_app.sh",
      "run_as": "user"
    }
  ]
}
```

Regras:

- `version` vira o nome da pasta dentro de `runtime/releases`.
- `package_url` deve apontar para um arquivo `.zip`.
- `entrypoint` normalmente sera `main.py`.
- `scripts` pode vir vazio.
- Os scripts rodam na ordem recebida.
- `run_as` aceita `user` ou `sudo`.
- Se a API falhar, o launcher tenta iniciar a ultima versao instalada.

## Formato do zip da versao

O zip pode conter os arquivos direto na raiz:

```text
main.py
requirements.txt
...
```

Ou pode conter uma pasta unica:

```text
v11_voz/
  main.py
  requirements.txt
```

O launcher procura o `entrypoint` nesses dois formatos.

## Scripts de instalacao

Os scripts retornados pela API precisam ser idempotentes: podem rodar de novo sem quebrar a maquina.

Exemplo de `install_system.sh`:

```bash
#!/bin/bash
set -e
sudo apt update
sudo apt install -y python3-venv python3-pip alsa-utils ffmpeg
```

Exemplo de `install_app.sh`:

```bash
#!/bin/bash
set -e
cd "$HOME/v12_launcher/runtime/releases/v11_voz"
/usr/bin/python3 -m pip install -r requirements.txt
```

Para uma versao com Piper, o script pode criar `~/piper-venv` e baixar as vozes, seguindo o guia da versao `v11_voz`.

## Logs

Logs do servico:

```bash
journalctl -u service_media -f
```

Logs do launcher:

```bash
tail -f ~/v12_launcher/logs/launcher.log
```

## Forcar reinstalacao

Pare o servico, apague o estado local e reinicie:

```bash
sudo systemctl stop service_media
rm ~/v12_launcher/state/current_release.json
sudo systemctl start service_media
```

Se quiser limpar tambem os arquivos baixados:

```bash
rm -rf ~/v12_launcher/runtime/releases ~/v12_launcher/runtime/scripts ~/v12_launcher/runtime/tmp
sudo systemctl start service_media
```

## Voltar manualmente para uma versao anterior

Se a pasta da versao anterior ainda existir, edite:

```bash
nano ~/v12_launcher/state/current_release.json
```

Exemplo:

```json
{
  "version": "v10_regis",
  "entrypoint": "main.py",
  "package_url": "",
  "installed_at": "manual"
}
```

Depois reinicie:

```bash
sudo systemctl restart service_media
```

Observacao: se a API ainda apontar para outra versao, o launcher vai tentar instalar a versao remota novamente na proxima inicializacao.
