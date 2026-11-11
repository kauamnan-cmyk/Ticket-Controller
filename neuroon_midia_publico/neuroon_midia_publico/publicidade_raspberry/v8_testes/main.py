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

# --- Constantes Globais ---
ID_TELA = 1 # ID da tela a ser passado para as APIs

# URL da API que fornece a lista de mídias (publicidade)
API_PUBLICIDADE_URL = f"https://example.com/levamidia/api/get_publicidade.php?id={ID_TELA}"
# URL da API que fornece os informativos
API_INFORMATIVO_URL_BASE = "https://example.com/levamidia/api/get_informativo.php"
# URL da API para inserir contagem de exibições
API_INSERT_EXIBICOES_URL = "https://example.com/levamidia/api/insert_exibicoes_basico.php"
# URL da API para verificar o formato da tela
API_POSICAO_TELA_URL = f"https://example.com/levamidia/api/get_posicao_tela.php?id_tela={ID_TELA}"

# --- Caminho da pasta de mídias e ícones ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(SCRIPT_DIR, "midias")
ICON_DIR = os.path.join(SCRIPT_DIR, "icons") # Caminho para ícones

# --- Intervalos e Tempos ---
API_PUBLICIDADE_CHECK_INTERVAL_MS = 10000  # 10 segundos
API_INFORMATIVO_CHECK_INTERVAL_MS = 300000 # 5 minutos
API_POSICAO_TELA_CHECK_INTERVAL_MS = 60000 # 1 minutos
IMAGE_DISPLAY_TIME_MS = 10000 # 10 segundos
INFORMATIVO_DISPLAY_TIME_MS = 120000 # 2 minutos
DATETIME_UPDATE_INTERVAL_MS = 1000 # 1 segundo
# Intervalo para reportar contagem de exibições: 1 minuto
REPORT_INTERVAL_MS = 60000 # 1 * 60 * 1000 ms

# --- Tamanhos de Fonte em Pixels ---
FONT_SIZE_TITULO = 34
FONT_SIZE_SUBTITULO = 24
FONT_SIZE_TEXTO = 15
FONT_SIZE_AVISO = 24 # Tamanho da fonte para o informativo_aviso

# --- Thread para Verificar a API de Publicidade Periodicamente ---
class PublicidadeApiThread(QThread):
    playlist_updated = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_media_list_signature = set() # Usado para detectar mudanças reais
        self.running = True

    def run(self):
        while self.running:
            try:
                response = requests.get(API_PUBLICIDADE_URL, timeout=10)
                response.raise_for_status()
                new_media_list_raw = response.json()

                if not isinstance(new_media_list_raw, list):
                    raise ValueError("API de Publicidade: resposta não é uma lista")

                processed_media_list = []
                new_signature = set()
                # Processa a lista garantindo que temos id_conteudo e url/url_midia
                for item in new_media_list_raw:
                    if isinstance(item, dict) and "id_conteudo" in item:
                        # Tenta obter a URL, priorizando 'url_midia' e depois 'url'
                        url = item.get("url_midia") or item.get("url")

                        if url: # Se encontrou uma URL válida
                            # Tenta converter id_conteudo para int, se falhar, pula o item
                            try:
                                id_conteudo = int(item["id_conteudo"])
                            except (ValueError, TypeError):
                                print(f"Item de publicidade inválido descartado (id_conteudo não numérico): {item}")
                                continue

                            nome = item.get("nome", os.path.basename(QUrl(url).path()))
                            processed_media_list.append({
                                "nome": nome,
                                "url": url, # Armazena sempre como 'url' internamente
                                "id_conteudo": id_conteudo
                            })
                            new_signature.add((url, id_conteudo))
                        else:
                            print(f"Item de publicidade inválido descartado (sem url ou url_midia): {item}")
                    else:
                        print(f"Item de publicidade inválido descartado (sem id_conteudo ou não é dicionário): {item}")


                # Compara assinaturas para detectar mudança real no conteúdo
                if new_signature != self.current_media_list_signature:
                    print("Playlist de publicidade alterada.")
                    self.current_media_list_signature = new_signature
                    self.playlist_updated.emit(processed_media_list)
                # else: # Descomente para debug
                #     print("Playlist de publicidade sem alterações.")

            except requests.exceptions.RequestException as e:
                error_msg = f"Falha na requisição da API de Publicidade: {e}"
                print(error_msg)
                self.error_signal.emit(error_msg)
            except ValueError as e:
                error_msg = f"Erro nos dados da API de Publicidade: {e}"
                print(error_msg)
                self.error_signal.emit(error_msg)
            except Exception as e:
                error_msg = f"Erro inesperado na thread da API de Publicidade: {e}"
                print(error_msg)
                self.error_signal.emit(error_msg)

            self.msleep(API_PUBLICIDADE_CHECK_INTERVAL_MS)

    def stop(self):
        print("Parando a thread da API de Publicidade...")
        self.running = False
        self.wait()

# --- Thread para Verificar a API de Informativos Periodicamente ---
class InformativoApiThread(QThread):
    informativos_updated = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True

    def run(self):
        while self.running:
            try:
                now = datetime.datetime.now()
                data_str = now.strftime("%Y-%m-%dT%H:%M:%S")
                params = {
                    'id': ID_TELA,
                    'data': data_str
                }
                # print(f"Buscando informativos: {API_INFORMATIVO_URL_BASE} com params: {params}")

                response = requests.get(API_INFORMATIVO_URL_BASE, params=params, timeout=10)
                response.raise_for_status()
                new_informativos = response.json()

                if not isinstance(new_informativos, list):
                    raise ValueError("API de Informativo: resposta não é uma lista")

                valid_informativos = []
                for item in new_informativos:
                    if isinstance(item, dict) and all(k in item for k in ["informativo_aviso", "informativo_titulo", "informativo_subtitulo", "informativo_texto"]):
                        valid_informativos.append(item)
                    else:
                        print(f"Informativo inválido descartado: {item}")

                # print(f"Recebidos {len(valid_informativos)} informativos válidos.")
                self.informativos_updated.emit(valid_informativos)

            except requests.exceptions.RequestException as e:
                error_msg = f"Falha na requisição da API de Informativo: {e}"
                print(error_msg)
                self.error_signal.emit(error_msg)
            except ValueError as e:
                error_msg = f"Erro nos dados da API de Informativo: {e}"
                print(error_msg)
                self.error_signal.emit(error_msg)
            except Exception as e:
                error_msg = f"Erro inesperado na thread da API de Informativo: {e}"
                print(error_msg)
                self.error_signal.emit(error_msg)

            self.msleep(API_INFORMATIVO_CHECK_INTERVAL_MS)

    def stop(self):
        print("Parando a thread da API de Informativo...")
        self.running = False
        self.wait()

# --- Thread para Verificar o Formato da Tela Periodicamente ---
class PosicaoTelaApiThread(QThread):
    formato_tela_updated = pyqtSignal(int)
    error_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.current_formato = None  # Armazena o formato atual para detectar mudanças

    def run(self):
        while self.running:
            try:
                response = requests.get(API_POSICAO_TELA_URL, timeout=10)
                response.raise_for_status()
                data = response.json()

                if isinstance(data, dict) and "formato_tela" in data:
                    try:
                        formato_tela = int(data["formato_tela"])
                        # Só emite o sinal se o formato mudou
                        if formato_tela != self.current_formato:
                            print(f"Formato de tela alterado: {formato_tela}")
                            self.current_formato = formato_tela
                            self.formato_tela_updated.emit(formato_tela)
                    except (ValueError, TypeError):
                        error_msg = f"Formato de tela inválido: {data['formato_tela']}"
                        print(error_msg)
                        self.error_signal.emit(error_msg)
                else:
                    error_msg = "API de Posição Tela: resposta não contém formato_tela"
                    print(error_msg)
                    self.error_signal.emit(error_msg)

            except requests.exceptions.RequestException as e:
                error_msg = f"Falha na requisição da API de Posição Tela: {e}"
                print(error_msg)
                self.error_signal.emit(error_msg)
            except ValueError as e:
                error_msg = f"Erro nos dados da API de Posição Tela: {e}"
                print(error_msg)
                self.error_signal.emit(error_msg)
            except Exception as e:
                error_msg = f"Erro inesperado na thread da API de Posição Tela: {e}"
                print(error_msg)
                self.error_signal.emit(error_msg)

            self.msleep(API_POSICAO_TELA_CHECK_INTERVAL_MS)

    def stop(self):
        print("Parando a thread da API de Posição Tela...")
        self.running = False
        self.wait()

# --- Janela Principal da Aplicação ---
class PublicidadePlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.playlist = [] # Lista de dicionários da API (url, nome, id_conteudo)
        self.current_playlist_index = -1
        # Dicionário para armazenar dados locais e contagem por id_conteudo
        # Estrutura: {id_conteudo: {'path': local_path, 'count': N, 'url': original_url}}
        self.media_data = {}
        self.informativos = []
        self.current_informativo_index = -1
        self.api_error_count = 0
        self.last_played_media_id = None # Para saber qual mídia acabou de tocar
        self.formato_tela = 1  # Formato padrão: 1 = horizontal, 2 = vertical
        
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
            padding-right: 30px;
            border-bottom: 2px solid #007BFF;
        """)
        self.info_details_label.setWordWrap(True)
        self.info_details_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # Label da imagem de informativo
        self.info_image_label = QLabel()
        self.info_image_label.setAlignment(Qt.AlignCenter)
        self.info_image_label.setStyleSheet("background-color: white;")
        self.info_image_label.hide()

        # Widget de aviso do condomínio
        self.condo_info_label = QLabel("Carregando informativo...")
        self.condo_info_label.setAlignment(Qt.AlignCenter)
        self.condo_info_label.setStyleSheet(f"""
            color: black;
            font-size: {FONT_SIZE_AVISO}px;
            font-weight: bold;
            background-color: transparent;
        """)

        # Widgets do rodapé com ícones
        icon_size = QSize(64, 64)
        label_style = f"color: black; font-size: {FONT_SIZE_TEXTO}px;"

        def create_info_widget(icon_filename, initial_text):
            widget = QWidget()
            layout = QHBoxLayout(widget)
            widget.setStyleSheet("background-color: transparent;")
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(6)

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

        self.clima_widget, self.clima_label = create_info_widget("weather.png", "Clima: --")
        self.dollar_widget, self.dollar_label = create_info_widget("dollar.png", "USD: --")
        self.btc_widget, self.btc_label = create_info_widget("bitcoin.png", "BTC: --")
        self.datetime_widget, self.datetime_label = create_info_widget("clock.png", "--/--/---- --:--:--")

    def init_ui(self):
        """Inicializa a interface com base no formato atual"""
        self.setWindowTitle("NeuroOn Publicidade Player")
        self.setStyleSheet("background-color: black; color: white;")
        
        # Limpa qualquer widget central existente
        if self.centralWidget():
            old_widget = self.centralWidget()
            self.setCentralWidget(None)
            old_widget.deleteLater()

        # Cria um novo widget central
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Aplica o layout apropriado com base no formato da tela
        if self.formato_tela == 1:
            self.apply_horizontal_layout(central_widget)
        else:
            self.apply_vertical_layout(central_widget)
        
        # Exibe em tela cheia
        self.showMaximized()
        QTimer.singleShot(100, self.showFullScreen)

        pixmap = QPixmap("icons/dollar.png")
        self.info_image_label.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.info_image_label.show()


    def apply_horizontal_layout(self, central_widget):
        """Aplica o layout horizontal (formato_tela = 1)"""
        print("Aplicando layout horizontal")
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Lado Esquerdo
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # Adiciona o container de mídia
        left_layout.addWidget(self.media_container, 9)

        # Rodapé
        footer_widget = QWidget()
        footer_widget.setFixedHeight(216)
        footer_widget.setStyleSheet("background-color: #222;")
        footer_main_layout = QVBoxLayout(footer_widget)
        footer_main_layout.setContentsMargins(0, 0, 0, 0)
        footer_main_layout.setSpacing(5)

        # Rodapé Superior
        top_footer_widget = QWidget()
        top_footer_widget.setStyleSheet("background-color: transparent;")
        top_footer_layout = QHBoxLayout(top_footer_widget)
        top_footer_layout.setContentsMargins(0, 0, 0, 0)
        top_footer_layout.addWidget(self.condo_info_label)

        # Rodapé Inferior
        bottom_footer_widget = QWidget()
        bottom_footer_widget.setStyleSheet("background-color: #111;")
        bottom_footer_layout = QHBoxLayout(bottom_footer_widget)
        bottom_footer_layout.setContentsMargins(20, 5, 20, 5)
        bottom_footer_layout.setSpacing(15)

        # Adiciona os widgets de informação com espaçamento
        bottom_footer_layout.addStretch(1)
        bottom_footer_layout.addWidget(self.clima_widget, 0, Qt.AlignCenter)
        bottom_footer_layout.addStretch(1)
        bottom_footer_layout.addWidget(self.dollar_widget, 0, Qt.AlignCenter)
        bottom_footer_layout.addStretch(1)
        bottom_footer_layout.addWidget(self.btc_widget, 0, Qt.AlignCenter)
        bottom_footer_layout.addStretch(1)
        bottom_footer_layout.addWidget(self.datetime_widget, 0, Qt.AlignCenter)
        bottom_footer_layout.addStretch(1)

        footer_main_layout.addWidget(top_footer_widget)
        footer_main_layout.addWidget(bottom_footer_widget)
        left_layout.addWidget(footer_widget, 1)

        # Lado Direito
        right_widget = QWidget()
        right_widget.setStyleSheet("background-color: #111; padding: 20px;")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        right_layout.addWidget(self.info_details_label)

        # Adiciona a imagem do informativo (100x100)
        self.info_image_label.setFixedSize(100, 100)
        right_layout.addWidget(self.info_image_label, 0, Qt.AlignCenter)

        # Adiciona os widgets principais ao layout
        main_layout.addWidget(left_widget, 8)
        main_layout.addWidget(right_widget, 2)


    def apply_vertical_layout(self, central_widget):
        """Aplica o layout vertical (formato_tela = 2) mantendo a tela fisicamente na horizontal"""
        print("Aplicando layout vertical (simulado)")
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Área de vídeo no topo (mantendo proporção 16:9)
        video_height = int(self.screen_width * 9/16)
        max_video_height = int(self.screen_height * 0.4)
        video_height = min(video_height, max_video_height)

        self.media_container.setFixedHeight(video_height)
        main_layout.addWidget(self.media_container)

        # Área central para informativos
        info_widget = QWidget()
        info_widget.setStyleSheet("background-color: white; padding: 20px;")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(20, 20, 20, 20)
        info_layout.setSpacing(15)

        # Título do informativo (aviso)
        info_header = QWidget()
        info_header_layout = QHBoxLayout(info_header)
        info_header_layout.setContentsMargins(0, 0, 0, 0)
        info_header_layout.addWidget(self.condo_info_label)

        # Detalhes do informativo
        info_layout.addWidget(info_header)
        info_layout.addWidget(self.info_details_label)

        # Adiciona a imagem do informativo (400x400)
        self.info_image_label.setFixedSize(400, 400)
        info_layout.addWidget(self.info_image_label, 0, Qt.AlignCenter)

        # Calcula espaço disponível
        footer_height = int(self.screen_height * 0.05)
        info_height = self.screen_height - video_height - footer_height
        info_widget.setMinimumHeight(info_height)

        main_layout.addWidget(info_widget, 1)

        # Rodapé
        footer_widget = QWidget()
        footer_widget.setFixedHeight(footer_height)
        footer_widget.setStyleSheet("background-color: #222;")
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(20, 5, 20, 5)
        footer_layout.setSpacing(15)

        footer_layout.addStretch(1)
        footer_layout.addWidget(self.clima_widget, 0, Qt.AlignCenter)
        footer_layout.addStretch(1)
        footer_layout.addWidget(self.dollar_widget, 0, Qt.AlignCenter)
        footer_layout.addStretch(1)
        footer_layout.addWidget(self.btc_widget, 0, Qt.AlignCenter)
        footer_layout.addStretch(1)
        footer_layout.addWidget(self.datetime_widget, 0, Qt.AlignCenter)
        footer_layout.addStretch(1)

        main_layout.addWidget(footer_widget)


    def init_playback(self):
        self.player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.player.setVideoOutput(self.video_widget)
        self.player.setMuted(True)
        self.player.mediaStatusChanged.connect(self.media_status_changed)
        self.player.error.connect(self.handle_player_error)

        self.playback_timer = QTimer(self)
        self.playback_timer.setSingleShot(True)
        self.playback_timer.timeout.connect(self.finish_current_media)

    def init_api_threads(self):
        self.publicidade_api_thread = PublicidadeApiThread(self)
        self.publicidade_api_thread.playlist_updated.connect(self.update_playlist_publicidade)
        self.publicidade_api_thread.error_signal.connect(self.handle_api_error)
        self.publicidade_api_thread.start()

        self.informativo_api_thread = InformativoApiThread(self)
        self.informativo_api_thread.informativos_updated.connect(self.update_informativos)
        self.informativo_api_thread.error_signal.connect(self.handle_api_error)
        self.informativo_api_thread.start()
        
        # Thread para verificar o formato da tela
        self.posicao_tela_api_thread = PosicaoTelaApiThread(self)
        self.posicao_tela_api_thread.formato_tela_updated.connect(self.update_formato_tela)
        self.posicao_tela_api_thread.error_signal.connect(self.handle_api_error)
        self.posicao_tela_api_thread.start()

    def init_timers(self):
        self.informativo_rotation_timer = QTimer(self)
        self.informativo_rotation_timer.timeout.connect(self.display_next_informativo)

        self.datetime_timer = QTimer(self)
        self.datetime_timer.timeout.connect(self.update_datetime_label)
        self.datetime_timer.start(DATETIME_UPDATE_INTERVAL_MS)
        self.update_datetime_label()

        # Timer para reportar contagem
        self.report_timer = QTimer(self)
        self.report_timer.timeout.connect(self.report_counts)
        self.report_timer.start(REPORT_INTERVAL_MS)

    def update_formato_tela(self, formato_tela):
        """Atualiza o formato da tela e recria a interface"""
        if formato_tela in [1, 2]:  # Apenas formatos válidos
            if self.formato_tela != formato_tela:
                self.formato_tela = formato_tela
                print(f"Alterando para formato de tela: {formato_tela}")
                
                # Salva o estado atual da reprodução
                current_media_id = self.last_played_media_id
                was_playing_video = self.video_widget.isVisible()
                
                # Pausa a reprodução atual
                if self.player.state() == QMediaPlayer.PlayingState:
                    self.player.pause()
                
                # Recria a interface com o novo layout
                self.init_ui()
                
                # Retoma a reprodução
                if current_media_id is not None:
                    if was_playing_video:
                        self.play_video(self.media_data[current_media_id]['path'])
                    else:
                        self.show_image(self.media_data[current_media_id]['path'])
        else:
            print(f"Formato de tela inválido ignorado: {formato_tela}")

    def handle_api_error(self, error_message):
        print(f"Erro de API: {error_message}")
        self.api_error_count += 1

    def update_playlist_publicidade(self, new_playlist):
        print("Recebida playlist de publicidade atualizada.")
        self.playlist = new_playlist
        # Atualiza self.media_data com base na nova playlist
        # Mantém contagens existentes, adiciona novas mídias com count 0
        current_ids = set(self.media_data.keys())
        new_ids = set(item['id_conteudo'] for item in new_playlist)

        # Remove mídias que não estão mais na playlist
        ids_to_remove = current_ids - new_ids
        for media_id in ids_to_remove:
            if media_id in self.media_data:
                 # Tenta enviar contagem final antes de remover
                 if self.media_data[media_id]['count'] > 0:
                    print(f"Mídia {media_id} removida da playlist. Enviando contagem final: {self.media_data[media_id]['count']}")
                    self.send_count_to_api(media_id, self.media_data[media_id]['count'])
                 del self.media_data[media_id]

        # Verifica/baixa as mídias da nova playlist
        print("Verificando/baixando mídias de publicidade...")
        for item in new_playlist:
            id_conteudo = item['id_conteudo']
            url = item['url']
            
            # Se é uma mídia nova, inicializa com count 0
            if id_conteudo not in self.media_data:
                self.media_data[id_conteudo] = {'url': url, 'path': None, 'count': 0}
            
            # Verifica se o arquivo já existe localmente
            filename = os.path.basename(QUrl(url).path())
            local_path = os.path.join(MEDIA_DIR, filename)
            
            if not os.path.exists(local_path):
                try:
                    print(f"Baixando mídia: {url}")
                    response = requests.get(url, stream=True, timeout=30)
                    response.raise_for_status()
                    
                    with open(local_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    print(f"Mídia baixada com sucesso: {local_path}")
                except Exception as e:
                    print(f"Erro ao baixar mídia {url}: {e}")
                    continue
            
            # Atualiza o caminho local
            self.media_data[id_conteudo]['path'] = local_path
        
        print("Verificação/download de mídias de publicidade concluído.")
        
        # Se não estava reproduzindo nada, inicia a reprodução
        if self.current_playlist_index == -1:
            self.current_playlist_index = 0
            self.play_next_media()

    def update_informativos(self, new_informativos):
        if new_informativos:
            print(f"Recebidos {len(new_informativos)} informativos para o ciclo.")
            self.informativos = new_informativos
            
            # Reinicia o índice e o timer
            self.current_informativo_index = -1
            self.informativo_rotation_timer.stop()
            
            # Exibe o primeiro informativo
            self.display_next_informativo()
        else:
            print("Nenhum informativo recebido.")
            self.condo_info_label.setText("Sem informativos disponíveis")
            self.info_details_label.setText("Sem informativos disponíveis")

    def display_next_informativo(self):
        if not self.informativos:
            return
        
        # Avança para o próximo informativo (com loop)
        self.current_informativo_index = (self.current_informativo_index + 1) % len(self.informativos)
        informativo = self.informativos[self.current_informativo_index]
        
        print(f"Exibindo informativo {self.current_informativo_index + 1}/{len(self.informativos)} por {INFORMATIVO_DISPLAY_TIME_MS/1000}s")
        
        # Atualiza os labels
        self.condo_info_label.setText(f"<h2>{informativo['informativo_aviso']}</h2>")
                
        # Formata o texto detalhado
        details_text = f"<h1>{informativo['informativo_titulo']}</h1>"
        details_text += f"<h2>{informativo['informativo_subtitulo']}</h2>"
        details_text += f"<p>{informativo['informativo_texto']}</p>"
        self.info_details_label.setText(details_text)
        
        # Configura o timer para o próximo informativo
        self.informativo_rotation_timer.start(INFORMATIVO_DISPLAY_TIME_MS)

    def update_datetime_label(self):
        now = QDateTime.currentDateTime()
        formatted_datetime = now.toString("dd/MM/yyyy HH:mm:ss")
        self.datetime_label.setText(formatted_datetime)

    def play_next_media(self):
        if not self.playlist:
            print("Playlist vazia. Aguardando atualização...")
            return
        
        # Avança para o próximo item (com loop)
        self.current_playlist_index = (self.current_playlist_index + 1) % len(self.playlist)
        item = self.playlist[self.current_playlist_index]
        id_conteudo = item['id_conteudo']
        
        if id_conteudo in self.media_data and self.media_data[id_conteudo]['path']:
            local_path = self.media_data[id_conteudo]['path']
            self.last_played_media_id = id_conteudo  # Armazena o ID da mídia atual
            
            # Verifica se é vídeo ou imagem
            if local_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                self.play_video(local_path)
            elif local_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                self.show_image(local_path)
            else:
                print(f"Formato de arquivo não suportado: {local_path}")
                self.play_next_media()  # Pula para o próximo
        else:
            print(f"Mídia não encontrada localmente: {item['url']}")
            self.play_next_media()  # Pula para o próximo

    def play_video(self, video_path):
        print(f"Reproduzindo vídeo: {video_path}")
        self.image_label.hide()
        self.video_widget.show()
        
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(video_path)))
        self.player.play()

    def show_image(self, image_path):
        print(f"Exibindo imagem: {image_path}")
        self.video_widget.hide()
        
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.image_label.setPixmap(pixmap)
            self.image_label.show()
            
            # Configura o timer para avançar após o tempo definido
            self.playback_timer.start(IMAGE_DISPLAY_TIME_MS)
        else:
            print(f"Erro ao carregar imagem: {image_path}")
            self.play_next_media()  # Pula para o próximo

    def media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.finish_current_media()

    def finish_current_media(self):
        # Incrementa o contador da mídia que acabou de ser exibida
        if self.last_played_media_id is not None and self.last_played_media_id in self.media_data:
            self.media_data[self.last_played_media_id]['count'] += 1
            print(f"Incrementado contador para mídia ID {self.last_played_media_id}. Nova contagem: {self.media_data[self.last_played_media_id]['count']}")
        
        # Avança para a próxima mídia
        self.play_next_media()

    def report_counts(self):
        """Envia as contagens acumuladas para a API"""
        print("Verificando contagens para envio...")
        for media_id, data in list(self.media_data.items()):
            if data['count'] > 0:
                success = self.send_count_to_api(media_id, data['count'])
                if success:
                    # Zera o contador apenas se o envio foi bem-sucedido
                    self.media_data[media_id]['count'] = 0
                    print(f"Contador zerado para mídia ID {media_id} após envio bem-sucedido")

    def send_count_to_api(self, id_conteudo, count):
        """Envia uma contagem específica para a API e retorna True se bem-sucedido"""
        try:
            params = {
                'exibicao_qtd': count,
                'id_tela': ID_TELA,
                'id_conteudo': id_conteudo
            }
            print(f"Enviando contagem para API: {params}")
            
            response = requests.get(API_INSERT_EXIBICOES_URL, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if isinstance(result, dict) and result.get('success') == "Exibição atualizada com sucesso":
                print(f"Contagem enviada com sucesso para mídia ID {id_conteudo}")
                return True
            else:
                print(f"Resposta inesperada da API de contagem: {result}")
                return False
                
        except Exception as e:
            print(f"Erro ao enviar contagem para mídia ID {id_conteudo}: {e}")
            return False

    def handle_player_error(self, error):
        print(f"Erro no player: {error}")
        self.play_next_media()  # Tenta a próxima mídia

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q:
            print("Tecla Q pressionada. Encerrando aplicação...")
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        print("Encerrando aplicação...")
        
        # Tenta enviar contagens finais
        print("Enviando contagens finais...")
        for media_id, data in list(self.media_data.items()):
            if data['count'] > 0:
                self.send_count_to_api(media_id, data['count'])
        
        # Para as threads
        if hasattr(self, 'publicidade_api_thread'):
            self.publicidade_api_thread.stop()
        if hasattr(self, 'informativo_api_thread'):
            self.informativo_api_thread.stop()
        if hasattr(self, 'posicao_tela_api_thread'):
            self.posicao_tela_api_thread.stop()
            
        # Para o player
        if hasattr(self, 'player'):
            self.player.stop()
            
        # Aceita o evento de fechamento
        event.accept()

# --- Ponto de Entrada da Aplicação ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = PublicidadePlayer()
    sys.exit(app.exec_())
