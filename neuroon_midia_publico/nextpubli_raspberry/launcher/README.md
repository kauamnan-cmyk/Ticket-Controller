# Neuroon Publicidade Launcher

Este launcher fica instalado uma unica vez no Raspberry. O servico Linux inicia o launcher, e o launcher consulta o servidor para decidir qual versao do player baixar e executar.

## Estrutura no Raspberry

Copie esta pasta para:

```bash
~/nextpubli_launcher
```

Estrutura em uso:

```text
~/nextpubli_launcher/
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
    device_identity.json
  logs/
    launcher.log
```

O launcher limpa somente `runtime/releases`, `runtime/scripts` e `runtime/tmp` quando instala uma nova versao. Ele nao apaga `config`, `state` nem `logs`.

## Configuracao unica do dispositivo

Edite:

```bash
nano ~/nextpubli_launcher/config/device_config.json
```

Campo principal:

```json
{
  "serial_dispositivo": "CONFIGURE_O_SERIAL_DO_RASPBERRY",
  "api_base_url": "https://example.com/nextpubli/api/raspberry",
  "release_endpoint": "get_launcher_release.php"
}
```

Endpoint chamado:

```text
https://example.com/nextpubli/api/raspberry/get_launcher_release.php?serial_dispositivo=SERIAL_DO_RASPBERRY
```

O servidor resolve `id_dispositivo` e `id_local`. O player continua chamando as APIs atuais com `id_local`.

## Instalar o servico

```bash
cd ~/nextpubli_launcher/config
chmod +x instalar_servico_launcher.sh
./instalar_servico_launcher.sh
```

O servico criado continua se chamando `service_media`.

## Remover o servico

```bash
cd ~/nextpubli_launcher/config
chmod +x remover_servico_launcher.sh
./remover_servico_launcher.sh
```

## Resposta esperada da API

```json
{
  "success": true,
  "serial_dispositivo": "CONFIGURE_O_SERIAL_DO_RASPBERRY",
  "id_dispositivo": 10,
  "id_local": 2,
  "version": "1.0.0",
  "package_url": "https://example.com/nextpubli/raspberry_releases/1.0.0/1.0.0.zip",
  "package_sha256": "hash_sha256_do_zip",
  "entrypoint": "main.py",
  "scripts": [
    {
      "name": "01_install_system.sh",
      "url": "https://example.com/nextpubli/raspberry_releases/1.0.0/scripts/01_install_system.sh",
      "sha256": "hash_sha256_do_script",
      "run_as": "sudo"
    }
  ]
}
```

Regras:

- `version` vira o nome da pasta dentro de `runtime/releases`.
- `package_url` deve apontar para um arquivo `.zip`.
- `package_sha256` e `scripts[].sha256` sao obrigatorios.
- `entrypoint` normalmente sera `main.py`.
- `scripts` pode vir vazio.
- Os scripts rodam na ordem recebida.
- `run_as` aceita `user` ou `sudo`.
- Se a API falhar, o launcher tenta iniciar a ultima versao instalada.

## Variaveis enviadas ao player

Ao iniciar o app, o launcher define:

```text
NEUROON_SERIAL_DISPOSITIVO
NEUROON_ID_DISPOSITIVO
NEUROON_ID_LOCAL
NEUROON_APP_VERSION
NEUROON_API_BASE_URL
```

## Tutorial rapido para publicar uma nova versao

Exemplo criando a versao `1.0.1`.

### 1. Criar a pasta da aplicacao

Copie a versao anterior:

```text
nextpubli_raspberry/raspberry/1.0.0/
```

Para:

```text
nextpubli_raspberry/raspberry/1.0.1/
```

Altere o app dentro da nova pasta. A aplicacao deve continuar lendo o local por:

```text
NEUROON_ID_LOCAL
```

Nao coloque `id_local` fixo no codigo.

### 2. Criar a pasta publica da release

Crie:

```text
nextpubli_raspberry/raspberry/raspberry_releases/1.0.1/
  scripts/
```

O conteudo dessa pasta sera publicado no servidor em:

```text
/nextpubli/raspberry_releases/1.0.1/
```

### 3. Gerar o ZIP da aplicacao

O ZIP deve conter os arquivos da aplicacao na raiz do ZIP, por exemplo:

```text
main.py
requirements.txt
```

No PowerShell:

```powershell
Compress-Archive `
  -Path nextpubli_raspberry\raspberry\1.0.1\* `
  -DestinationPath nextpubli_raspberry\raspberry\raspberry_releases\1.0.1\1.0.1.zip `
  -Force
```

### 4. Criar ou copiar os scripts Linux

Coloque os scripts em:

```text
nextpubli_raspberry/raspberry/raspberry_releases/1.0.1/scripts/
```

Exemplo:

```text
01_install_system.sh
02_install_piper.sh
```

Os scripts precisam ser idempotentes: podem rodar mais de uma vez sem quebrar a maquina.

### 5. Calcular os SHA-256

No PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 nextpubli_raspberry\raspberry\raspberry_releases\1.0.1\1.0.1.zip
Get-FileHash -Algorithm SHA256 nextpubli_raspberry\raspberry\raspberry_releases\1.0.1\scripts\01_install_system.sh
Get-FileHash -Algorithm SHA256 nextpubli_raspberry\raspberry\raspberry_releases\1.0.1\scripts\02_install_piper.sh
```

Use os hashes em minusculo no `manifest.json` e no SQL.

### 6. Criar o manifest.json

Crie:

```text
nextpubli_raspberry/raspberry/raspberry_releases/1.0.1/manifest.json
```

Modelo:

```json
{
  "version": "1.0.1",
  "entrypoint": "main.py",
  "package_path": "raspberry_releases/1.0.1/1.0.1.zip",
  "package_sha256": "sha256_do_zip",
  "scripts": [
    {
      "execution_order": 1,
      "name": "01_install_system.sh",
      "script_path": "raspberry_releases/1.0.1/scripts/01_install_system.sh",
      "script_sha256": "sha256_do_script_01",
      "run_as": "sudo"
    },
    {
      "execution_order": 2,
      "name": "02_install_piper.sh",
      "script_path": "raspberry_releases/1.0.1/scripts/02_install_piper.sh",
      "script_sha256": "sha256_do_script_02",
      "run_as": "user"
    }
  ]
}
```

### 7. Subir arquivos para o servidor

Suba:

```text
nextpubli_raspberry/raspberry/raspberry_releases/1.0.1/
```

Para:

```text
/nextpubli/raspberry_releases/1.0.1/
```

### 8. Inserir a release no banco

Antes, garanta que `schema_launcher.sql` ja foi executado uma vez no servidor.

Depois rode um SQL como este, trocando os hashes:

```sql
UPDATE raspberry_releases
SET is_active = 0
WHERE is_active = 1;

INSERT INTO raspberry_releases (
  version,
  package_path,
  package_sha256,
  entrypoint,
  status,
  is_active,
  published_at
) VALUES (
  '1.0.1',
  'raspberry_releases/1.0.1/1.0.1.zip',
  'sha256_do_zip',
  'main.py',
  'published',
  1,
  NOW()
)
ON DUPLICATE KEY UPDATE
  package_path = VALUES(package_path),
  package_sha256 = VALUES(package_sha256),
  entrypoint = VALUES(entrypoint),
  status = VALUES(status),
  is_active = VALUES(is_active),
  published_at = VALUES(published_at);

SET @release_id = (
  SELECT id_release
  FROM raspberry_releases
  WHERE version = '1.0.1'
  LIMIT 1
);

DELETE FROM raspberry_release_scripts
WHERE id_release = @release_id;

INSERT INTO raspberry_release_scripts (
  id_release,
  execution_order,
  name,
  script_path,
  script_sha256,
  run_as,
  is_enabled
) VALUES
(
  @release_id,
  1,
  '01_install_system.sh',
  'raspberry_releases/1.0.1/scripts/01_install_system.sh',
  'sha256_do_script_01',
  'sudo',
  1
),
(
  @release_id,
  2,
  '02_install_piper.sh',
  'raspberry_releases/1.0.1/scripts/02_install_piper.sh',
  'sha256_do_script_02',
  'user',
  1
);
```

### 9. Atualizar no Raspberry

O launcher consulta updates no start. Para aplicar logo:

```bash
sudo systemctl restart service_media
```

Para acompanhar:

```bash
journalctl -u service_media -f
tail -f ~/nextpubli_launcher/logs/launcher.log
```

## Logs

Logs do servico:

```bash
journalctl -u service_media -f
```

Logs do launcher:

```bash
tail -f ~/nextpubli_launcher/logs/launcher.log
```

## Forcar reinstalacao

```bash
sudo systemctl stop service_media
rm ~/nextpubli_launcher/state/current_release.json
sudo systemctl start service_media
```

Se quiser limpar tambem os arquivos baixados:

```bash
rm -rf ~/nextpubli_launcher/runtime/releases ~/nextpubli_launcher/runtime/scripts ~/nextpubli_launcher/runtime/tmp
sudo systemctl start service_media
```
