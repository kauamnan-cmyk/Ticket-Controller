#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# --- Importações de Bibliotecas ---
import sys
import os
import requests # Para fazer requisições HTTP (buscar a API)
import time     # Para pausas (embora usemos QTimer principalmente)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QSpacerItem
) # Componentes da interface gráfica
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent # Para tocar vídeo/áudio
from PyQt5.QtMultimediaWidgets import QVideoWidget # Widget específico para exibir vídeo
from PyQt5.QtCore import QUrl, Qt, QTimer, QThread, pyqtSignal, QSize # Utilitários, Timers, Threads, Sinais
from PyQt5.QtGui import QPixmap, QKeyEvent # Para exibir imagens e capturar teclas

# --- Constantes Globais ---
# URL da API que fornece a lista de mídias
API_URL = "https://example.com/levamidia/api/get_publicidade.php?id=1" # URL corrigida conforme solicitado
# Diretório onde as mídias baixadas serão salvas (dentro da pasta home do usuário)
MEDIA_DIR = os.path.join(os.path.expanduser("~"), "manus_media")
# Intervalo para verificar a API por atualizações (em milissegundos)
API_CHECK_INTERVAL_MS = 10000  # 10 segundos
# Tempo que cada imagem ficará na tela (em milissegundos)
IMAGE_DISPLAY_TIME_MS = 10000 # 10 segundos

# --- Thread para Verificar a API Periodicamente ---
# Usar uma thread separada evita que a interface gráfica trave durante a consulta da API
class ApiCheckThread(QThread):
    # Sinal emitido quando a playlist é atualizada (envia a nova lista)
    playlist_updated = pyqtSignal(list)
    # Sinal emitido em caso de erro na consulta da API (envia mensagem de erro)
    error_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_media_list = [] # Armazena a lista de mídias atual
        self.running = True          # Flag para controlar a execução da thread

    # Método principal da thread, executado em loop
    def run(self):
        while self.running:
            try:
                # Faz a requisição GET para a API
                response = requests.get(API_URL, timeout=5) # Timeout de 5 segundos
                response.raise_for_status() # Lança exceção se a resposta for erro (4xx ou 5xx)
                new_media_list = response.json() # Converte a resposta JSON em lista Python

                # --- Processamento da Resposta da API (Adaptado) ---
                # Verifica se a resposta é realmente uma lista
                if not isinstance(new_media_list, list):
                    raise ValueError("API response is not a list")

                processed_media_list = [] # Lista para armazenar os itens processados
                # Verifica se a lista não está vazia e se o primeiro item é uma string (URL)
                if new_media_list and isinstance(new_media_list[0], str):
                    print("API retornou uma lista de URLs. Processando...")
                    # Itera sobre as strings (URLs)
                    for url_str in new_media_list:
                        # Verifica se é uma string e começa com http (validação básica)
                        if isinstance(url_str, str) and url_str.startswith("http"):
                             # Cria um dicionário para manter a estrutura interna consistente
                             filename = os.path.basename(QUrl(url_str).path()) # Extrai nome do arquivo da URL
                             processed_media_list.append({"nome": filename, "url": url_str})
                        else:
                             print(f"Skipping invalid URL string: {url_str}")
                # Verifica se a lista não está vazia e se o primeiro item é um dicionário (formato original esperado)
                elif new_media_list and isinstance(new_media_list[0], dict):
                     print("API retornou uma lista de objetos. Processando...")
                     # Itera sobre os dicionários
                     for item in new_media_list:
                         # Verifica se é um dicionário e contém a chave "url"
                         if isinstance(item, dict) and "url" in item:
                             # Garante que a chave "nome" exista, gera se ausente
                             if "nome" not in item:
                                 item["nome"] = os.path.basename(QUrl(item["url"]).path())
                             processed_media_list.append(item)
                         else:
                             print(f"Skipping invalid object item: {item}")
                else:
                    # Caso a lista esteja vazia ou em formato inesperado
                    print("API retornou uma lista vazia ou formato inesperado.")
                    processed_media_list = [] # Garante que seja uma lista vazia

                # Compara a lista processada com a lista atual para ver se houve mudanças
                if self._list_content_changed(self.current_media_list, processed_media_list):
                    print("Playlist alterada, emitindo sinal.")
                    self.current_media_list = processed_media_list # Atualiza a lista atual
                    self.playlist_updated.emit(self.current_media_list) # Emite o sinal com a nova lista
                else:
                    print("Nenhuma mudança na playlist.")
                # --- Fim do Processamento da Resposta ---

            # Tratamento de erros de requisição (rede, timeout, etc.)
            except requests.exceptions.RequestException as e:
                error_msg = f"Falha na requisição da API: {e}"
                print(error_msg)
                self.error_signal.emit(error_msg)
                # Continua rodando com a lista antiga em caso de falha temporária
            # Tratamento de erro se a resposta não for JSON válido ou lista
            except ValueError as e:
                error_msg = f"Erro nos dados da API: {e}"
                print(error_msg)
                self.error_signal.emit(error_msg)
            # Tratamento de outros erros inesperados
            except Exception as e:
                error_msg = f"Erro inesperado na thread da API: {e}"
                print(error_msg)
                self.error_signal.emit(error_msg)

            # Aguarda o intervalo definido antes da próxima verificação
            self.msleep(API_CHECK_INTERVAL_MS)

    # Método auxiliar para comparar duas listas de mídia
    def _list_content_changed(self, list1, list2):
        # Comparação simples baseada no tamanho e nas URLs ordenadas
        if len(list1) != len(list2):
            return True
        # Extrai e ordena as URLs de cada lista para comparação
        urls1 = sorted([item.get("url") for item in list1])
        urls2 = sorted([item.get("url") for item in list2])
        return urls1 != urls2

    # Método para parar a thread
    def stop(self):
        print("Parando a thread da API...")
        self.running = False
        self.wait() # Espera a thread terminar completamente

# --- Janela Principal da Aplicação ---
class PublicidadePlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.playlist = []          # Lista de dicionários representando as mídias a tocar
        self.current_index = -1     # Índice da mídia atual na playlist
        self.media_files = {}       # Dicionário mapeando URL da mídia para caminho local
        self.error_count = 0        # Contador de erros (pode ser usado para exibir status)

        # Cria o diretório de mídias se ele não existir
        if not os.path.exists(MEDIA_DIR):
            print(f"Criando diretório de mídia: {MEDIA_DIR}")
            os.makedirs(MEDIA_DIR)

        # Inicializa os componentes da interface, playback e a thread da API
        self.init_ui()
        self.init_playback()
        self.init_api_check()

    # Configuração da Interface Gráfica (UI)
    def init_ui(self):
        self.setWindowTitle("Manus Publicidade Player")
        self.setStyleSheet("background-color: black; color: white;") # Estilo base
        # Tenta maximizar e depois colocar em tela cheia (melhor compatibilidade)
        self.showMaximized()
        QTimer.singleShot(100, self.showFullScreen) # Aplica tela cheia após um pequeno delay

        # Widget central e layout principal horizontal
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0) # Sem margens externas
        main_layout.setSpacing(0) # Sem espaçamento entre as seções

        # --- Lado Esquerdo (Player de Mídia e Rodapé) ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget) # Layout vertical para mídia e rodapé
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # Container para a mídia (vídeo ou imagem)
        self.media_container = QWidget()
        self.media_layout = QVBoxLayout(self.media_container)
        self.media_layout.setContentsMargins(0, 0, 0, 0)
        self.media_layout.setSpacing(0)

        # Widget para exibir vídeo
        self.video_widget = QVideoWidget()
        # Label para exibir imagem
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter) # Centraliza a imagem
        # Faz a imagem ignorar o tamanho preferido e preencher o espaço
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setBackgroundRole(self.backgroundRole()) # Usa cor de fundo do tema
        self.image_label.setAutoFillBackground(True)

        # Adiciona os widgets de vídeo e imagem ao container (um ficará visível por vez)
        self.media_layout.addWidget(self.video_widget)
        self.media_layout.addWidget(self.image_label)
        self.video_widget.hide() # Começa escondido
        self.image_label.hide()  # Começa escondido

        # Adiciona o container de mídia ao layout esquerdo, ocupando a maior parte (9)
        left_layout.addWidget(self.media_container, 9)

        # --- Rodapé (Footer) --- # Layout modificado conforme solicitação
        footer_widget = QWidget()
        footer_widget.setFixedHeight(220) # Altura definida pelo usuário
        footer_widget.setStyleSheet("background-color: #222; border-top: 1px solid #444;") # Estilo base do rodapé

        # Layout vertical principal para o rodapé (divide em parte superior e inferior)
        footer_main_layout = QVBoxLayout(footer_widget)
        footer_main_layout.setContentsMargins(5, 5, 5, 5) # Pequeno padding interno
        footer_main_layout.setSpacing(5) # Espaço entre as metades superior e inferior

        # --- Metade Superior do Rodapé (Informativo Condomínio) ---
        top_footer_widget = QWidget()
        # Cor de fundo igual ao painel direito e bordas arredondadas
        top_footer_widget.setStyleSheet("background-color: #111; border-radius: 5px;")
        top_footer_layout = QHBoxLayout(top_footer_widget)
        top_footer_layout.setContentsMargins(10, 5, 10, 5) # Padding interno
        self.condo_info_label = QLabel("Informativo Condomínio: Reunião dia 15/06 às 19h (Simulado)")
        self.condo_info_label.setAlignment(Qt.AlignCenter) # Centraliza o texto
        # Estilo do texto (cor, tamanho, negrito, fundo transparente para não cobrir o do widget)
        self.condo_info_label.setStyleSheet("color: #eee; font-size: 16px; font-weight: bold; background-color: transparent;")
        top_footer_layout.addWidget(self.condo_info_label)

        # --- Metade Inferior do Rodapé (Infos Dinâmicas) ---
        bottom_footer_widget = QWidget()
        bottom_footer_widget.setStyleSheet("background-color: transparent;") # Fundo transparente
        bottom_footer_layout = QHBoxLayout(bottom_footer_widget)
        bottom_footer_layout.setContentsMargins(10, 0, 10, 0) # Padding horizontal

        # Cria os labels para as informações dinâmicas
        self.clima_label = QLabel("Clima: 24°C Nublado (Simulado)")
        self.dollar_label = QLabel("USD: R$ 5,25 (Simulado)")
        self.btc_label = QLabel("BTC: $68,500 (Simulado)") # Alterado de Euro para BTC
        self.datetime_label = QLabel("18/07/2024 14:30 (Simulado)") # Data e Hora

        # Aplica um estilo comum aos labels da parte inferior
        label_style = "color: #ccc; font-size: 15px;"
        self.clima_label.setStyleSheet(label_style)
        self.dollar_label.setStyleSheet(label_style)
        self.btc_label.setStyleSheet(label_style)
        self.datetime_label.setStyleSheet(label_style)

        # Adiciona os labels ao layout inferior na ordem correta, com espaçadores (stretch)
        # para criar o efeito "space-around"
        bottom_footer_layout.addStretch(1) # Espaçador inicial
        bottom_footer_layout.addWidget(self.clima_label)
        bottom_footer_layout.addStretch(2) # Espaçador maior entre itens
        bottom_footer_layout.addWidget(self.dollar_label)
        bottom_footer_layout.addStretch(2)
        bottom_footer_layout.addWidget(self.btc_label)
        bottom_footer_layout.addStretch(2)
        bottom_footer_layout.addWidget(self.datetime_label)
        bottom_footer_layout.addStretch(1) # Espaçador final

        # Adiciona as metades superior e inferior ao layout principal do rodapé
        footer_main_layout.addWidget(top_footer_widget)
        footer_main_layout.addWidget(bottom_footer_widget)

        # Adiciona o rodapé completo ao layout esquerdo, ocupando a parte inferior (1)
        left_layout.addWidget(footer_widget, 1)

        # --- Lado Direito (Informações Fixas do Condomínio) ---
        right_widget = QWidget()
        # Cor de fundo e borda esquerda para separar visualmente
        right_widget.setStyleSheet("background-color: #111; border-left: 1px solid #444;")
        right_layout = QVBoxLayout(right_widget)
        self.info_label = QLabel("Informações do Condomínio\n\n- Avisos importantes\n- Eventos\n- Contatos úteis\n\n(Espaço reservado)")
        self.info_label.setAlignment(Qt.AlignTop | Qt.AlignLeft) # Alinha no topo e esquerda
        self.info_label.setStyleSheet("color: #eee; font-size: 16px; padding: 20px;") # Estilo
        self.info_label.setWordWrap(True) # Quebra de linha automática
        right_layout.addWidget(self.info_label)
        right_layout.addStretch() # Empurra o conteúdo para cima

        # --- Adiciona os lados esquerdo e direito ao layout principal ---
        # Define a proporção da largura (8 para esquerda, 2 para direita = 80%/20%)
        main_layout.addWidget(left_widget, 8)
        main_layout.addWidget(right_widget, 2)

    # Inicialização do Player de Mídia
    def init_playback(self):
        self.player = QMediaPlayer(None, QMediaPlayer.VideoSurface) # Cria o player
        self.player.setVideoOutput(self.video_widget) # Associa à saída de vídeo
        self.player.setMuted(True) # Começa sem som, conforme requisito
        # Conecta sinais do player a métodos de tratamento
        self.player.mediaStatusChanged.connect(self.media_status_changed) # Mudança de status (fim, erro)
        self.player.error.connect(self.handle_player_error) # Erro específico do player

        # Timer para controlar a duração da exibição de imagens
        self.playback_timer = QTimer(self)
        self.playback_timer.setSingleShot(True) # Dispara apenas uma vez
        self.playback_timer.timeout.connect(self.play_next) # Chama play_next quando o tempo esgota

    # Inicialização da Thread de Verificação da API
    def init_api_check(self):
        self.api_thread = ApiCheckThread(self) # Cria a instância da thread
        # Conecta os sinais da thread aos métodos correspondentes na janela principal
        self.api_thread.playlist_updated.connect(self.update_playlist)
        self.api_thread.error_signal.connect(self.handle_api_error)
        self.api_thread.start() # Inicia a execução da thread

    # Método chamado quando a thread da API reporta um erro
    def handle_api_error(self, error_message):
        print(f"Erro na API: {error_message}")
        self.error_count += 1
        # Poderia adicionar lógica aqui para mostrar um indicador visual se muitos erros ocorrerem
        pass # Continua com a playlist atual em caso de erro

    # Método chamado quando a thread da API envia uma nova playlist
    def update_playlist(self, new_playlist):
        print("Recebida playlist atualizada da thread da API.")
        self.playlist = new_playlist # Atualiza a playlist local
        self.download_media() # Baixa/verifica as mídias da nova playlist

        # Se nada estiver tocando, inicia a reprodução do início da nova playlist
        if self.player.state() == QMediaPlayer.StoppedState and not self.playback_timer.isActive():
             if not self.playlist:
                 print("Playlist vazia após atualização.")
                 self.stop_playback() # Para tudo se a playlist estiver vazia
             else:
                 print("Playlist atualizada, iniciando reprodução do começo.")
                 self.current_index = -1 # Reseta o índice para começar do 0
                 self.play_next() # Chama o próximo item
        else:
            # Se algo já estava tocando, apenas informa que a playlist foi atualizada
            # A reprodução continuará e incorporará as mudanças no próximo ciclo
            print("Playlist atualizada, a reprodução continuará e incorporará as mudanças.")
            # Opcional: Verifica se o índice atual ainda é válido na nova lista
            if self.current_index >= len(self.playlist):
                print("Índice atual inválido após atualização, reiniciando.")
                self.current_index = -1
                self.play_next() # Reinicia se o item atual foi removido

    # Método para baixar as mídias da playlist atual
    def download_media(self):
        print("Iniciando verificação/download de mídias...")
        required_files = set() # Conjunto para guardar os caminhos locais necessários
        new_media_files = {}   # Dicionário temporário para URL -> caminho local

        # Itera sobre os itens da playlist atual
        for item in self.playlist:
            url = item.get("url") # Pega a URL do item
            if not url:
                continue # Pula se não houver URL

            # Gera o nome do arquivo local a partir da URL
            filename = os.path.basename(QUrl(url).path())
            local_path = os.path.join(MEDIA_DIR, filename)
            required_files.add(local_path) # Adiciona ao conjunto de arquivos necessários
            new_media_files[url] = local_path # Mapeia URL para caminho local

            # Verifica se o arquivo já existe localmente
            if not os.path.exists(local_path):
                print(f"Baixando {url} para {local_path}...")
                try:
                    # Faz o download usando requests em stream para arquivos grandes
                    response = requests.get(url, stream=True, timeout=10)
                    response.raise_for_status() # Verifica erro no download
                    # Salva o conteúdo em blocos
                    with open(local_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"Download concluído: {filename}")
                # Trata erros de download
                except requests.exceptions.RequestException as e:
                    print(f"Falha ao baixar {url}: {e}")
                    # Remove o arquivo do mapeamento se o download falhar
                    if url in new_media_files:
                         del new_media_files[url]
                    if local_path in required_files:
                        required_files.remove(local_path)
                # Trata outros erros ao salvar o arquivo
                except Exception as e:
                    print(f"Erro ao salvar arquivo {local_path}: {e}")
                    if url in new_media_files:
                         del new_media_files[url]
                    if local_path in required_files:
                        required_files.remove(local_path)
            # else:
                # print(f"Arquivo {filename} já existe.")
                # pass

        # --- Limpeza de Arquivos Antigos ---
        # Itera sobre os arquivos existentes no diretório de mídia
        for existing_file in os.listdir(MEDIA_DIR):
            full_path = os.path.join(MEDIA_DIR, existing_file)
            # Se um arquivo local não está na lista de arquivos necessários, remove-o
            if full_path not in required_files:
                print(f"Removendo arquivo antigo: {existing_file}")
                try:
                    os.remove(full_path)
                except OSError as e:
                    print(f"Falha ao remover {full_path}: {e}")

        # Atualiza o dicionário de arquivos de mídia da classe
        self.media_files = new_media_files
        print("Verificação/download de mídias concluído.")

    # Método principal para tocar a próxima mídia da playlist
    def play_next(self):
        self.stop_playback() # Garante que qualquer reprodução anterior seja parada

        # Verifica se a playlist ou os arquivos locais estão vazios
        if not self.playlist or not self.media_files:
            print("Playlist ou arquivos de mídia vazios, aguardando...")
            # Tenta novamente após 5 segundos (API pode atualizar)
            self.playback_timer.start(5000)
            return

        # Avança para o próximo índice (ou volta para 0 se chegar ao fim)
        self.current_index = (self.current_index + 1) % len(self.playlist)
        media_item = self.playlist[self.current_index] # Pega o item da playlist
        url = media_item.get("url") # Pega a URL

        # Verifica se o arquivo local correspondente existe (pode ter falhado o download)
        if url not in self.media_files:
            print(f"Arquivo de mídia para {url} não encontrado localmente, pulando.")
            # Tenta o próximo item imediatamente
            QTimer.singleShot(100, self.play_next)
            return

        local_path = self.media_files[url] # Pega o caminho local
        print(f"Tocando índice {self.current_index}: {local_path}")

        # Verifica a extensão do arquivo para decidir como tocar
        if local_path.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
            # É um vídeo
            self.image_label.hide() # Esconde o label de imagem
            self.video_widget.show() # Mostra o widget de vídeo
            # Define a mídia no player e inicia a reprodução
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(local_path)))
            self.player.play()
            # O fim da reprodução será detectado pelo sinal mediaStatusChanged
        elif local_path.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif")):
            # É uma imagem
            self.video_widget.hide() # Esconde o widget de vídeo
            self.image_label.show()  # Mostra o label de imagem
            pixmap = QPixmap(local_path) # Carrega a imagem
            # Verifica se a imagem foi carregada corretamente
            if pixmap.isNull():
                print(f"Erro ao carregar imagem: {local_path}")
                self.image_label.setText("Erro ao carregar imagem")
                self.playback_timer.start(2000) # Mostra erro brevemente e avança
            else:
                # Redimensiona a imagem para caber no label, mantendo proporção
                scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(scaled_pixmap) # Define a imagem no label
                # Inicia o timer para exibir a imagem pelo tempo definido
                self.playback_timer.start(IMAGE_DISPLAY_TIME_MS)
        else:
            # Tipo de arquivo não suportado
            print(f"Tipo de arquivo não suportado: {local_path}")
            # Pula para o próximo item rapidamente
            self.playback_timer.start(100)

    # Método chamado quando o status do QMediaPlayer muda
    def media_status_changed(self, status):
        # Se o vídeo terminou de tocar
        if status == QMediaPlayer.EndOfMedia:
            print("Vídeo finalizado.")
            self.play_next() # Toca o próximo item
        # Se a mídia for inválida
        elif status == QMediaPlayer.InvalidMedia:
            print("Mídia inválida.")
            self.handle_player_error("Mídia inválida") # Trata como erro
            self.play_next() # Tenta o próximo
        # Outros status (carregado, bufferizando, etc.) podem ser tratados aqui se necessário
        elif status == QMediaPlayer.LoadedMedia:
             pass # Mídia carregada, pronto para tocar

    # Método chamado quando ocorre um erro no QMediaPlayer
    def handle_player_error(self, error):
        # Exibe a mensagem de erro do player
        print(f"Erro no Player: {self.player.errorString()} (Código: {error})")
        # Tenta se recuperar tocando o próximo item após um pequeno delay
        # para evitar loops rápidos em caso de erro persistente
        self.stop_playback()
        QTimer.singleShot(1000, self.play_next) # Espera 1 segundo

    # Método para parar completamente a reprodução atual
    def stop_playback(self):
        # Para o player de vídeo se estiver tocando
        if self.player.state() != QMediaPlayer.StoppedState:
            self.player.stop()
        # Para o timer de imagem se estiver ativo
        if self.playback_timer.isActive():
            self.playback_timer.stop()
        # Esconde ambos os widgets de mídia e limpa o label de imagem
        self.video_widget.hide()
        self.image_label.hide()
        self.image_label.clear()

    # Método chamado quando uma tecla é pressionada
    def keyPressEvent(self, event: QKeyEvent):
        # Se a tecla for 'q' (minúsculo ou maiúsculo)
        if event.key() == Qt.Key_Q:
            print("Tecla Q pressionada, saindo...")
            self.close() # Fecha a aplicação
        else:
            # Passa o evento para o tratamento padrão da classe pai
            super().keyPressEvent(event)

    # Método chamado quando a janela é redimensionada
    def resizeEvent(self, event):
        # Redimensiona a imagem atual (se houver) para se ajustar ao novo tamanho do label
        # --- CORREÇÃO INCLUÍDA ---
        # Verifica se image_label já foi inicializado antes de acessá-lo
        if hasattr(self, "image_label") and self.image_label.pixmap() and not self.image_label.pixmap().isNull():
        # --- FIM DA CORREÇÃO ---
             scaled_pixmap = self.image_label.pixmap().scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
             self.image_label.setPixmap(scaled_pixmap)
        # Chama o método da classe pai para outros tratamentos de redimensionamento
        super().resizeEvent(event)

    # Método chamado quando a janela está prestes a ser fechada
    def closeEvent(self, event):
        print("Fechando a aplicação...")
        self.api_thread.stop() # Para a thread da API
        self.stop_playback()   # Para a reprodução de mídia
        event.accept() # Confirma o fechamento da janela

# --- Execução Principal do Script ---
if __name__ == "__main__":
    # Verifica se está rodando em um ambiente gráfico (necessário para PyQt)
    if "DISPLAY" not in os.environ and "WAYLAND_DISPLAY" not in os.environ:
        print("Erro: Ambiente gráfico não detectado. PyQt requer uma sessão gráfica.")
        print("Certifique-se de rodar a partir do Desktop do Raspberry Pi ou com X forwarding.")
        sys.exit(1)

    # Cria a aplicação Qt
    app = QApplication(sys.argv)

    # Verifica se o backend de multimídia do Qt está funcional
    # (Tenta criar um QMediaPlayer para forçar a verificação)
    try:
        _test_player = QMediaPlayer()
        if _test_player.supportedMimeTypes() == []:
             print("Aviso: Nenhum tipo MIME suportado pelo QMediaPlayer. Verifique os plugins GStreamer.")
        del _test_player
    except Exception as e:
        print(f"Erro ao inicializar QMediaPlayer: {e}")
        print("Verifique se os plugins GStreamer necessários estão instalados.")
        print("No Raspberry Pi OS (Debian), tente:")
        print("sudo apt update")
        print("sudo apt install --reinstall gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav libqt5multimedia5-plugins -y")
        sys.exit(1)

    # Cria e exibe a janela principal do player
    player_window = PublicidadePlayer()
    player_window.show()

    # Inicia o loop de eventos da aplicação Qt
    sys.exit(app.exec_())

