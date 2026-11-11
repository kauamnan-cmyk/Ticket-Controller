#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# --- Importações de Bibliotecas ---
import sys
import os
import requests # Para fazer requisições HTTP (buscar a API)
import time     # Para pausas (embora usemos QTimer principalmente)
import datetime # Para obter a data e hora atuais
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QSpacerItem
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

# --- Caminho da pasta de mídias ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(SCRIPT_DIR, "midias")

# --- Intervalos e Tempos (MODIFICADOS) ---
API_PUBLICIDADE_CHECK_INTERVAL_MS = 10000  # 10 segundos
# Intervalo para verificar a API de informativos: 5 minutos
API_INFORMATIVO_CHECK_INTERVAL_MS = 300000 # 5 * 60 * 1000 ms
# Tempo que cada imagem de publicidade ficará na tela
IMAGE_DISPLAY_TIME_MS = 10000 # 10 segundos
# Tempo que cada informativo ficará na tela: 2 minutos
INFORMATIVO_DISPLAY_TIME_MS = 120000 # 2 * 60 * 1000 ms
# Intervalo para atualizar o relógio
DATETIME_UPDATE_INTERVAL_MS = 1000 # 1 segundo

# --- Thread para Verificar a API de Publicidade Periodicamente ---
class PublicidadeApiThread(QThread):
    playlist_updated = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_media_list = []
        self.running = True

    def run(self):
        while self.running:
            try:
                response = requests.get(API_PUBLICIDADE_URL, timeout=10)
                response.raise_for_status()
                new_media_list = response.json()

                if not isinstance(new_media_list, list):
                    raise ValueError("API de Publicidade: resposta não é uma lista")

                processed_media_list = []
                if new_media_list and isinstance(new_media_list[0], str):
                    for url_str in new_media_list:
                        if isinstance(url_str, str) and url_str.startswith("http"):
                             filename = os.path.basename(QUrl(url_str).path())
                             processed_media_list.append({"nome": filename, "url": url_str})
                elif new_media_list and isinstance(new_media_list[0], dict):
                    for item in new_media_list:
                        if isinstance(item, dict) and "url" in item:
                            if "nome" not in item:
                                item["nome"] = os.path.basename(QUrl(item["url"]).path())
                            processed_media_list.append(item)
                else:
                    processed_media_list = []

                if self._list_content_changed(self.current_media_list, processed_media_list):
                    print("Playlist de publicidade alterada.")
                    self.current_media_list = processed_media_list
                    self.playlist_updated.emit(self.current_media_list)

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

    def _list_content_changed(self, list1, list2):
        if len(list1) != len(list2):
            return True
        urls1 = sorted([item.get("url") for item in list1])
        urls2 = sorted([item.get("url") for item in list2])
        return urls1 != urls2

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
                print(f"Buscando informativos: {API_INFORMATIVO_URL_BASE} com params: {params}")

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

                print(f"Recebidos {len(valid_informativos)} informativos válidos.")
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

            # Espera 5 minutos para a próxima verificação (MODIFICADO)
            self.msleep(API_INFORMATIVO_CHECK_INTERVAL_MS)

    def stop(self):
        print("Parando a thread da API de Informativo...")
        self.running = False
        self.wait()

# --- Janela Principal da Aplicação ---
class PublicidadePlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.playlist = []
        self.current_index = -1
        self.media_files = {}
        self.informativos = []
        self.current_informativo_index = -1
        self.api_error_count = 0

        if not os.path.exists(MEDIA_DIR):
            print(f"Criando diretório de mídia: {MEDIA_DIR}")
            os.makedirs(MEDIA_DIR)

        self.init_ui()
        self.init_playback()
        self.init_api_threads()
        self.init_timers()

    def init_ui(self):
        self.setWindowTitle("Manus Publicidade Player")
        self.setStyleSheet("background-color: black; color: white;")
        self.showMaximized()
        QTimer.singleShot(100, self.showFullScreen)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Lado Esquerdo
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

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

        left_layout.addWidget(self.media_container, 9)

        # Rodapé
        footer_widget = QWidget()
        footer_widget.setFixedHeight(220)
        footer_widget.setStyleSheet("background-color: #222;")
        footer_main_layout = QVBoxLayout(footer_widget)
        footer_main_layout.setContentsMargins(5, 5, 5, 5)
        footer_main_layout.setSpacing(5)

        top_footer_widget = QWidget()
        top_footer_widget.setStyleSheet("background-color: #111; border-radius: 5px;")
        top_footer_layout = QHBoxLayout(top_footer_widget)
        top_footer_layout.setContentsMargins(10, 5, 10, 5)
        self.condo_info_label = QLabel("Carregando informativo...")
        self.condo_info_label.setAlignment(Qt.AlignCenter)
        self.condo_info_label.setStyleSheet("color: #eee; font-size: 16px; font-weight: bold; background-color: transparent;")
        top_footer_layout.addWidget(self.condo_info_label)

        bottom_footer_widget = QWidget()
        bottom_footer_widget.setStyleSheet("background-color: transparent;")
        bottom_footer_layout = QHBoxLayout(bottom_footer_widget)
        bottom_footer_layout.setContentsMargins(10, 0, 10, 0)

        self.clima_label = QLabel("Clima: --")
        self.dollar_label = QLabel("USD: --")
        self.btc_label = QLabel("BTC: --")
        self.datetime_label = QLabel("--/--/---- --:--:--")

        label_style = "color: #ccc; font-size: 15px;"
        self.clima_label.setStyleSheet(label_style)
        self.dollar_label.setStyleSheet(label_style)
        self.btc_label.setStyleSheet(label_style)
        self.datetime_label.setStyleSheet(label_style)

        bottom_footer_layout.addStretch(1)
        bottom_footer_layout.addWidget(self.clima_label)
        bottom_footer_layout.addStretch(2)
        bottom_footer_layout.addWidget(self.dollar_label)
        bottom_footer_layout.addStretch(2)
        bottom_footer_layout.addWidget(self.btc_label)
        bottom_footer_layout.addStretch(2)
        bottom_footer_layout.addWidget(self.datetime_label)
        bottom_footer_layout.addStretch(1)

        footer_main_layout.addWidget(top_footer_widget)
        footer_main_layout.addWidget(bottom_footer_widget)
        left_layout.addWidget(footer_widget, 1)

        # Lado Direito
        right_widget = QWidget()
        right_widget.setStyleSheet("background-color: #111; border: 1px solid #444;")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(15, 15, 15, 15)
        self.info_details_label = QLabel("Carregando detalhes do informativo...")
        self.info_details_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.info_details_label.setStyleSheet("color: #eee; font-size: 16px;")
        self.info_details_label.setWordWrap(True)
        right_layout.addWidget(self.info_details_label)
        right_layout.addStretch()

        main_layout.addWidget(left_widget, 8)
        main_layout.addWidget(right_widget, 2)

    def init_playback(self):
        self.player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.player.setVideoOutput(self.video_widget)
        self.player.setMuted(True)
        self.player.mediaStatusChanged.connect(self.media_status_changed)
        self.player.error.connect(self.handle_player_error)

        self.playback_timer = QTimer(self)
        self.playback_timer.setSingleShot(True)
        self.playback_timer.timeout.connect(self.play_next_publicidade)

    def init_api_threads(self):
        self.publicidade_api_thread = PublicidadeApiThread(self)
        self.publicidade_api_thread.playlist_updated.connect(self.update_playlist_publicidade)
        self.publicidade_api_thread.error_signal.connect(self.handle_api_error)
        self.publicidade_api_thread.start()

        self.informativo_api_thread = InformativoApiThread(self)
        self.informativo_api_thread.informativos_updated.connect(self.update_informativos)
        self.informativo_api_thread.error_signal.connect(self.handle_api_error)
        self.informativo_api_thread.start()

    def init_timers(self):
        # Timer para rotação dos informativos (MODIFICADO)
        self.informativo_rotation_timer = QTimer(self)
        # Não é mais single shot, vai disparar repetidamente no intervalo fixo
        # self.informativo_rotation_timer.setSingleShot(True)
        self.informativo_rotation_timer.timeout.connect(self.display_next_informativo)
        # O timer será iniciado em update_informativos ou display_next_informativo

        # Timer para atualizar o relógio no rodapé
        self.datetime_timer = QTimer(self)
        self.datetime_timer.timeout.connect(self.update_datetime_label)
        self.datetime_timer.start(DATETIME_UPDATE_INTERVAL_MS)
        self.update_datetime_label()

    def handle_api_error(self, error_message):
        print(f"Erro de API: {error_message}")
        self.api_error_count += 1

    def update_playlist_publicidade(self, new_playlist):
        print("Recebida playlist de publicidade atualizada.")
        self.playlist = new_playlist
        self.download_media()

        if self.player.state() == QMediaPlayer.StoppedState and not self.playback_timer.isActive():
             if not self.playlist:
                 print("Playlist de publicidade vazia após atualização.")
                 self.stop_playback()
             else:
                 print("Iniciando reprodução da publicidade.")
                 self.current_index = -1
                 self.play_next_publicidade()
        else:
            print("Playlist de publicidade atualizada, reprodução continuará.")
            if self.current_index >= len(self.playlist):
                self.current_index = -1
                self.play_next_publicidade()

    def update_informativos(self, new_informativos):
        print(f"Recebidos {len(new_informativos)} informativos para o ciclo.")
        # Para o timer antigo se estiver rodando
        if self.informativo_rotation_timer.isActive():
            self.informativo_rotation_timer.stop()

        self.informativos = new_informativos
        self.current_informativo_index = -1 # Reseta para começar do primeiro

        # Inicia o ciclo de exibição imediatamente se houver informativos
        if self.informativos:
            self.display_next_informativo()
        else:
            # Limpa os campos se não houver informativos
            self.condo_info_label.setText("Sem informativos no momento.")
            self.info_details_label.setText("")

    # Lógica de Exibição dos Informativos (MODIFICADA)
    def display_next_informativo(self):
        # Para o timer caso ele estivesse rodando (segurança)
        if self.informativo_rotation_timer.isActive():
            self.informativo_rotation_timer.stop()

        if not self.informativos:
            print("Ciclo de informativos: Lista vazia.")
            # Não reinicia o timer se não há o que exibir
            return

        # Avança para o próximo índice circularmente
        self.current_informativo_index = (self.current_informativo_index + 1) % len(self.informativos)
        informativo = self.informativos[self.current_informativo_index]

        print(f"Exibindo informativo {self.current_informativo_index + 1}/{len(self.informativos)} por {INFORMATIVO_DISPLAY_TIME_MS / 1000:.0f}s")

        # Atualiza os labels da interface
        self.condo_info_label.setText(informativo.get("informativo_aviso", "Aviso indisponível"))

        titulo = informativo.get("informativo_titulo", "")
        subtitulo = informativo.get("informativo_subtitulo", "")
        texto = informativo.get("informativo_texto", "")
        details_text = f"<b>{titulo}</b><br/>"
        if subtitulo:
            details_text += f"<i>{subtitulo}</i><br/><br/>"
        else:
            details_text += "<br/>"
        details_text += texto.replace("\n", "<br/>")
        self.info_details_label.setText(details_text)

        # Agenda o timer para chamar esta função novamente após o tempo FIXO
        self.informativo_rotation_timer.start(INFORMATIVO_DISPLAY_TIME_MS)

    def download_media(self):
        print("Verificando/baixando mídias de publicidade...")
        required_files = set()
        new_media_files = {}

        for item in self.playlist:
            url = item.get("url")
            if not url:
                continue

            filename = os.path.basename(QUrl(url).path())
            local_path = os.path.join(MEDIA_DIR, filename)
            required_files.add(local_path)
            new_media_files[url] = local_path

            if not os.path.exists(local_path):
                print(f"Baixando {url} para {local_path}...")
                try:
                    response = requests.get(url, stream=True, timeout=15)
                    response.raise_for_status()
                    with open(local_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"Download concluído: {filename}")
                except requests.exceptions.RequestException as e:
                    print(f"Falha ao baixar {url}: {e}")
                    if url in new_media_files: del new_media_files[url]
                    if local_path in required_files: required_files.remove(local_path)
                except Exception as e:
                    print(f"Erro ao salvar arquivo {local_path}: {e}")
                    if url in new_media_files: del new_media_files[url]
                    if local_path in required_files: required_files.remove(local_path)

        try:
            if os.path.exists(MEDIA_DIR):
                for existing_file in os.listdir(MEDIA_DIR):
                    full_path = os.path.join(MEDIA_DIR, existing_file)
                    if full_path not in required_files:
                        print(f"Removendo arquivo antigo: {existing_file}")
                        try:
                            os.remove(full_path)
                        except OSError as e:
                            print(f"Falha ao remover {full_path}: {e}")
            else:
                print(f"Diretório de mídia não encontrado para limpeza: {MEDIA_DIR}")
        except Exception as e:
            print(f"Erro durante a limpeza de arquivos antigos: {e}")

        self.media_files = new_media_files
        print("Verificação/download de mídias de publicidade concluído.")

    def play_next_publicidade(self):
        self.stop_playback()

        if not self.playlist or not self.media_files:
            self.playback_timer.start(5000)
            return

        self.current_index = (self.current_index + 1) % len(self.playlist)
        media_item = self.playlist[self.current_index]
        url = media_item.get("url")

        if url not in self.media_files:
            print(f"Arquivo de publicidade para {url} não encontrado, pulando.")
            QTimer.singleShot(100, self.play_next_publicidade)
            return

        local_path = self.media_files[url]

        if local_path.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
            self.image_label.hide()
            self.video_widget.show()
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(local_path)))
            self.player.play()
        elif local_path.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif")):
            self.video_widget.hide()
            self.image_label.show()
            pixmap = QPixmap(local_path)
            if pixmap.isNull():
                print(f"Erro ao carregar imagem: {local_path}")
                self.image_label.setText("Erro ao carregar imagem")
                self.playback_timer.start(2000)
            else:
                label_size = self.image_label.size()
                if label_size.isEmpty() or not self.image_label.isVisible():
                    label_size = self.media_container.size()
                    if label_size.isEmpty(): label_size = QSize(640, 480)

                scaled_pixmap = pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(scaled_pixmap)
                self.playback_timer.start(IMAGE_DISPLAY_TIME_MS)
        else:
            print(f"Tipo de arquivo de publicidade não suportado: {local_path}")
            self.playback_timer.start(100)

    def media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.play_next_publicidade()
        elif status == QMediaPlayer.InvalidMedia:
            print("Mídia de publicidade inválida.")
            self.handle_player_error("Mídia inválida")
            self.play_next_publicidade()

    def handle_player_error(self, error):
        print(f"Erro no Player: {self.player.errorString()} (Código: {error})")
        self.stop_playback()
        QTimer.singleShot(1000, self.play_next_publicidade)

    def stop_playback(self):
        if self.player.state() != QMediaPlayer.StoppedState:
            self.player.stop()
        if self.playback_timer.isActive():
            self.playback_timer.stop()
        self.video_widget.hide()
        self.image_label.hide()
        self.image_label.clear()

    def update_datetime_label(self):
        now = QDateTime.currentDateTime()
        self.datetime_label.setText(now.toString("dd/MM/yyyy HH:mm:ss"))

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Q:
            print("Tecla Q pressionada, saindo...")
            self.close()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        if hasattr(self, "image_label") and self.image_label.pixmap() and not self.image_label.pixmap().isNull():
             try:
                 label_size = self.image_label.size()
                 if not label_size.isEmpty() and self.image_label.isVisible():
                     scaled_pixmap = self.image_label.pixmap().scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                     self.image_label.setPixmap(scaled_pixmap)
             except Exception as e:
                 print(f"Erro ao redimensionar imagem no resizeEvent: {e}")
        super().resizeEvent(event)

    def closeEvent(self, event):
        print("Fechando a aplicação...")
        if hasattr(self, 'datetime_timer') and self.datetime_timer.isActive(): self.datetime_timer.stop()
        if hasattr(self, 'informativo_rotation_timer') and self.informativo_rotation_timer.isActive(): self.informativo_rotation_timer.stop()
        if hasattr(self, 'publicidade_api_thread'): self.publicidade_api_thread.stop()
        if hasattr(self, 'informativo_api_thread'): self.informativo_api_thread.stop()
        self.stop_playback()
        event.accept()

if __name__ == "__main__":
    if "DISPLAY" not in os.environ and "WAYLAND_DISPLAY" not in os.environ:
        print("Erro: Ambiente gráfico não detectado.")
        sys.exit(1)

    app = QApplication(sys.argv)

    try:
        _test_player = QMediaPlayer()
        if not _test_player.supportedMimeTypes():
            print("Aviso: Nenhum tipo MIME suportado pelo QMediaPlayer. Verifique os plugins GStreamer. TESTA ESSES AQUI!")
            print("sudo apt update && sudo apt install --reinstall gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav libqt5multimedia5-plugins -y")
        del _test_player
    except Exception as e:
        print(f"Erro ao inicializar QMediaPlayer: {e}. Verifique plugins GStreamer.")
        sys.exit(1)

    player_window = PublicidadePlayer()
    player_window.show()
    sys.exit(app.exec_())

