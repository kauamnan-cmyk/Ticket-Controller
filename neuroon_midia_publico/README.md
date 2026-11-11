# Neuroon Midia - Raspberry

Este documento descreve o novo fluxo de desenvolvimento e publicacao da aplicacao do Raspberry dentro de `nextpubli_raspberry`.

As pastas antigas em `publicidade_raspberry` ficam como historico. O fluxo novo deve usar somente:

```text
nextpubli_raspberry/
  apis_servidor/
  launcher/
  raspberry/
```

## Ideia geral

O Raspberry deixa de receber manualmente uma pasta completa da aplicacao a cada atualizacao.

Agora o processo fica assim:

1. O Raspberry instala uma unica vez o launcher em `~/nextpubli_launcher`.
2. O arquivo manual do Raspberry guarda apenas o `serial_dispositivo`.
3. No boot, o servico `service_media` inicia o launcher.
4. O launcher consulta a API `get_launcher_release.php`.
5. O servidor identifica o dispositivo, resolve o `id_local` e informa a release ativa.
6. O launcher baixa o ZIP da versao, valida o SHA-256, baixa os scripts, valida os scripts e executa a instalacao.
7. O launcher inicia o `main.py` da versao instalada, enviando `NEUROON_ID_LOCAL` por variavel de ambiente.

As APIs antigas continuam recebendo `id_local`. A diferenca e que o `id_local` nao fica mais fixo no codigo do app.

## Estrutura local

```text
nextpubli_raspberry/
  apis_servidor/
    identificar_dispositivo.php
    get_launcher_release.php
    launcher_helpers.php
    schema_launcher.sql
    seed_release_1_0_0.sql
    ...

  launcher/
    launcher.py
    README.md
    config/
      device_config.json
      instalar_servico_launcher.sh
      remover_servico_launcher.sh

  raspberry/
    1.0.0/
      main.py
      requirements.txt

    raspberry_releases/
      1.0.0/
        1.0.0.zip
        manifest.json
        scripts/
          01_install_system.sh
          02_install_piper.sh
```

## O que sobe para o servidor

No servidor, dentro do projeto publico `nextpubli`, as APIs novas ficam junto das APIs atuais:

```text
/nextpubli/api/raspberry/
  identificar_dispositivo.php
  get_launcher_release.php
  launcher_helpers.php
```

Os artefatos das releases ficam em uma pasta publica:

```text
/nextpubli/raspberry_releases/
  1.0.0/
    1.0.0.zip
    manifest.json
    scripts/
      01_install_system.sh
      02_install_piper.sh
```

No repo local essa pasta fica em:

```text
nextpubli_raspberry/raspberry/raspberry_releases/
```

Ao publicar, suba o conteudo dela para:

```text
/nextpubli/raspberry_releases/
```

## Banco de dados

Execute uma vez:

```text
nextpubli_raspberry/apis_servidor/schema_launcher.sql
```

Para publicar a release inicial `1.0.0`, execute:

```text
nextpubli_raspberry/apis_servidor/seed_release_1_0_0.sql
```

As tabelas novas guardam os metadados das releases e dos scripts. Os arquivos em si ficam no filesystem do servidor.

## Launcher no Raspberry

Copie para o Raspberry:

```text
nextpubli_raspberry/launcher/
```

Destino recomendado:

```text
~/nextpubli_launcher/
```

Edite apenas:

```text
~/nextpubli_launcher/config/device_config.json
```

Configure:

```json
{
  "serial_dispositivo": "CONFIGURE_O_SERIAL_DO_RASPBERRY"
}
```

Depois instale o servico:

```bash
cd ~/nextpubli_launcher/config
chmod +x instalar_servico_launcher.sh
./instalar_servico_launcher.sh
```

O servico continua se chamando `service_media`.

## Criando uma nova versao

Para criar uma nova versao, por exemplo `1.0.1`:

1. Copie a pasta da versao anterior em `nextpubli_raspberry/raspberry/`.
2. Ajuste o app, mantendo o `id_local` vindo de `NEUROON_ID_LOCAL`.
3. Gere o ZIP da versao.
4. Coloque o ZIP em `nextpubli_raspberry/raspberry/raspberry_releases/1.0.1/`.
5. Coloque os scripts Linux necessarios em `scripts/`.
6. Calcule os SHA-256 do ZIP e dos scripts.
7. Atualize o `manifest.json`.
8. Crie ou atualize um seed SQL para apontar a release ativa para a nova versao.
9. Suba os artefatos para `/nextpubli/raspberry_releases/1.0.1/`.
10. Rode o SQL no servidor.

Depois disso, no proximo boot/restart do servico, o launcher baixa e instala a nova versao.

## SHA-256

Cada ZIP e cada script publicado tem um SHA-256. Ele funciona como uma impressao digital do arquivo.

O launcher baixa o arquivo, calcula o SHA-256 localmente e compara com o valor informado pela API. Se for diferente, a instalacao para.

Isso evita instalar arquivo corrompido, incompleto ou diferente do esperado.

Sempre que alterar o ZIP ou qualquer script, recalcule o hash e atualize:

```text
manifest.json
seed_release_*.sql
banco de dados do servidor
```

No Windows:

```powershell
Get-FileHash -Algorithm SHA256 caminho\do\arquivo
```

No Linux:

```bash
sha256sum caminho/do/arquivo
```

## Variaveis que o launcher envia ao app

O launcher inicia o `main.py` com estas variaveis:

```text
NEUROON_SERIAL_DISPOSITIVO
NEUROON_ID_DISPOSITIVO
NEUROON_ID_LOCAL
NEUROON_APP_VERSION
NEUROON_API_BASE_URL
```

A aplicacao deve usar `NEUROON_ID_LOCAL` para chamar as APIs antigas.

## Logs uteis

Servico:

```bash
journalctl -u service_media -f
```

Launcher:

```bash
tail -f ~/nextpubli_launcher/logs/launcher.log
```

## Regra importante

Nao altere as APIs antigas para receber `serial_dispositivo`.

O fluxo correto e:

```text
serial_dispositivo -> API nova -> id_dispositivo -> id_local -> APIs antigas
```

Assim o app novo continua compativel com o backend atual, mas sem precisar editar `id_local` dentro do codigo a cada cliente.
