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
# URL da API para inserir contagem de exibições
API_INSERT_EXIBICOES_URL = "https://example.com/levamidia/api/insert_exibicoes_basico.php"

# --- Caminho da pasta de mídias ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(SCRIPT_DIR, "midias")

# --- Intervalos e Tempos ---
API_PUBLICIDADE_CHECK_INTERVAL_MS = 10000  # 10 segundos
API_INFORMATIVO_CHECK_INTERVAL_MS = 300000 # 5 minutos
IMAGE_DISPLAY_TIME_MS = 10000 # 10 segundos
INFORMATIVO_DISPLAY_TIME_MS = 120000 # 2 minutos
DATETIME_UPDATE_INTERVAL_MS = 1000 # 1 segundo
# Intervalo para reportar contagem de exibições: 1 minuto
REPORT_INTERVAL_MS = 60000 # 1 * 60 * 1000 ms

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
        self.condo_info_label.setStyleSheet("color: #eee; font-size: 24px; font-weight: bold; background-color: transparent;")
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

        # Lado Direito (Estilizado para ocupar 100%)
        right_widget = QWidget()
        right_widget.setStyleSheet("background-color: #1A1A1A; padding: 20px;")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0) # Ajustado para usar o padding do widget
        right_layout.setSpacing(10)

        self.info_details_label = QLabel("Carregando detalhes do informativo...")
        self.info_details_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.info_details_label.setStyleSheet("color: #E0E0E0; font-size: 20px; background-color: transparent;")
        self.info_details_label.setWordWrap(True)
        # Política de tamanho para ocupar espaço vertical
        self.info_details_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        right_layout.addWidget(self.info_details_label)

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
        self.playback_timer.timeout.connect(self.finish_current_media) # Conecta ao método que finaliza e incrementa

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
        self.informativo_rotation_timer = QTimer(self)
        self.informativo_rotation_timer.timeout.connect(self.display_next_informativo)

        self.datetime_timer = QTimer(self)
        self.datetime_timer.timeout.connect(self.update_datetime_label)
        self.datetime_timer.start(DATETIME_UPDATE_INTERVAL_MS)
        self.update_datetime_label()

        # Novo Timer para reportar contagem
        self.report_timer = QTimer(self)
        self.report_timer.timeout.connect(self.report_counts)
        self.report_timer.start(REPORT_INTERVAL_MS)

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
                 print(f"Removida mídia {media_id} dos dados locais.")

        # Adiciona/Atualiza mídias da nova playlist
        for item in new_playlist:
            media_id = item['id_conteudo']
            url = item['url'] # Já garantido que é a URL correta pela thread
            filename = item['nome']
            local_path = os.path.join(MEDIA_DIR, filename)
            if media_id not in self.media_data:
                self.media_data[media_id] = {'path': local_path, 'count': 0, 'url': url}
                print(f"Adicionada nova mídia {media_id} aos dados locais.")
            else:
                # Atualiza path/url caso tenham mudado, mantém a contagem
                self.media_data[media_id]['path'] = local_path
                self.media_data[media_id]['url'] = url

        self.download_media()

        # Se nada estava tocando, inicia a reprodução
        if self.player.state() == QMediaPlayer.StoppedState and not self.playback_timer.isActive():
             if not self.playlist:
                 print("Playlist de publicidade vazia após atualização.")
                 self.stop_playback()
             else:
                 print("Iniciando reprodução da publicidade.")
                 self.current_playlist_index = -1
                 self.last_played_media_id = None # Reseta ao iniciar nova playlist
                 self.play_next_publicidade()
        else:
            print("Playlist de publicidade atualizada, reprodução continuará.")
            # Ajusta o índice se ele ficou inválido
            if self.current_playlist_index >= len(self.playlist):
                self.current_playlist_index = -1
                # Não chama play_next aqui, deixa o ciclo natural continuar

    def update_informativos(self, new_informativos):
        if self.informativo_rotation_timer.isActive():
            self.informativo_rotation_timer.stop()
        self.informativos = new_informativos
        self.current_informativo_index = -1
        if self.informativos:
            # print(f"Recebidos {len(self.informativos)} informativos para o ciclo.")
            self.display_next_informativo()
        else:
            self.condo_info_label.setText("Sem informativos no momento.")
            self.info_details_label.setText("")

    # Lógica de Exibição dos Informativos
    def display_next_informativo(self):
        if self.informativo_rotation_timer.isActive():
            self.informativo_rotation_timer.stop()

        if not self.informativos:
            self.condo_info_label.setText("Sem informativos no momento.")
            self.info_details_label.setText("")
            return

        self.current_informativo_index = (self.current_informativo_index + 1) % len(self.informativos)
        informativo = self.informativos[self.current_informativo_index]
        # print(f"Exibindo informativo {self.current_informativo_index + 1}/{len(self.informativos)} por {INFORMATIVO_DISPLAY_TIME_MS / 1000}s")

        # Atualiza o label superior do rodapé
        self.condo_info_label.setText(informativo.get("informativo_aviso", "Aviso indisponível"))

        # Atualiza o painel direito
        titulo = informativo.get("informativo_titulo", "")
        subtitulo = informativo.get("informativo_subtitulo", "")
        texto = informativo.get("informativo_texto", "")

        # Formata o texto com HTML básico para o QLabel
        details_text = f'''<p style="font-size: 24px; font-weight: bold; color: #FFFFFF; margin-bottom: 10px;">{titulo}</p>'''
        if subtitulo:
            details_text += f'''<p style="font-size: 18px; color: #B0B0B0; font-style: italic; margin-bottom: 15px;">{subtitulo}</p>'''
        # Substitui quebras de linha por <br/> para HTML
        texto_html = texto.replace("\n", "<br/>")
        details_text += f'''<p style="font-size: 16px; color: #D0D0D0; line-height: 1.4;">{texto_html}</p>'''

        self.info_details_label.setText(details_text)

        # Reinicia o timer para o próximo informativo
        self.informativo_rotation_timer.start(INFORMATIVO_DISPLAY_TIME_MS)

    def download_media(self):
        print("Verificando/baixando mídias de publicidade...")
        if not self.playlist:
            print("Playlist vazia, nada para baixar.")
            return

        # Usa self.media_data que já foi atualizado
        media_to_download = list(self.media_data.items()) # Cria cópia para iterar
        for media_id, data in media_to_download:
            local_path = data['path']
            url = data['url']
            if not os.path.exists(local_path):
                print(f"Baixando mídia ID {media_id}: {url} para {local_path}")
                try:
                    response = requests.get(url, stream=True, timeout=30)
                    response.raise_for_status()
                    with open(local_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"Download concluído: {local_path}")
                except requests.exceptions.RequestException as e:
                    print(f"Erro ao baixar {url}: {e}")
                    # Remove arquivo parcial se existir e remove dos dados locais para não tentar tocar
                    if os.path.exists(local_path):
                        os.remove(local_path)
                    if media_id in self.media_data:
                         del self.media_data[media_id]
                         # Remove da playlist ativa também para evitar tentar tocar
                         self.playlist = [item for item in self.playlist if item['id_conteudo'] != media_id]
                         print(f"Removida mídia ID {media_id} devido a falha no download.")
                except Exception as e:
                    print(f"Erro inesperado durante download de {url}: {e}")
                    if os.path.exists(local_path):
                        os.remove(local_path)
                    if media_id in self.media_data:
                         del self.media_data[media_id]
                         self.playlist = [item for item in self.playlist if item['id_conteudo'] != media_id]
                         print(f"Removida mídia ID {media_id} devido a erro inesperado no download.")
            # else: # Descomente para debug
            #     print(f"Mídia ID {media_id} já existe localmente: {local_path}")

        # Limpa arquivos órfãos no diretório de mídia
        self.cleanup_orphan_files()
        print("Verificação/download de mídias de publicidade concluído.")

    def cleanup_orphan_files(self):
        if not os.path.exists(MEDIA_DIR):
            return
        try:
            # Obtém todos os caminhos de arquivo atualmente em uso (no dicionário media_data)
            current_files_in_use = set(data['path'] for data in self.media_data.values())
            # Itera sobre os arquivos no diretório de mídia
            for filename in os.listdir(MEDIA_DIR):
                file_path = os.path.join(MEDIA_DIR, filename)
                # Se for um arquivo e não estiver na lista de arquivos em uso, remove
                if os.path.isfile(file_path) and file_path not in current_files_in_use:
                    print(f"Limpando arquivo órfão: {file_path}")
                    os.remove(file_path)
        except Exception as e:
            print(f"Erro ao limpar arquivos órfãos: {e}")

    # Lógica de Reprodução da Publicidade
    def play_next_publicidade(self):
        # Para timers antigos
        if self.playback_timer.isActive():
            self.playback_timer.stop()
        if self.player.state() != QMediaPlayer.StoppedState:
            self.player.stop()

        if not self.playlist:
            print("Playlist de publicidade vazia, parando reprodução.")
            self.stop_playback()
            return

        # Avança o índice
        self.current_playlist_index = (self.current_playlist_index + 1) % len(self.playlist)
        media_item = self.playlist[self.current_playlist_index]
        media_id = media_item['id_conteudo']

        # Verifica se temos dados locais para essa mídia
        if media_id not in self.media_data:
            print(f"Erro: Mídia ID {media_id} não encontrada nos dados locais. Pulando.")
            # Tenta tocar a próxima imediatamente
            QTimer.singleShot(100, self.play_next_publicidade)
            return

        local_path = self.media_data[media_id]['path']

        if not os.path.exists(local_path):
            print(f"Arquivo não encontrado localmente: {local_path}. Tentando baixar novamente ou pular.")
            # Tenta baixar de novo rapidamente
            self.download_media() # Poderia ser mais específico, mas por ora baixa tudo
            if not os.path.exists(local_path):
                 print(f"Download falhou novamente para {local_path}. Pulando item.")
                 QTimer.singleShot(100, self.play_next_publicidade)
                 return
            else:
                 print("Download rápido bem-sucedido. Continuando...")

        # print(f"Reproduzindo mídia ID {media_id}: {local_path}")
        self.last_played_media_id = media_id # Guarda o ID da mídia que vai começar

        if local_path.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
            self.image_label.hide()
            self.video_widget.show()
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(local_path)))
            self.player.play()
            # O incremento da contagem será feito em media_status_changed ou finish_current_media
        elif local_path.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif")):
            self.video_widget.hide()
            self.image_label.show()
            pixmap = QPixmap(local_path)
            if pixmap.isNull():
                print(f"Erro ao carregar imagem: {local_path}")
                self.image_label.setText("Erro Imagem")
                self.last_played_media_id = None # Não conta exibição se deu erro
                self.playback_timer.start(2000) # Mostra erro por 2s e pula
            else:
                # Redimensiona a imagem para caber no label mantendo a proporção
                scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(scaled_pixmap)
                # Inicia timer para mostrar a imagem e depois chamar finish_current_media
                self.playback_timer.start(IMAGE_DISPLAY_TIME_MS)
        else:
            print(f"Formato de arquivo não suportado: {local_path}")
            self.last_played_media_id = None # Não conta exibição se formato inválido
            # Pula para o próximo item após um pequeno delay
            QTimer.singleShot(100, self.play_next_publicidade)

    # Chamado quando uma mídia (imagem ou vídeo) termina sua exibição
    def finish_current_media(self):
        if self.last_played_media_id is not None and self.last_played_media_id in self.media_data:
            self.media_data[self.last_played_media_id]['count'] += 1
            # print(f"Incrementado contador para mídia ID {self.last_played_media_id}. Nova contagem: {self.media_data[self.last_played_media_id]['count']}")
        else:
            # print("Nenhuma mídia anterior válida para incrementar contador.")
            pass

        self.last_played_media_id = None # Reseta para a próxima mídia
        self.play_next_publicidade() # Toca a próxima mídia da playlist

    # Chamado quando o status do QMediaPlayer muda (ex: vídeo terminou)
    def media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            # print(f"Vídeo ID {self.last_played_media_id} terminou.")
            self.finish_current_media()
        elif status == QMediaPlayer.InvalidMedia:
            print(f"Erro: Mídia inválida - {self.player.errorString()}")
            self.last_played_media_id = None # Não conta exibição se inválida
            self.play_next_publicidade() # Pula para a próxima
        elif status == QMediaPlayer.LoadedMedia:
            # print("Mídia carregada.")
            pass
        elif status == QMediaPlayer.LoadingMedia:
            # print("Carregando mídia...")
            pass

    def handle_player_error(self, error):
        # Adiciona uma verificação para ignorar erros "sem erro" que podem ocorrer
        if error != QMediaPlayer.NoError:
            print(f"Erro no Player: {self.player.errorString()} (Código: {error})")
            # Tenta tocar o próximo item mesmo em caso de erro
            self.last_played_media_id = None # Não conta exibição se deu erro no player
            self.play_next_publicidade()
        # else: # Descomente para debug
        #     print("Recebido sinal de erro do player, mas sem erro real (NoError). Ignorando.")


    def update_datetime_label(self):
        now = QDateTime.currentDateTime()
        self.datetime_label.setText(now.toString("dd/MM/yyyy HH:mm:ss"))

    # --- Lógica de Contagem e Envio para API ---
    def report_counts(self):
        # print("Verificando contagens para reportar...")
        items_to_report = []
        # Cria uma cópia das chaves para iterar, pois podemos modificar o dicionário
        media_ids = list(self.media_data.keys())

        for media_id in media_ids:
            # Verifica se a mídia ainda existe nos dados (pode ter sido removida)
            if media_id in self.media_data and self.media_data[media_id]['count'] > 0:
                items_to_report.append((media_id, self.media_data[media_id]['count']))

        if not items_to_report:
            # print("Nenhuma contagem para reportar.")
            return

        # print(f"Enviando {len(items_to_report)} contagens para a API...")
        for media_id, count in items_to_report:
            self.send_count_to_api(media_id, count)
            # Pausa pequena entre requisições para não sobrecarregar a API (opcional)
            time.sleep(0.1)

    def send_count_to_api(self, media_id, count):
        params = {
            'exibicao_qtd': count,
            'id_tela': ID_TELA,
            'id_conteudo': media_id
        }
        try:
            # print(f"Enviando contagem para API: id_conteudo={media_id}, qtd={count}")
            response = requests.get(API_INSERT_EXIBICOES_URL, params=params, timeout=10)
            response.raise_for_status() # Levanta erro para status HTTP >= 400

            # Verifica a resposta EXATA de sucesso
            try:
                response_data = response.json()
                # Compara o dicionário de resposta diretamente
                if response_data == {"success": "Exibição atualizada com sucesso"}:
                    print(f"Sucesso ao enviar contagem para mídia ID {media_id}. Zerando contador local.")
                    # Zera o contador local APENAS se a API confirmou
                    if media_id in self.media_data:
                        self.media_data[media_id]['count'] = 0
                else:
                    print(f"API de contagem retornou resposta inesperada para mídia ID {media_id}: {response.text}. Contador NÃO zerado.")
            except json.JSONDecodeError:
                print(f"API de contagem retornou resposta não-JSON para mídia ID {media_id}: {response.text}. Contador NÃO zerado.")

        except requests.exceptions.RequestException as e:
            print(f"Falha ao enviar contagem para API para mídia ID {media_id}: {e}. Contador NÃO zerado.")
        except Exception as e:
            print(f"Erro inesperado ao enviar contagem para API para mídia ID {media_id}: {e}. Contador NÃO zerado.")

    # --- Eventos da Janela ---
    def resizeEvent(self, event):
        # Redimensiona a imagem quando a janela/label muda de tamanho
        if hasattr(self, 'image_label') and self.image_label.pixmap() and not self.image_label.pixmap().isNull():
            # Pega o pixmap original (não o já escalado) para reescalar
            # Precisamos buscar o path original e recarregar o pixmap
            # Verifica se a última mídia tocada era uma imagem e existe nos dados
            if self.last_played_media_id and self.last_played_media_id in self.media_data:
                 original_path = self.media_data[self.last_played_media_id]['path']
                 # Verifica se o path é de uma imagem antes de tentar carregar
                 if original_path.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".gif")) and os.path.exists(original_path):
                     pixmap = QPixmap(original_path)
                     if not pixmap.isNull():
                          scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                          self.image_label.setPixmap(scaled_pixmap)
        super().resizeEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Q:
            print("Tecla 'Q' pressionada. Encerrando...")
            self.close()
        else:
            super().keyPressEvent(event)

    def stop_playback(self):
        print("Parando reprodução...")
        if self.playback_timer.isActive():
            self.playback_timer.stop()
        if self.player.state() != QMediaPlayer.StoppedState:
            self.player.stop()
        self.video_widget.hide()
        self.image_label.hide()

    def closeEvent(self, event):
        print("Fechando aplicação...")
        self.stop_playback()

        # Para as threads de API
        if hasattr(self, 'publicidade_api_thread') and self.publicidade_api_thread.isRunning():
            self.publicidade_api_thread.stop()
        if hasattr(self, 'informativo_api_thread') and self.informativo_api_thread.isRunning():
            self.informativo_api_thread.stop()

        # Para os timers
        if hasattr(self, 'informativo_rotation_timer') and self.informativo_rotation_timer.isActive():
            self.informativo_rotation_timer.stop()
        if hasattr(self, 'datetime_timer') and self.datetime_timer.isActive():
            self.datetime_timer.stop()
        if hasattr(self, 'report_timer') and self.report_timer.isActive():
            self.report_timer.stop()
            # Tenta enviar uma última vez as contagens pendentes ao fechar
            print("Enviando contagens finais antes de fechar...")
            self.report_counts()
            # Espera um pouco para dar tempo das requisições terminarem (opcional)
            time.sleep(1) # Espera 1 segundo

        print("Aplicação encerrada.")
        event.accept()

# --- Bloco Principal de Execução ---
if __name__ == '__main__':
    # Verifica se o diretório de mídia existe, se não, cria
    if not os.path.exists(MEDIA_DIR):
        try:
            os.makedirs(MEDIA_DIR)
            print(f"Diretório de mídia criado em: {MEDIA_DIR}")
        except OSError as e:
            print(f"Erro ao criar diretório de mídia {MEDIA_DIR}: {e}")
            sys.exit(1) # Sai se não conseguir criar o diretório

    app = QApplication(sys.argv)
    player_window = PublicidadePlayer()
    player_window.show()
    sys.exit(app.exec_())

