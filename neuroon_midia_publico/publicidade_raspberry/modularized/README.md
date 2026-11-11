# Documentação do Projeto de Player de Publicidade Modularizado

## 1. Introdução

Este documento detalha a modularização da aplicação de player digital de publicidade e informativos em PyQt5. O objetivo principal foi reorganizar o código-fonte original (`main.py`) em uma estrutura mais modular, facilitando a manutenção, organização e reuso de componentes, sem alterar o funcionamento visual e lógico da aplicação.

A aplicação é um player digital que exibe mídias (imagens e vídeos), informativos de texto com imagem e widgets de rodapé (clima, cotação de dólar, bitcoin e hora), consumindo conteúdo via APIs e exibindo em tela cheia. Ela suporta alternância entre layouts horizontal e vertical dinamicamente.




## 2. Estrutura do Projeto

O projeto foi reorganizado nas seguintes pastas para melhor separação de responsabilidades:

- `core/`: Contém a janela principal (`PublicidadePlayer`), a lógica de layouts e a criação dos widgets da interface gráfica. O arquivo `main.py` original foi movido para `core/main.py`.
- `threads/`: Contém as classes de threads responsáveis por consultar as APIs periodicamente. Cada thread foi separada em seu próprio arquivo:
    - `publicidade_api_thread.py`: Responsável pela consulta da API de publicidade.
    - `informativo_api_thread.py`: Responsável pela consulta da API de informativos.
    - `posicao_tela_api_thread.py`: Responsável pela consulta da API de formato de tela.
- `services/`: Destinado a módulos que tratam da comunicação com APIs, gerenciamento de mídias (download, verificação e contagem) e controle de informativos. (Atualmente, parte dessa lógica ainda reside em `core/main.py` e pode ser refatorada para cá em futuras iterações).
- `config/`: Armazena configurações globais, URLs de API, intervalos de tempo, tamanhos de fonte e caminhos de diretórios. O arquivo `constants.py` foi criado para centralizar essas definições.
- `utils/`: Destinado a funções auxiliares e módulos de logging, se necessário. (Atualmente vazio).
- `midias/`: Pasta para armazenamento de arquivos de mídia (imagens e vídeos) baixados.
- `icons/`: Pasta para armazenamento de arquivos de ícones.
- `main.py`: O novo ponto de entrada da aplicação, que importa e executa a classe `PublicidadePlayer` de `core/main.py`.




## 3. Mudanças e Refatoração

As principais mudanças e refatorações realizadas foram:

- **Separação de Constantes**: Todas as constantes globais, como URLs de API, intervalos de tempo e tamanhos de fonte, foram movidas do `main.py` original para `config/constants.py`. Isso centraliza as configurações e facilita futuras modificações.

- **Modularização das Threads de API**: As classes de threads (`PublicidadeApiThread`, `InformativoApiThread`, `PosicaoTelaApiThread`) foram extraídas do `main.py` e movidas para arquivos individuais dentro da pasta `threads/`. Cada arquivo agora contém a lógica específica para a consulta de sua respectiva API, emitindo sinais para a janela principal quando os dados são atualizados ou erros ocorrem.

- **Ponto de Entrada Simplificado**: Um novo arquivo `main.py` foi criado na raiz do projeto. Este arquivo é minimalista e tem como única responsabilidade iniciar a aplicação PyQt5 e instanciar a classe `PublicidadePlayer` (agora localizada em `core/main.py`).

- **Ajustes de Importação**: As importações dentro de `core/main.py` e dos novos arquivos de thread foram atualizadas para refletir a nova estrutura de diretórios, utilizando importações relativas ou absolutas conforme necessário.

- **Preservação de Funcionalidades**: Todas as funcionalidades existentes da aplicação original foram mantidas, incluindo:
    - Exibição de publicidade (imagens e vídeos) com download e contagem de exibições.
    - Exibição de informativos com texto e imagem.
    - Controle dinâmico de layout (horizontal/vertical) sem reiniciar a aplicação.
    - Rodapé com informações de clima, dólar, bitcoin e data/hora.
    - Controle de threads e timers para atualizações periódicas.
    - Encerramento ordenado da aplicação.
    - Atalho de teclado para fechar a aplicação (`Q`).

- **Tratamento de Erros e Dependências**: Durante o processo de teste, foram identificados e corrigidos erros de sintaxe e dependências ausentes (como `PyQt5` e bibliotecas `libpulse-mainloop-glib0`, `libxcb-xinerama0`, `libxcb-icccm4`).




## 4. Como Executar a Aplicação

Para executar a aplicação modularizada, siga os passos abaixo:

### Pré-requisitos

Certifique-se de ter o Python 3 e o `pip` instalados em seu sistema. A aplicação utiliza a biblioteca PyQt5, que requer algumas dependências de sistema para funcionar corretamente em ambientes Linux baseados em Debian/Ubuntu. Você pode instalá-las com os seguintes comandos:

```bash
sudo apt-get update
sudo apt-get install -y python3-pip libpulse-mainloop-glib0 libxcb-xinerama0 libxcb-icccm4 libxcb-render-util0 libxcb-image0 libxcb-xkb1
```

### Instalação das Dependências Python

Navegue até o diretório raiz do projeto e instale as dependências Python usando `pip`:

```bash
pip3 install PyQt5 requests
```

### Execução

Após instalar as dependências, você pode executar a aplicação a partir do diretório raiz do projeto:

```bash
python3 main.py
```

A aplicação será iniciada em tela cheia. Para fechar, pressione a tecla `Q`.




## 5. Próximos Passos (Refatorações Futuras)

Embora a aplicação tenha sido modularizada, algumas áreas podem ser ainda mais refatoradas para melhorar a clareza e a separação de responsabilidades:

- **Mover Lógica de Download de Mídia para `services/`**: A função `download_new_media` e a lógica de gerenciamento de `self.media_data` em `PublicidadePlayer` poderiam ser extraídas para um módulo em `services/media_manager.py`.
- **Mover Lógica de Informativos para `services/`**: Similarmente, a lógica de processamento e exibição de informativos (`handle_informativos_update`, `show_next_informativo`) poderia ser movida para `services/informativo_manager.py`.
- **Centralizar Criação de Widgets de Rodapé**: A função auxiliar `create_info_widget` e a criação dos widgets de rodapé poderiam ser encapsuladas em um módulo separado em `core/widgets.py` ou `core/footer.py`.
- **Gerenciamento de Layouts**: A lógica dentro de `apply_layout` poderia ser dividida em classes ou funções separadas para cada tipo de layout (horizontal e vertical), tornando o código mais legível e fácil de manter.

## 6. Considerações Finais

A modularização foi realizada com o objetivo de tornar o projeto mais robusto e fácil de expandir. O comportamento original da aplicação foi preservado, garantindo que todas as funcionalidades operem como esperado na nova estrutura.


