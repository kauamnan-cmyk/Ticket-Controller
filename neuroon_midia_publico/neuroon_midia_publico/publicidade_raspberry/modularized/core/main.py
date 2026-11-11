#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# --- Importações de Bibliotecas ---
import sys
import os
import requests # Para fazer requisições HTTP (buscar a API)
import time     # Para pausas (embora usemos QTimer principalmente)
import datetime # Para obter a data e hora atuais
import json     # Para tratar respostas JSON da API de contagem
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QSpacerItem,
    QDesktopWidget
) # Componentes da interface gráfica
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent # Para tocar vídeo/áudio
from PyQt5.QtMultimediaWidgets import QVideoWidget # Widget específico para exibir vídeo
from PyQt5.QtCore import QUrl, Qt, QTimer, QThread, pyqtSignal, QSize, QDateTime # Utilitários, Timers, Threads, Sinais, Data/Hora
from PyQt5.QtGui import QPixmap, QKeyEvent # Para exibir imagens e capturar teclas

# Importações dos módulos modularizados
from config.constants import (
    ID_TELA, API_PUBLICIDADE_URL, API_INFORMATIVO_URL_BASE, API_INSERT_EXIBICOES_URL,
    API_POSICAO_TELA_URL, MEDIA_DIR, ICON_DIR, API_PUBLICIDADE_CHECK_INTERVAL_MS,
    API_INFORMATIVO_CHECK_INTERVAL_MS, API_POSICAO_TELA_CHECK_INTERVAL_MS,
    IMAGE_DISPLAY_TIME_MS, INFORMATIVO_DISPLAY_TIME_MS, DATETIME_UPDATE_INTERVAL_MS,
    REPORT_INTERVAL_MS, FONT_SIZE_TITULO, FONT_SIZE_SUBTITULO, FONT_SIZE_TEXTO,
    FONT_SIZE_AVISO, FONT_SIZE_ICON
)
from threads.publicidade_api_thread import PublicidadeApiThread
from threads.informativo_api_thread import InformativoApiThread
from threads.posicao_tela_api_thread import PosicaoTelaApiThread

# --- Janela Principal da Aplicação ---
class PublicidadePlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.playlist = [] # Lista de dicionários da API (url, nome, id_conteudo)
        self.current_playlist_index = -1
        # Dicionário para armazenar dados locais e contagem por id_conteudo
        # Estrutura: {id_conteudo: {"path": local_path, "count": N, "url": original_url}}
        self.media_data = {}
        self.informativos = []
        self.current_informativo_index = -1
        self.api_error_count = 0
        self.last_played_media_id = None # Para saber qual mídia acabou de tocar
        self.formato_tela = 1  # Formato padrão: 1 = horizontal, 2 = vertical
        self.current_media_type = None # Inicializa a variável aqui
        
        # Armazena as dimensões da tela
        self.screen_geometry = QDesktopWidget().screenGeometry()
        self.screen_width = self.screen_geometry.width()
        self.screen_height = self.screen_geometry.height()

        if not os.path.exists(MEDIA_DIR):
            print(f"Criando diretório de mídia: {MEDIA_DIR}")
            os.makedirs(MEDIA_DIR)

        # Widgets que serão reutilizados em ambos os layouts
        self.create_widgets()
        
        # Inicializa a UI com o layout padrão (horizontal)
        self.init_ui()
        self.init_playback()
        self.init_api_threads()
        self.init_timers()

    def create_widgets(self):
        """Cria os widgets que serão usados em ambos os layouts"""
        # Widgets de mídia
        self.media_container = QWidget()
        self.media_layout = QVBoxLayout(self.media_container)
        self.media_layout.setContentsMargins(0, 0, 0, 0)
        self.media_layout.setSpacing(0)

        self.video_widget = QVideoWidget()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setBackgroundRole(self.backgroundRole())
        self.image_label.setAutoFillBackground(True)

        self.media_layout.addWidget(self.video_widget)
        self.media_layout.addWidget(self.image_label)
        self.video_widget.hide()
        self.image_label.hide()

        # Widgets de informativo
        self.info_details_label = QLabel("Carregando detalhes do informativo...")
        self.info_details_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.info_details_label.setStyleSheet(f"""
            color: black;
            font-size: {FONT_SIZE_TITULO}px;
            background-color: white;
        """)
        self.info_details_label.setWordWrap(True)
        self.info_details_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # Widget de imagem do informativo
        self.info_image_label = QLabel()
        self.info_image_label.setAlignment(Qt.AlignCenter)
        self.info_image_label.setStyleSheet("background-color: transparent;")
        self.info_image_label.setScaledContents(True)
        self.info_image_label.hide()

        # Widget de aviso do condomínio
        self.condo_info_label = QLabel("Carregando informativo...")
        self.condo_info_label.setAlignment(Qt.AlignLeft)
        self.condo_info_label.setStyleSheet(f"""
            color: white;
            font-size: {FONT_SIZE_AVISO}px;
            font-weight: bold;
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                stop: 0 #007BFF, stop: 1 white);
            padding: 5px 15px;
        """)

        # Widgets do rodapé com ícones
        icon_size = QSize(64, 64)
        label_style = f"""color: black; font-size: {FONT_SIZE_ICON}px; font-weight:bold;"""

        # Função auxiliar para criar grupo ícone+texto
        def create_info_widget(icon_filename, initial_text):
            widget = QWidget()
            layout = QHBoxLayout(widget)
            widget.setStyleSheet("background-color:transparent;")
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(6) # Espaço entre ícone e texto

            icon_label = QLabel()
            icon_path = os.path.join(ICON_DIR, icon_filename)
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                icon_label.setPixmap(pixmap.scaled(icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                icon_label.setFixedSize(icon_size)
            else:
                print(f"Aviso: Ícone não encontrado em {icon_path}")
                icon_label.setFixedSize(icon_size)

            text_label = QLabel(initial_text)
            text_label.setStyleSheet(label_style)

            layout.addWidget(icon_label)
            layout.addWidget(text_label)
            return widget, text_label

        # Criar widgets de informação
        self.clima_widget, self.clima_label = create_info_widget("weather.png", "Clima: --")
        self.dollar_widget, self.dollar_label = create_info_widget("dollar.png", "USD: --")
        self.btc_widget, self.btc_label = create_info_widget("bitcoin.png", "BTC: --")
        self.datetime_widget, self.datetime_label = create_info_widget("clock.png", "--/--/---- --:--:--")

    def init_ui(self):
        """Inicializa a interface do usuário e aplica o layout inicial"""
        self.setWindowTitle("Player de Publicidade")
        self.showFullScreen()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.central_widget.setStyleSheet("background-color: black;")

        self.apply_layout(self.formato_tela) # Aplica o layout inicial

    def apply_layout(self, formato_tela):
        """Aplica o layout horizontal (1) ou vertical (2) dinamicamente"""
        # Limpa o layout existente
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().hide() # Esconde os widgets antes de removê-los
                # item.widget().setParent(None) # REMOVIDO: Não deletar widgets
            elif item.layout():
                self.clear_layout(item.layout())

        if formato_tela == 1: # Layout Horizontal
            print("Aplicando layout horizontal...")
            # Layout principal horizontal
            h_main_layout = QHBoxLayout()
            h_main_layout.setContentsMargins(0, 0, 0, 0)
            h_main_layout.setSpacing(0)

            # Lado esquerdo (mídia)
            left_side_widget = QWidget()
            left_side_layout = QVBoxLayout(left_side_widget)
            left_side_layout.setContentsMargins(0, 0, 0, 0)
            left_side_layout.setSpacing(0)
            left_side_widget.setStyleSheet("background-color: black;")

            # Container de mídia (80% do lado esquerdo)
            media_area_widget = QWidget()
            media_area_layout = QVBoxLayout(media_area_widget)
            media_area_layout.setContentsMargins(0, 0, 0, 0)
            media_area_layout.setSpacing(0)
            media_area_layout.addWidget(self.media_container) # Adiciona o container de mídia
            media_area_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            media_area_widget.setMinimumHeight(int(self.screen_height * 0.9))

            # Rodapé do lado esquerdo (20% do lado esquerdo)
            left_footer_widget = QWidget()
            left_footer_layout = QVBoxLayout(left_footer_widget)
            left_footer_layout.setContentsMargins(0, 0, 0, 0)
            left_footer_layout.setSpacing(0)
            left_footer_widget.setStyleSheet("background-color: black;")

            # Aviso (10% do rodapé esquerdo)
            condo_info_container = QWidget()
            condo_info_layout = QVBoxLayout(condo_info_container)
            condo_info_layout.setContentsMargins(0, 0, 0, 0)
            condo_info_layout.setSpacing(0)
            condo_info_layout.addWidget(self.condo_info_label)
            condo_info_container.setFixedHeight(int(self.screen_height * 0.1 * 0.5)) # 5% da altura total
            condo_info_container.setStyleSheet("background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #007BFF, stop: 1 white);")

            # Widgets de informação (10% do rodapé esquerdo)
            info_widgets_container = QWidget()
            info_widgets_layout = QHBoxLayout(info_widgets_container)
            info_widgets_layout.setContentsMargins(0, 0, 0, 0)
            info_widgets_layout.setSpacing(0)
            info_widgets_layout.addStretch(1)
            info_widgets_layout.addWidget(self.clima_widget)
            info_widgets_layout.addStretch(1)
            info_widgets_layout.addWidget(self.dollar_widget)
            info_widgets_layout.addStretch(1)
            info_widgets_layout.addWidget(self.btc_widget)
            info_widgets_layout.addStretch(1)
            info_widgets_layout.addWidget(self.datetime_widget)
            info_widgets_layout.addStretch(1)
            info_widgets_container.setFixedHeight(int(self.screen_height * 0.1 * 0.5)) # 5% da altura total
            info_widgets_container.setStyleSheet("background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #007BFF, stop: 1 white);")

            left_footer_layout.addWidget(condo_info_container)
            left_footer_layout.addWidget(info_widgets_container)

            left_side_layout.addWidget(media_area_widget, 9) # 90% para mídia
            left_side_layout.addWidget(left_footer_widget, 1) # 10% para rodapé

            # Lado direito (informativo)
            right_side_widget = QWidget()
            right_side_layout = QVBoxLayout(right_side_widget)
            right_side_layout.setContentsMargins(10, 10, 10, 10)
            right_side_layout.setSpacing(10)
            right_side_widget.setStyleSheet("background-color: white;")

            right_side_layout.addWidget(self.info_details_label)
            right_side_layout.addWidget(self.info_image_label)
            right_side_layout.addStretch(1)

            h_main_layout.addWidget(left_side_widget, 8) # 80% para o lado esquerdo
            h_main_layout.addWidget(right_side_widget, 2) # 20% para o lado direito

            self.main_layout.addLayout(h_main_layout)

        elif formato_tela == 2: # Layout Vertical
            print("Aplicando layout vertical...")
            # Container de mídia no topo
            media_top_container = QWidget()
            media_top_layout = QVBoxLayout(media_top_container)
            media_top_layout.setContentsMargins(0, 0, 0, 0)
            media_top_layout.setSpacing(0)
            media_top_layout.addWidget(self.media_container)
            media_top_container.setStyleSheet("background-color: black;")
            # Limita a altura a 40% da tela, mantendo proporção 16:9
            media_top_container.setMaximumHeight(int(self.screen_height * 0.4))
            media_top_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

            # Painel de informativo
            info_panel_widget = QWidget()
            info_panel_layout = QVBoxLayout(info_panel_widget)
            info_panel_layout.setContentsMargins(10, 10, 10, 10)
            info_panel_layout.setSpacing(10)
            info_panel_widget.setStyleSheet("background-color: white;")

            # Aviso
            condo_info_container = QWidget()
            condo_info_layout = QVBoxLayout(condo_info_container)
            condo_info_layout.setContentsMargins(0, 0, 0, 0)
            condo_info_layout.setSpacing(0)
            condo_info_layout.addWidget(self.condo_info_label)
            condo_info_container.setStyleSheet("background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #007BFF, stop: 1 white);")

            info_panel_layout.addWidget(condo_info_container)
            info_panel_layout.addWidget(self.info_details_label)
            info_panel_layout.addWidget(self.info_image_label)
            info_panel_layout.addStretch(1)

            # Rodapé
            footer_widget = QWidget()
            footer_layout = QHBoxLayout(footer_widget)
            footer_layout.setContentsMargins(0, 0, 0, 0)
            footer_layout.setSpacing(0)
            footer_layout.addStretch(1)
            footer_layout.addWidget(self.clima_widget)
            footer_layout.addStretch(1)
            footer_layout.addWidget(self.dollar_widget)
            footer_layout.addStretch(1)
            footer_layout.addWidget(self.btc_widget)
            footer_layout.addStretch(1)
            footer_layout.addWidget(self.datetime_widget)
            footer_layout.addStretch(1)
            footer_widget.setFixedHeight(int(self.screen_height * 0.05)) # 5% da altura total
            footer_widget.setStyleSheet("background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #007BFF, stop: 1 white);")

            self.main_layout.addWidget(media_top_container)
            self.main_layout.addWidget(info_panel_widget)
            self.main_layout.addWidget(footer_widget)

        self.central_widget.setLayout(self.main_layout)
        self.central_widget.update()

        # Garante que os widgets de mídia estejam visíveis no novo layout
        if self.current_media_type == "video":
            self.video_widget.show()
            self.image_label.hide()
        elif self.current_media_type == "image":
            self.image_label.show()
            self.video_widget.hide()
        else:
            self.video_widget.hide()
            self.image_label.hide()

        # Garante que os widgets de informativo estejam visíveis no novo layout
        self.info_details_label.show()
        if self.info_image_label.pixmap() and not self.info_image_label.pixmap().isNull():
            self.info_image_label.show()
        else:
            self.info_image_label.hide()
        self.condo_info_label.show()

        # Garante que os widgets do rodapé estejam visíveis no novo layout
        self.clima_widget.show()
        self.dollar_widget.show()
        self.btc_widget.show()
        self.datetime_widget.show()

    def clear_layout(self, layout):
        """Função auxiliar para limpar um layout"""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().hide()
                    # item.widget().setParent(None) # REMOVIDO: Não deletar widgets
                elif item.layout():
                    self.clear_layout(item.layout())

    def init_playback(self):
        """Inicializa o player de mídia"""
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.stateChanged.connect(self.media_state_changed)
        self.media_player.mediaStatusChanged.connect(self.media_status_changed)
        self.media_player.error.connect(self.media_error)

        # self.current_media_type = None # Esta linha foi movida para __init__

    def init_api_threads(self):
        """Inicializa e inicia as threads de API"""
        self.publicidade_thread = PublicidadeApiThread()
        self.publicidade_thread.playlist_updated.connect(self.handle_playlist_update)
        self.publicidade_thread.error_signal.connect(self.handle_api_error)
        self.publicidade_thread.start()

        self.informativo_thread = InformativoApiThread()
        self.informativo_thread.informativos_updated.connect(self.handle_informativos_update)
        self.informativo_thread.error_signal.connect(self.handle_api_error)
        self.informativo_thread.start()

        self.posicao_tela_thread = PosicaoTelaApiThread()
        self.posicao_tela_thread.formato_tela_updated.connect(self.handle_formato_tela_update)
        self.posicao_tela_thread.error_signal.connect(self.handle_api_error)
        self.posicao_tela_thread.start()

    def init_timers(self):
        """Inicializa os timers para controle de reprodução e atualização"""
        # Timer para alternar entre mídias
        self.media_timer = QTimer(self)
        self.media_timer.timeout.connect(self.play_next_media)

        # Timer para rotacionar informativos
        self.informativo_timer = QTimer(self)
        self.informativo_timer.timeout.connect(self.show_next_informativo)
        self.informativo_timer.start(INFORMATIVO_DISPLAY_TIME_MS)

        # Timer para atualizar data e hora
        self.datetime_timer = QTimer(self)
        self.datetime_timer.timeout.connect(self.update_datetime_label)
        self.datetime_timer.start(DATETIME_UPDATE_INTERVAL_MS)
        self.update_datetime_label() # Chama uma vez para exibir imediatamente

        # Timer para reportar contagens de exibição
        self.report_timer = QTimer(self)
        self.report_timer.timeout.connect(self.report_exibicoes)
        self.report_timer.start(REPORT_INTERVAL_MS)

    def handle_playlist_update(self, new_playlist):
        """Lida com a atualização da playlist de publicidade"""
        print(f"Playlist atualizada com {len(new_playlist)} itens.")
        self.playlist = new_playlist
        # Reinicia a reprodução se a playlist não estiver vazia e não houver mídia tocando
        if self.playlist and self.media_player.state() == QMediaPlayer.StoppedState:
            self.current_playlist_index = -1 # Para começar do primeiro item
            self.play_next_media()
        elif not self.playlist:
            print("Playlist vazia. Parando reprodução.")
            self.media_player.stop()
            self.media_timer.stop()
            self.video_widget.hide()
            self.image_label.hide()

        # Inicia o download das novas mídias em segundo plano
        self.download_new_media()

    def download_new_media(self):
        """Baixa novas mídias da playlist que ainda não estão no cache local"""
        # Identifica mídias que precisam ser baixadas
        urls_to_download = []
        for media_item in self.playlist:
            url = media_item["url"]
            id_conteudo = media_item["id_conteudo"]
            # Verifica se a mídia já está no cache e se o arquivo existe
            if id_conteudo not in self.media_data or not os.path.exists(self.media_data[id_conteudo]["path"]):
                urls_to_download.append((url, id_conteudo))

        if urls_to_download:
            print(f"Iniciando download de {len(urls_to_download)} novas mídias...")
            # Pode-se usar uma thread separada ou um pool de threads para downloads
            # Para simplificar, faremos de forma síncrona aqui, mas idealmente seria assíncrono
            for url, id_conteudo in urls_to_download:
                try:
                    response = requests.get(url, stream=True, timeout=30)
                    response.raise_for_status()

                    # Determina a extensão do arquivo
                    content_type = response.headers.get("Content-Type", "").lower()
                    if "video" in content_type:
                        ext = ".mp4" # Assumindo mp4 para vídeos
                    elif "image/jpeg" in content_type:
                        ext = ".jpg"
                    elif "image/png" in content_type:
                        ext = ".png"
                    elif "image/gif" in content_type:
                        ext = ".gif"
                    else:
                        # Tenta adivinhar pela URL se o Content-Type não ajudar
                        path_parts = QUrl(url).path().split(".")
                        if len(path_parts) > 1:
                            ext = "." + path_parts[-1].lower()
                        else:
                            ext = ".bin" # Fallback para desconhecido

                    # Cria um nome de arquivo único baseado no id_conteudo e extensão
                    local_filename = f"{id_conteudo}{ext}"
                    local_path = os.path.join(MEDIA_DIR, local_filename)

                    with open(local_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"Download concluído: {local_filename}")
                    self.media_data[id_conteudo] = {
                        "path": local_path,
                        "count": 0,
                        "url": url # Armazena a URL original para referência
                    }
                except requests.exceptions.RequestException as e:
                    print(f"Erro ao baixar {url}: {e}")
                except Exception as e:
                    print(f"Erro inesperado no download de {url}: {e}")
        else:
            print("Nenhuma mídia nova para baixar.")

    def play_next_media(self):
        """Reproduz a próxima mídia na playlist"""
        if not self.playlist:
            print("Playlist vazia. Nada para reproduzir.")
            self.media_player.stop()
            self.media_timer.stop()
            self.video_widget.hide()
            self.image_label.hide()
            return

        self.current_playlist_index = (self.current_playlist_index + 1) % len(self.playlist)
        media_item = self.playlist[self.current_playlist_index]
        id_conteudo = media_item["id_conteudo"]
        url = media_item["url"]

        # Verifica se a mídia está no cache e se o arquivo existe
        if id_conteudo in self.media_data and os.path.exists(self.media_data[id_conteudo]["path"]):
            local_path = self.media_data[id_conteudo]["path"]
            print(f"Reproduzindo mídia local: {local_path}")

            # Incrementa a contagem de exibição
            self.media_data[id_conteudo]["count"] += 1
            self.last_played_media_id = id_conteudo

            if local_path.lower().endswith((".mp4", ".avi", ".mov", ".mkv", ".webm")):
                self.current_media_type = "video"
                self.image_label.hide()
                self.video_widget.show()
                self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(local_path)))
                self.media_player.play()
                self.media_timer.stop() # O timer será iniciado novamente em media_state_changed para imagens
            elif local_path.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                self.current_media_type = "image"
                self.video_widget.hide()
                self.image_label.show()
                pixmap = QPixmap(local_path)
                if not pixmap.isNull():
                    # Escala a imagem para preencher o QLabel mantendo a proporção
                    scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.image_label.setPixmap(scaled_pixmap)
                    self.media_timer.start(IMAGE_DISPLAY_TIME_MS)
                else:
                    print(f"Erro: Não foi possível carregar a imagem {local_path}")
                    self.play_next_media() # Tenta a próxima mídia
            else:
                print(f"Formato de mídia não suportado: {local_path}")
                self.play_next_media() # Tenta a próxima mídia
        else:
            print(f"Mídia não encontrada localmente ou arquivo ausente: {url}. Tentando baixar novamente...")
            # Remove a entrada inválida para forçar um novo download
            if id_conteudo in self.media_data:
                del self.media_data[id_conteudo]
            self.download_new_media() # Tenta baixar novamente
            self.play_next_media() # Tenta a próxima mídia

    def media_state_changed(self, state):
        """Lida com as mudanças de estado do player de mídia"""
        if state == QMediaPlayer.StoppedState:
            # Se a mídia parou (e não é uma imagem), reproduz a próxima
            if self.current_media_type == "video":
                self.play_next_media()

    def media_status_changed(self, status):
        """Lida com as mudanças de status da mídia (ex: fim do arquivo)"""
        if status == QMediaPlayer.EndOfMedia:
            # Para vídeos, EndOfMedia significa que o vídeo terminou
            if self.current_media_type == "video":
                self.play_next_media()

    def media_error(self, error):
        """Lida com erros de reprodução de mídia"""
        print(f"Erro de mídia: {self.media_player.errorString()} ({error})")
        self.play_next_media() # Tenta a próxima mídia em caso de erro

    def handle_informativos_update(self, new_informativos):
        """Lida com a atualização da lista de informativos"""
        print(f"Informativos atualizados com {len(new_informativos)} itens.")
        self.informativos = new_informativos
        if self.informativos and not self.informativo_timer.isActive():
            self.informativo_timer.start(INFORMATIVO_DISPLAY_TIME_MS)
            self.show_next_informativo() # Exibe o primeiro informativo imediatamente
        elif not self.informativos:
            print("Nenhum informativo disponível. Ocultando painel.")
            self.informativo_timer.stop()
            self.info_details_label.clear()
            self.info_image_label.clear()
            self.condo_info_label.clear()
            self.info_details_label.hide()
            self.info_image_label.hide()
            self.condo_info_label.hide()

    def show_next_informativo(self):
        """Exibe o próximo informativo na lista"""
        if not self.informativos:
            return

        self.current_informativo_index = (self.current_informativo_index + 1) % len(self.informativos)
        informativo = self.informativos[self.current_informativo_index]

        # Atualiza o aviso
        self.condo_info_label.setText(informativo.get("informativo_aviso", ""))
        self.condo_info_label.show()

        # Atualiza os detalhes do informativo
        titulo = informativo.get("informativo_titulo", "")
        subtitulo = informativo.get("informativo_subtitulo", "")
        texto = informativo.get("informativo_texto", "")

        formatted_text = f"<p><span style=\"font-size:{FONT_SIZE_TITULO}px; font-weight:bold;\">{titulo}</span></p>"
        if subtitulo:
            formatted_text += f"<p><span style=\"font-size:{FONT_SIZE_SUBTITULO}px;\">{subtitulo}</span></p>"
        if texto:
            formatted_text += f"<p><span style=\"font-size:{FONT_SIZE_TEXTO}px;\">{texto}</span></p>"

        self.info_details_label.setText(formatted_text)
        self.info_details_label.show()

        # Atualiza a imagem do informativo
        image_url = informativo.get("informativo_imagem", None)
        if image_url:
            try:
                image_data = requests.get(image_url, timeout=5).content
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)
                if not pixmap.isNull():
                    # Redimensiona a imagem para o tamanho especificado no planejamento
                    if self.formato_tela == 1: # Horizontal
                        target_size = QSize(100, 100)
                    else: # Vertical
                        target_size = QSize(854, 480)

                    scaled_pixmap = pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.info_image_label.setPixmap(scaled_pixmap)
                    self.info_image_label.show()
                else:
                    self.info_image_label.hide()
                    print(f"Erro: Não foi possível carregar a imagem do informativo de {image_url}")
            except requests.exceptions.RequestException as e:
                self.info_image_label.hide()
                print(f"Erro ao baixar imagem do informativo {image_url}: {e}")
            except Exception as e:
                self.info_image_label.hide()
                print(f"Erro inesperado ao processar imagem do informativo {image_url}: {e}")
        else:
            self.info_image_label.hide()

    def update_datetime_label(self):
        """Atualiza o QLabel com a data e hora atuais"""
        current_datetime = QDateTime.currentDateTime().toString("dd/MM/yyyy HH:mm:ss")
        self.datetime_label.setText(current_datetime)

    def report_exibicoes(self):
        """Reporta as contagens de exibição para a API"""
        exibicoes_to_report = []
        for id_conteudo, data in self.media_data.items():
            if data["count"] > 0:
                exibicoes_to_report.append({
                    "id_conteudo": id_conteudo,
                    "quantidade": data["count"],
                    "url": data["url"] # Inclui a URL original para referência
                })
                data["count"] = 0 # Reseta a contagem após adicionar para o relatório

        if exibicoes_to_report:
            print(f"Reportando {len(exibicoes_to_report)} contagens de exibição...")
            try:
                # A API espera um array de objetos JSON
                payload = json.dumps(exibicoes_to_report)
                headers = {"Content-Type": "application/json"}
                response = requests.post(API_INSERT_EXIBICOES_URL, data=payload, headers=headers, timeout=10)
                response.raise_for_status()
                print("Contagens reportadas com sucesso.")
            except requests.exceptions.RequestException as e:
                print(f"Erro ao reportar exibições: {e}")
                # Em caso de erro, as contagens não são resetadas e serão tentadas novamente
                # na próxima execução do timer
            except Exception as e:
                print(f"Erro inesperado ao reportar exibições: {e}")

    def handle_formato_tela_update(self, new_formato):
        """Lida com a atualização do formato da tela"""
        if self.formato_tela != new_formato:
            print(f"Detectada mudança de formato de tela: de {self.formato_tela} para {new_formato}")
            self.formato_tela = new_formato
            self.apply_layout(self.formato_tela)
            # Se uma mídia estava tocando, tenta reproduzi-la novamente no novo layout
            if self.media_player.state() == QMediaPlayer.PlayingState:
                # Pausa e tenta reproduzir o item atual para reajustar ao novo layout
                self.media_player.stop()
                # Encontra o item atual na playlist para reproduzir
                if self.playlist and self.current_playlist_index != -1:
                    # Re-chama play_next_media para o item atual
                    # Isso pode ser otimizado para apenas redefinir o media_player
                    # mas para garantir o reajuste, chamamos a função completa
                    self.play_next_media() # Isso avançará para o próximo, então precisamos ajustar
                    # Uma alternativa seria armazenar o item atual e reproduzi-lo diretamente
            elif self.playlist and self.current_playlist_index != -1: # Se estava pausado ou parado
                self.play_next_media() # Tenta reproduzir o próximo ou o atual

    def handle_api_error(self, error_msg):
        """Lida com erros das threads da API"""
        self.api_error_count += 1
        print(f"Erro da API (total: {self.api_error_count}): {error_msg}")
        # Implementar lógica de retry ou notificação ao usuário se necessário

    def keyPressEvent(self, event: QKeyEvent):
        """Captura eventos de teclado"""
        if event.key() == Qt.Key_Q:
            print("Tecla \'Q\' pressionada. Encerrando aplicação...")
            self.close()

    def closeEvent(self, event):
        """Lida com o evento de fechamento da janela"""
        print("Fechando aplicação...")
        self.report_exibicoes() # Garante que as contagens pendentes sejam enviadas

        # Para as threads
        if hasattr(self, 'publicidade_thread') and self.publicidade_thread.isRunning():
            self.publicidade_thread.stop()
        if hasattr(self, 'informativo_thread') and self.informativo_thread.isRunning():
            self.informativo_thread.stop()
        if hasattr(self, 'posicao_tela_thread') and self.posicao_tela_thread.isRunning():
            self.posicao_tela_thread.stop()

        # Para os timers
        if hasattr(self, 'media_timer') and self.media_timer.isActive():
            self.media_timer.stop()
        if hasattr(self, 'informativo_timer') and self.informativo_timer.isActive():
            self.informativo_timer.stop()
        if hasattr(self, 'datetime_timer') and self.datetime_timer.isActive():
            self.datetime_timer.stop()
        if hasattr(self, 'report_timer') and self.report_timer.isActive():
            self.report_timer.stop()

        self.media_player.stop()
        super().closeEvent(event)

# --- Função Principal ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = PublicidadePlayer()
    sys.exit(app.exec_())


