# NextPubli Raspberry 1.0.0

Esta pasta contem a aplicacao do player de publicidade que roda no Raspberry. A versao `1.0.0` e a primeira versao preparada para ser instalada e iniciada pelo launcher em vez de ser configurada manualmente por cliente.

## Como a aplicacao inicia

O `main.py` nao deve ser iniciado manualmente no fluxo normal. Quem inicia a aplicacao e o launcher instalado em:

```text
~/nextpubli_launcher/
```

O launcher baixa o ZIP da release, extrai em `runtime/releases/1.0.0/` e executa:

```bash
/usr/bin/python3 main.py
```

Antes de iniciar, o launcher envia as variaveis de ambiente que a aplicacao precisa:

```text
NEUROON_SERIAL_DISPOSITIVO
NEUROON_ID_DISPOSITIVO
NEUROON_ID_LOCAL
NEUROON_APP_VERSION
NEUROON_API_BASE_URL
```

A variavel obrigatoria e:

```text
NEUROON_ID_LOCAL
```

Se ela nao existir ou for invalida, o app encerra com erro. Isso evita rodar o player apontando para um local errado.

## Arquivos principais

```text
main.py
requirements.txt
README.md
```

- `main.py`: aplicacao PyQt5 principal.
- `requirements.txt`: dependencias Python usadas pelo app.
- `README.md`: este documento.

Arquivos de instalacao do Linux, como Piper e dependencias do sistema, nao ficam nesta pasta. Eles ficam como scripts da release em:

```text
nextpubli_raspberry/raspberry/raspberry_releases/1.0.0/scripts/
```

Esses scripts sao retornados pela API do launcher e executados antes do app iniciar.

## Dependencias

Dependencias Python:

```text
PyQt5
requests
```

Dependencias de sistema esperadas no Raspberry:

```text
python3
python3-pip
python3-venv
python3-requests
python3-pyqt5
python3-pyqt5.qtmultimedia
libqt5multimedia5-plugins
alsa-utils
ffmpeg
```

O recurso de voz usa Piper em uma venv separada:

```text
~/piper-venv/bin/python
~/piper-voices/
```

Essa instalacao e feita pelo script `02_install_piper.sh` da release.

## APIs usadas

A base da API vem de:

```text
NEUROON_API_BASE_URL
```

Se nao vier do launcher, o app usa:

```text
https://example.com/nextpubli/api/raspberry
```

Endpoints consumidos pelo `main.py`:

```text
get_configuracoes.php?id_local=...
get_publicidade.php?id_local=...
get_informativo.php
get_posicao_tela.php?id_local=...
get_senhas_chamada.php?id_local=...
insert_publicidade_exibicao.php
ping_aparelho.php?id_local=...
```

Importante: as APIs antigas continuam recebendo `id_local`. A conversao de `serial_dispositivo` para `id_local` acontece antes, no launcher e nas APIs novas do servidor.

## Funcionalidades

### Configuracoes remotas

Ao iniciar, o app chama `get_configuracoes.php` e aplica intervalos, tempos de exibicao e tamanhos de fonte. Se a API falhar, ele tenta novamente a cada 5 segundos ate carregar.

### Playlist de publicidade

O app consulta `get_publicidade.php` periodicamente. Quando a lista muda, ele baixa as novas midias para a pasta local:

```text
midias/
```

Depois reproduz imagens e videos em loop.

Formatos aceitos:

```text
Videos: .mp4, .avi, .mov, .mkv
Imagens: .jpg, .jpeg, .png, .gif, .bmp
```

### Informativos

O app consulta `get_informativo.php` e exibe informativos em uma area lateral ou inferior, dependendo do formato de tela.

### Formato da tela

O app consulta `get_posicao_tela.php` e adapta o layout pelo campo `formato_tela`.

Formatos tratados:

```text
1: layout horizontal com midia e informativos
2: layout vertical, mantendo a tela fisica na horizontal
3: fullscreen para midia
4: layout com chamadas de senha
```

Valores fora dessa lista sao ignorados.

### Chamadas de senha

No formato `4`, o app inicia a consulta a `get_senhas_chamada.php`.

Quando recebe senhas:

- mostra o painel "Chamadas";
- destaca a senha principal;
- lista as demais senhas;
- aciona audio de chamada via Piper;
- faz rolagem automatica se a lista for maior que o painel.

Se ficar sem senhas pelo tempo configurado, o app volta para o layout fullscreen.

### Audio das chamadas

O audio usa Piper local:

```text
~/piper-venv/bin/python -m piper
```

Modelo padrao:

```text
pt_BR-faber-medium
```

Player de audio:

```text
aplay
```

Se Piper ou a pasta de vozes nao existirem, o app continua rodando e registra o problema no log.

### Ping de atividade

O app chama `ping_aparelho.php` periodicamente enviando:

```text
versao_app=1.0.0
```

Isso permite o servidor atualizar status online/offline e versao em execucao.

### Registro de exibicoes

Quando uma midia termina, o app guarda uma exibicao pendente. Periodicamente ele envia essas exibicoes para `insert_publicidade_exibicao.php`.

Ao fechar a aplicacao, ele tenta enviar as exibicoes restantes antes de encerrar.

## Atalhos e operacao

Tecla para encerrar a aplicacao:

```text
Q
```

No fluxo real, prefira controlar pelo servico:

```bash
sudo systemctl restart service_media
sudo systemctl stop service_media
sudo systemctl start service_media
```

Logs do servico:

```bash
journalctl -u service_media -f
```

Logs do launcher:

```bash
tail -f ~/nextpubli_launcher/logs/launcher.log
```

## Como rodar manualmente para teste

Normalmente nao e necessario, mas para testar fora do launcher:

```bash
cd caminho/da/versao/1.0.0
export NEUROON_ID_LOCAL=2
export NEUROON_APP_VERSION=1.0.0
export NEUROON_API_BASE_URL=https://example.com/nextpubli/api/raspberry
/usr/bin/python3 main.py
```

Em ambiente grafico Linux, tambem pode ser necessario:

```bash
export DISPLAY=:0
export XAUTHORITY=/home/pi/.Xauthority
```

## Cuidados ao alterar

- Nao voltar a colocar `ID_LOCAL` fixo no codigo.
- Manter `NEUROON_ID_LOCAL` como fonte do local.
- Se mudar arquivos desta pasta, gere novamente o ZIP da release.
- Depois de gerar o ZIP, recalcule o SHA-256 e atualize o `manifest.json` e o SQL da release.
- Scripts de instalacao devem ficar em `raspberry_releases/<versao>/scripts/`, nao dentro desta pasta.

