#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# --- Importações de Bibliotecas ---
import sys
import os
import requests # Para fazer requisições HTTP (buscar a API)
import time     # Para pausas (embora usemos QTimer principalmente)
import datetime # Para obter a data e hora atuais
import json     # Para tratar respostas JSON da API de contagem
import queue
import re
import subprocess
import tempfile
import threading
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QSpacerItem,
    QDesktopWidget, QShortcut, QScrollArea
) # Componentes da interface gráfica
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent # Para tocar vídeo/áudio
from PyQt5.QtMultimediaWidgets import QVideoWidget # Widget específico para exibir vídeo
from PyQt5.QtCore import QUrl, Qt, QTimer, QThread, pyqtSignal, QSize, QDateTime # Utilitários, Timers, Threads, Sinais, Data/Hora
from PyQt5.QtGui import QPixmap, QKeyEvent, QKeySequence # Para exibir imagens e capturar teclas

class ElidedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.full_text = ""
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.set_full_text(text)

    def set_full_text(self, text):
        self.full_text = text or ""
        self.update_elided_text()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_elided_text()

    def update_elided_text(self):
        available_width = self.width()

        if available_width <= 0:
            QLabel.setText(self, self.full_text)
            return

        elided_text = self.fontMetrics().elidedText(self.full_text, Qt.ElideRight, available_width)
        QLabel.setText(self, elided_text)

# --- Constantes Globais ---
def get_required_int_env(name):
    value = os.environ.get(name)
    if value is None or str(value).strip() == "":
        raise RuntimeError(f"Variavel de ambiente obrigatoria ausente: {name}")

    try:
        parsed_value = int(value)
    except (TypeError, ValueError):
        raise RuntimeError(f"Variavel de ambiente invalida para {name}: {value}")

    if parsed_value <= 0:
        raise RuntimeError(f"Variavel de ambiente deve ser maior que zero para {name}: {value}")

    return parsed_value


ID_LOCAL = get_required_int_env("NEUROON_ID_LOCAL")
APP_VERSION = os.environ.get("NEUROON_APP_VERSION", "1.0.0")

BASE_URL = os.environ.get("NEUROON_API_BASE_URL", "https://example.com/nextpubli/api/raspberry").rstrip("/")

# URL da API que fornece a lista de mídias (publicidade)
API_PUBLICIDADE_URL = f"{BASE_URL}/get_publicidade.php?id_local={ID_LOCAL}"
# URL da API que fornece os informativos
API_INFORMATIVO_URL_BASE = f"{BASE_URL}/get_informativo.php"
# URL da API para inserir exibições individuais
API_INSERT_EXIBICOES_URL = f"{BASE_URL}/insert_publicidade_exibicao.php"
# URL da API para verificar o formato da tela
API_POSICAO_TELA_URL = f"{BASE_URL}/get_posicao_tela.php?id_local={ID_LOCAL}"
# URL da API para registrar atividade do aparelho
API_PING_APARELHO_URL = f"{BASE_URL}/ping_aparelho.php?id_local={ID_LOCAL}"
# URL da API para buscar senhas chamadas no formato de tela 4
API_SENHAS_CHAMADA_URL = f"{BASE_URL}/get_senhas_chamada.php?id_local={ID_LOCAL}"
# URL da API para buscar configuracoes iniciais do player
API_CONFIGURACOES_URL = f"{BASE_URL}/get_configuracoes.php?id_local={ID_LOCAL}"

def api_response_as_list(data, api_name):
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        message = data.get("erro") or data.get("mensagem") or data.get("info")
        if message:
            print(f"{api_name}: {message}")
            return []

    raise ValueError(f"{api_name}: resposta não é uma lista")

# --- Caminho da pasta de mídias e ícones ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(SCRIPT_DIR, "midias")
ICON_DIR = os.path.join(SCRIPT_DIR, "icons") # Caminho para ícones
# --- Audio das chamadas de senha ---
SENHAS_AUDIO_ENABLED = True
SENHAS_AUDIO_TEST_ON_WINDOWS = True
PIPER_PYTHON = os.path.expanduser("~/piper-venv/bin/python")
PIPER_DATA_DIR = os.path.expanduser("~/piper-voices")
PIPER_MODEL = "pt_BR-faber-medium"
AUDIO_PLAYER = "aplay"

# --- Intervalos e Tempos ---
API_PUBLICIDADE_CHECK_INTERVAL_MS = 10000  # 10 segundos
API_INFORMATIVO_CHECK_INTERVAL_MS = 300000 # 5 minutos
API_POSICAO_TELA_CHECK_INTERVAL_MS = 60000 # 1 minutos
API_PING_APARELHO_INTERVAL_MS = 60000 # 1 minuto
API_SENHAS_CHAMADA_INTERVAL_MS = 3000 # 3 segundos
SENHAS_CHAMADA_FULLSCREEN_TIMEOUT_MS = 600000 # 10 minutos
IMAGE_DISPLAY_TIME_MS = 10000 # 10 segundos
INFORMATIVO_DISPLAY_TIME_MS = 120000 # 2 minutos
DATETIME_UPDATE_INTERVAL_MS = 1000 # 1 segundo
# Intervalo para reportar exibições: 1 minuto
REPORT_INTERVAL_MS = 60000 # 1 * 60 * 1000 ms
MAX_EXIBICOES_INSERT_REQUESTS_PER_REPORT = 50

# --- Tamanhos de Fonte em Pixels ---
FONT_SIZE_TITULO = 24
FONT_SIZE_SUBTITULO = 18
FONT_SIZE_TEXTO = 14
FONT_SIZE_AVISO = 24 # Tamanho da fonte para o informativo_aviso
FONT_SIZE_ICON = 20

CONFIG_FIELDS = {
    "api_publicidade_check_interval_ms": "API_PUBLICIDADE_CHECK_INTERVAL_MS",
    "api_informativo_check_interval_ms": "API_INFORMATIVO_CHECK_INTERVAL_MS",
    "api_posicao_tela_check_interval_ms": "API_POSICAO_TELA_CHECK_INTERVAL_MS",
    "api_ping_aparelho_interval_ms": "API_PING_APARELHO_INTERVAL_MS",
    "api_senhas_chamada_interval_ms": "API_SENHAS_CHAMADA_INTERVAL_MS",
    "senhas_chamada_fullscreen_timeout_ms": "SENHAS_CHAMADA_FULLSCREEN_TIMEOUT_MS",
    "image_display_time_ms": "IMAGE_DISPLAY_TIME_MS",
    "informativo_display_time_ms": "INFORMATIVO_DISPLAY_TIME_MS",
    "datetime_update_interval_ms": "DATETIME_UPDATE_INTERVAL_MS",
    "report_interval_ms": "REPORT_INTERVAL_MS",
    "font_size_titulo": "FONT_SIZE_TITULO",
    "font_size_subtitulo": "FONT_SIZE_SUBTITULO",
    "font_size_texto": "FONT_SIZE_TEXTO",
    "font_size_aviso": "FONT_SIZE_AVISO",
    "font_size_icon": "FONT_SIZE_ICON",
}

def apply_runtime_config(config):
    validated_config = {}

    for api_key, global_name in CONFIG_FIELDS.items():
        value = config.get(api_key)

        if value is None:
            raise ValueError(f"Configuracao ausente: {api_key}")

        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValueError(f"Configuracao invalida para {api_key}: {value}")

        if value <= 0:
            raise ValueError(f"Configuracao deve ser maior que zero para {api_key}: {value}")

        validated_config[global_name] = value

    for global_name, value in validated_config.items():
        globals()[global_name] = value

# --- Thread para Buscar Configuracoes Iniciais ---
class ConfiguracoesApiThread(QThread):
    configuracoes_loaded = pyqtSignal(dict)
    status_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.stop_event = threading.Event()

    def run(self):
        while self.running and not self.stop_event.is_set():
            try:
                response = requests.get(API_CONFIGURACOES_URL, timeout=10)
                response.raise_for_status()
                data = response.json()

                if not isinstance(data, dict):
                    raise ValueError("API de Configuracoes: resposta nao e um objeto JSON")

                if data.get("success") is False:
                    raise ValueError(data.get("erro") or data.get("mensagem") or data)

                config = data.get("configuracoes", data)
                if not isinstance(config, dict):
                    raise ValueError("API de Configuracoes: configuracoes nao e um objeto")

                apply_runtime_config(config)
                print("Configuracoes carregadas com sucesso.")
                self.configuracoes_loaded.emit(config)
                return

            except Exception as e:
                error_msg = f"Falha ao buscar configuracoes iniciais: {e}"
                print(error_msg)
                self.status_signal.emit(error_msg)

            if self.stop_event.wait(5):
                break

    def stop(self):
        print("Parando a thread da API de Configuracoes...")
        self.running = False
        self.stop_event.set()
        if not self.wait(3000):
            print("Thread da API de Configuracoes nao respondeu ao stop; encerrando forcado.")
            self.terminate()
            self.wait(1000)

# --- Thread para Verificar a API de Publicidade Periodicamente ---
class PublicidadeApiThread(QThread):
    playlist_updated = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_media_list_signature = set() # Usado para detectar mudanças reais
        self.running = True
        self.stop_event = threading.Event()

    def run(self):
        while self.running and not self.stop_event.is_set():
            try:
                response = requests.get(API_PUBLICIDADE_URL, timeout=10)
                response.raise_for_status()
                new_media_list_raw = api_response_as_list(response.json(), "API de Publicidade")

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

            if self.stop_event.wait(API_PUBLICIDADE_CHECK_INTERVAL_MS / 1000):
                break

    def stop(self):
        print("Parando a thread da API de Publicidade...")
        self.running = False
        self.stop_event.set()
        if not self.wait(3000):
            print("Thread da API de Publicidade nao respondeu ao stop; encerrando forçado.")
            self.terminate()
            self.wait(1000)

# --- Thread para Verificar a API de Informativos Periodicamente ---
class InformativoApiThread(QThread):
    informativos_updated = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.stop_event = threading.Event()

    def run(self):
        while self.running and not self.stop_event.is_set():
            try:
                now = datetime.datetime.now()
                data_str = now.strftime("%Y-%m-%dT%H:%M:%S")
                params = {
                    'id': ID_LOCAL,
                    'data': data_str
                }
                # print(f"Buscando informativos: {API_INFORMATIVO_URL_BASE} com params: {params}")

                response = requests.get(API_INFORMATIVO_URL_BASE, params=params, timeout=10)
                response.raise_for_status()
                new_informativos = api_response_as_list(response.json(), "API de Informativo")

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

            if self.stop_event.wait(API_INFORMATIVO_CHECK_INTERVAL_MS / 1000):
                break

    def stop(self):
        print("Parando a thread da API de Informativo...")
        self.running = False
        self.stop_event.set()
        if not self.wait(3000):
            print("Thread da API de Informativo nao respondeu ao stop; encerrando forçado.")
            self.terminate()
            self.wait(1000)

# --- Thread para Verificar o Formato da Tela Periodicamente ---
class PosicaoTelaApiThread(QThread):
    formato_tela_updated = pyqtSignal(int)
    error_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.stop_event = threading.Event()
        self.current_formato = None  # Armazena o formato atual para detectar mudanças

    def run(self):
        while self.running and not self.stop_event.is_set():
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

            if self.stop_event.wait(API_POSICAO_TELA_CHECK_INTERVAL_MS / 1000):
                break

    def stop(self):
        print("Parando a thread da API de Posição Tela...")
        self.running = False
        self.stop_event.set()
        if not self.wait(3000):
            print("Thread da API de Posicao Tela nao respondeu ao stop; encerrando forçado.")
            self.terminate()
            self.wait(1000)

# --- Thread para registrar atividade do aparelho periodicamente ---
class HeartbeatApiThread(QThread):
    error_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.stop_event = threading.Event()

    def run(self):
        while self.running and not self.stop_event.is_set():
            try:
                response = requests.get(
                    API_PING_APARELHO_URL,
                    params={'versao_app': APP_VERSION},
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()

                if isinstance(data, dict) and data.get("success"):
                    print("Ping de atividade enviado.")
                else:
                    error_msg = f"Resposta inesperada da API de ping: {data}"
                    print(error_msg)
                    self.error_signal.emit(error_msg)

            except requests.exceptions.RequestException as e:
                error_msg = f"Falha na requisicao da API de ping: {e}"
                print(error_msg)
                self.error_signal.emit(error_msg)
            except ValueError as e:
                error_msg = f"Erro nos dados da API de ping: {e}"
                print(error_msg)
                self.error_signal.emit(error_msg)
            except Exception as e:
                error_msg = f"Erro inesperado na thread da API de ping: {e}"
                print(error_msg)
                self.error_signal.emit(error_msg)

            if self.stop_event.wait(API_PING_APARELHO_INTERVAL_MS / 1000):
                break

    def stop(self):
        print("Parando a thread da API de ping...")
        self.running = False
        self.stop_event.set()
        if not self.wait(3000):
            print("Thread da API de ping nao respondeu ao stop; encerrando forcado.")
            self.terminate()
            self.wait(1000)

# --- Janela Principal da Aplicação ---
# --- Thread para buscar senhas chamadas no formato de tela 4 ---
class SenhasChamadaApiThread(QThread):
    senhas_updated = pyqtSignal(list, bool)
    error_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.stop_event = threading.Event()

    def run(self):
        interval_seconds = API_SENHAS_CHAMADA_INTERVAL_MS / 1000

        while self.running and not self.stop_event.is_set():
            started_at = time.monotonic()

            try:
                response = requests.get(API_SENHAS_CHAMADA_URL, timeout=2.5)
                response.raise_for_status()
                data = response.json()

                if isinstance(data, list):
                    valid_senhas = []

                    for item in data:
                        if isinstance(item, dict) and all(k in item for k in ["senha", "cliente_nome", "qtd_pessoas"]):
                            valid_senhas.append({
                                "senha": item["senha"],
                                "cliente_nome": item["cliente_nome"],
                                "qtd_pessoas": item["qtd_pessoas"]
                            })
                        else:
                            print(f"Senha invalida descartada: {item}")

                    self.senhas_updated.emit(valid_senhas, True)
                elif isinstance(data, dict):
                    message = data.get("erro") or data.get("mensagem") or data.get("info")
                    error_msg = f"API de Senhas: {message or data}"
                    print(error_msg)
                    self.senhas_updated.emit([], False)
                    self.error_signal.emit(error_msg)
                else:
                    error_msg = "API de Senhas: resposta nao e uma lista"
                    print(error_msg)
                    self.senhas_updated.emit([], False)
                    self.error_signal.emit(error_msg)

            except requests.exceptions.RequestException as e:
                error_msg = f"Falha na requisicao da API de Senhas: {e}"
                print(error_msg)
                self.senhas_updated.emit([], False)
                self.error_signal.emit(error_msg)
            except ValueError as e:
                error_msg = f"Erro nos dados da API de Senhas: {e}"
                print(error_msg)
                self.senhas_updated.emit([], False)
                self.error_signal.emit(error_msg)
            except Exception as e:
                error_msg = f"Erro inesperado na thread da API de Senhas: {e}"
                print(error_msg)
                self.senhas_updated.emit([], False)
                self.error_signal.emit(error_msg)

            elapsed = time.monotonic() - started_at
            wait_seconds = max(0, interval_seconds - elapsed)

            if self.stop_event.wait(wait_seconds):
                break

    def stop(self):
        print("Parando a thread da API de Senhas...")
        self.running = False
        self.stop_event.set()
        if not self.wait(3000):
            print("Thread da API de Senhas nao respondeu ao stop; encerrando forcado.")
            self.terminate()
            self.wait(1000)

class SenhaSpeechManager:
    def __init__(self):
        self.enabled = SENHAS_AUDIO_ENABLED
        self.queue = queue.Queue()
        self.stop_event = threading.Event()
        self.worker = threading.Thread(target=self._run, daemon=True)
        self.availability_checked = False
        self.available = False
        self.worker.start()

    def enqueue_senha(self, senha):
        if not self.enabled or self.stop_event.is_set():
            return

        text = self.build_speech_text(senha)
        if not text:
            return

        self.queue.put(text)

    def build_speech_text(self, senha):
        cliente_nome = self.normalize_text(senha.get("cliente_nome", ""))
        senha_codigo = self.normalize_senha_codigo(senha.get("senha", ""))

        if not senha_codigo:
            return ""

        if cliente_nome:
            return f"{cliente_nome}, senha {senha_codigo}"

        return f"Senha {senha_codigo}"

    def normalize_text(self, value):
        return " ".join(str(value or "").split())

    def normalize_senha_codigo(self, value):
        senha_codigo = self.normalize_text(value)
        senha_codigo = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", senha_codigo)
        senha_codigo = re.sub(r"(?<=\d)(?=[A-Za-z])", " ", senha_codigo)
        return senha_codigo

    def _run(self):
        while not self.stop_event.is_set():
            try:
                text = self.queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                self._speak_blocking(text)
            except Exception as e:
                print(f"Erro ao tocar audio da senha: {e}")
            finally:
                self.queue.task_done()

    def _speak_blocking(self, text):
        if sys.platform.startswith("win") and SENHAS_AUDIO_TEST_ON_WINDOWS:
            print(f"[AUDIO TESTE] {text}")
            return

        if not self._ensure_available():
            return

        audio_path = None

        try:
            with tempfile.NamedTemporaryFile(prefix="senha_chamada_", suffix=".wav", delete=False) as audio_file:
                audio_path = audio_file.name

            subprocess.run([
                PIPER_PYTHON,
                "-m",
                "piper",
                "-m",
                PIPER_MODEL,
                "--data-dir",
                PIPER_DATA_DIR,
                "-f",
                audio_path,
                "--",
                text,
            ], check=True)

            subprocess.run([AUDIO_PLAYER, audio_path], check=True)
        finally:
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except OSError as e:
                    print(f"Nao foi possivel remover audio temporario {audio_path}: {e}")

    def _ensure_available(self):
        if self.availability_checked:
            return self.available

        self.availability_checked = True
        missing = []

        if not os.path.exists(PIPER_PYTHON):
            missing.append(PIPER_PYTHON)
        if not os.path.isdir(PIPER_DATA_DIR):
            missing.append(PIPER_DATA_DIR)

        if missing:
            print("Audio de chamadas desativado. Piper nao encontrado: " + ", ".join(missing))
            self.available = False
            return False

        self.available = True
        return True

    def stop(self):
        self.stop_event.set()

        while True:
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except queue.Empty:
                break

        if self.worker.is_alive():
            self.worker.join(timeout=1)


def senha_chamada_key(senha):
    return (
        str(senha.get("senha", "")).strip(),
        str(senha.get("cliente_nome", "")).strip().lower(),
    )
# --- Janela Principal da Aplicacao ---
class PublicidadePlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.playlist = [] # Lista de dicionários da API (url, nome, id_conteudo)
        self.current_playlist_index = -1
        # Dicionário para armazenar dados locais por id_conteudo
        # Estrutura: {id_conteudo: {'path': local_path, 'url': original_url}}
        self.media_data = {}
        self.pending_exibicoes = []
        self.informativos = []
        self.current_informativo_index = -1
        self.api_error_count = 0
        self.is_closing = False
        self.last_played_media_id = None # Para saber qual mídia acabou de tocar
        self.current_image_pixmap = None
        self.formato_tela = None
        self.senhas_chamada = []
        self.senhas_chamada_empty_since = None
        self.senhas_chamada_panel_active = False
        self.senhas_chamada_api_thread = None
        self.senhas_scroll_direction = 1
        self.senhas_title_font_size = 38
        self.senhas_item_min_height = 140
        self.senhas_item_senha_font_size = 30
        self.senhas_item_nome_font_size = 24
        self.senhas_item_pessoas_font_size = 20
        self.senha_speech_manager = SenhaSpeechManager()
        self.configuracoes_api_thread = None
        self.config_status_label = None
        self.configuracoes_loaded = False
        self.quit_shortcut = QShortcut(QKeySequence("Q"), self)
        self.quit_shortcut.setContext(Qt.ApplicationShortcut)
        self.quit_shortcut.activated.connect(self.close_from_q)

        # Armazena as dimensões da tela
        self.screen_geometry = QDesktopWidget().screenGeometry()
        self.screen_width = self.screen_geometry.width()
        self.screen_height = self.screen_geometry.height()

        if not os.path.exists(MEDIA_DIR):
            print(f"Criando diretório de mídia: {MEDIA_DIR}")
            os.makedirs(MEDIA_DIR)

        self.init_config_loading_ui()
        self.start_configuracoes_thread()

    def init_config_loading_ui(self):
        self.setWindowTitle("NeuroOn Publicidade Player")
        self.setStyleSheet("background-color: black; color: white;")

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.config_status_label = QLabel("Buscando configurações...")
        self.config_status_label.setAlignment(Qt.AlignCenter)
        self.config_status_label.setStyleSheet("""
            color: white;
            background-color: black;
            font-size: 48px;
            font-weight: bold;
        """)
        main_layout.addWidget(self.config_status_label)

        self.showMaximized()
        QTimer.singleShot(100, self.showFullScreen)

    def start_configuracoes_thread(self):
        if self.configuracoes_api_thread is not None and self.configuracoes_api_thread.isRunning():
            return

        self.configuracoes_api_thread = ConfiguracoesApiThread(self)
        self.configuracoes_api_thread.configuracoes_loaded.connect(self.handle_configuracoes_loaded)
        self.configuracoes_api_thread.status_signal.connect(self.handle_configuracoes_status)
        self.configuracoes_api_thread.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if hasattr(self, 'image_label') and self.image_label.isVisible():
            QTimer.singleShot(0, self.update_image_pixmap)

    def handle_configuracoes_status(self, status_message):
        print(status_message)

    def handle_configuracoes_loaded(self, _config):
        if self.is_closing or self.configuracoes_loaded:
            return

        if self.config_status_label is not None:
            self.config_status_label.setText("Iniciando...")

        self.configuracoes_loaded = True
        self.create_widgets()
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

        self.senhas_panel_widget = QWidget()
        self.senhas_panel_widget.setStyleSheet("background-color: white;")
        senhas_panel_layout = QVBoxLayout(self.senhas_panel_widget)
        senhas_panel_layout.setContentsMargins(24, 24, 24, 24)
        senhas_panel_layout.setSpacing(14)

        self.senhas_title_label = QLabel("Chamadas")
        self.senhas_title_label.setAlignment(Qt.AlignCenter)
        self.senhas_title_label.setStyleSheet("""
            color: #111;
            font-size: 34px;
            font-weight: bold;
            background-color: transparent;
        """)
        senhas_panel_layout.addWidget(self.senhas_title_label)

        self.senhas_scroll_area = QScrollArea()
        self.senhas_scroll_area.setWidgetResizable(True)
        self.senhas_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.senhas_scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: white;
                border: none;
            }
            QScrollBar:vertical {
                background: #eef2f7;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #94a3b8;
                border-radius: 5px;
            }
        """)

        self.senhas_list_widget = QWidget()
        self.senhas_list_widget.setStyleSheet("background-color: white;")
        self.senhas_list_layout = QVBoxLayout(self.senhas_list_widget)
        self.senhas_list_layout.setContentsMargins(0, 0, 0, 0)
        self.senhas_list_layout.setSpacing(12)
        self.senhas_list_layout.addStretch(1)

        self.senhas_scroll_area.setWidget(self.senhas_list_widget)
        senhas_panel_layout.addWidget(self.senhas_scroll_area, 1)

        self.senhas_bottom_widget = QWidget()
        self.senhas_bottom_widget.setStyleSheet("background-color: white;")
        senhas_bottom_layout = QVBoxLayout(self.senhas_bottom_widget)
        senhas_bottom_layout.setContentsMargins(0, 0, 0, 0)
        senhas_bottom_layout.setSpacing(0)

        self.senhas_bottom_label = QLabel("")
        self.senhas_bottom_label.setAlignment(Qt.AlignCenter)
        self.senhas_bottom_label.setWordWrap(True)
        self.senhas_bottom_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.senhas_bottom_label.setStyleSheet("""
            color: white;
            background-color: #111827;
            font-size: 42px;
            font-weight: bold;
        """)
        senhas_bottom_layout.addWidget(self.senhas_bottom_label, 1)

    def detach_reusable_widgets(self):
        reusable_widget_names = [
            "media_container",
            "info_details_label",
            "info_image_label",
            "condo_info_label",
            "clima_widget",
            "dollar_widget",
            "btc_widget",
            "datetime_widget",
            "senhas_panel_widget",
            "senhas_bottom_widget",
        ]

        for widget_name in reusable_widget_names:
            widget = getattr(self, widget_name, None)
            if widget is None:
                continue
            try:
                widget.setParent(None)
            except RuntimeError:
                print(f"Aviso: widget {widget_name} ja foi removido pelo Qt.")

    def reset_media_container_constraints(self):
        self.media_container.setMinimumSize(0, 0)
        self.media_container.setMaximumSize(16777215, 16777215)
        self.media_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def init_ui(self):
        """Inicializa a interface com base no formato atual"""
        self.setWindowTitle("NeuroOn Publicidade Player")
        self.setStyleSheet("background-color: black; color: white;")
        
        # Limpa qualquer widget central existente
        old_widget = self.takeCentralWidget()
        if old_widget:
            self.detach_reusable_widgets()
            old_widget.deleteLater()

        # Cria um novo widget central
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Aplica o layout apropriado com base no formato da tela
        if self.formato_tela is None:
            self.apply_startup_layout(central_widget)
        elif self.formato_tela == 1:
            self.apply_horizontal_layout(central_widget)
        elif self.formato_tela == 3:
            self.apply_fullscreen_layout(central_widget)
        elif self.formato_tela == 4:
            if self.senhas_chamada_panel_active:
                self.apply_senhas_chamada_layout(central_widget)
            else:
                self.apply_fullscreen_layout(central_widget)
        else:
            self.apply_vertical_layout(central_widget)
        
        # Exibe em tela cheia.
        self.showMaximized()
        QTimer.singleShot(100, self.showFullScreen)

    def apply_startup_layout(self, central_widget):
        """Aplica uma tela inicial enquanto o formato real ainda nao chegou da API."""
        print("Aplicando layout inicial")
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        startup_label = QLabel("Iniciando...")
        startup_label.setAlignment(Qt.AlignCenter)
        startup_label.setStyleSheet("""
            color: white;
            background-color: black;
            font-size: 48px;
            font-weight: bold;
        """)
        main_layout.addWidget(startup_label)

    def apply_fullscreen_layout(self, central_widget):
        """Aplica o layout fullscreen (formato_tela = 3)"""
        print("Aplicando layout fullscreen")
        self.reset_media_container_constraints()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Container midia
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        center_layout.addWidget(self.media_container, 9)

        main_layout.addWidget(center_widget)
        return 3

    def apply_senhas_chamada_layout(self, central_widget):
        """Aplica o layout de chamadas (formato_tela = 4)."""
        print("Aplicando layout de chamadas")
        self.reset_media_container_constraints()
        central_widget.setStyleSheet("background-color: white;")

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        panel_width = int(self.screen_width * 0.30)
        media_width = self.screen_width - panel_width
        media_height = int(media_width * 9 / 16)

        if media_height > self.screen_height:
            media_height = self.screen_height
            media_width = int(media_height * 16 / 9)

        panel_width = self.screen_width - media_width
        self.senhas_title_font_size = max(36, min(64, int(panel_width * 0.095)))
        self.senhas_item_min_height = max(135, min(220, int(media_height * 0.18)))
        self.senhas_item_senha_font_size = max(30, min(56, int(min(panel_width * 0.085, self.senhas_item_min_height * 0.25))))
        self.senhas_item_nome_font_size = max(24, min(44, int(min(panel_width * 0.065, self.senhas_item_min_height * 0.19))))
        self.senhas_item_pessoas_font_size = max(19, min(34, int(min(panel_width * 0.052, self.senhas_item_min_height * 0.145))))
        self.senhas_title_label.setStyleSheet(f"""
            color: #111;
            font-size: {self.senhas_title_font_size}px;
            font-weight: bold;
            background-color: transparent;
        """)

        top_widget = QWidget()
        top_widget.setStyleSheet("background-color: white;")
        top_widget.setFixedHeight(media_height)
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        self.media_container.setStyleSheet("background-color: black;")
        self.media_container.setFixedSize(media_width, media_height)

        top_layout.addWidget(self.media_container, 0, Qt.AlignTop | Qt.AlignLeft)
        top_layout.addWidget(self.senhas_panel_widget, 1)

        main_layout.addWidget(top_widget, 0)

        self.senhas_bottom_widget.setMinimumHeight(0)
        self.senhas_bottom_widget.setMaximumHeight(16777215)
        self.senhas_bottom_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        bottom_available_height = max(1, self.screen_height - media_height)
        bottom_font_size = max(56, min(130, int(bottom_available_height * 0.32)))
        self.senhas_bottom_label.setStyleSheet(f"""
            color: white;
            background-color: #111827;
            font-size: {bottom_font_size}px;
            font-weight: bold;
        """)
        main_layout.addWidget(self.senhas_bottom_widget, 1)
        self.render_senhas_chamada()

    def apply_horizontal_layout(self, central_widget):
        """Aplica o layout horizontal (formato_tela = 1)"""
        print("Aplicando layout horizontal")
        self.reset_media_container_constraints()
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
        footer_widget.setStyleSheet(f"""background-color: #222;""")
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
        bottom_footer_widget.setStyleSheet(f"""background-color: #111;
                                           background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                stop: 0 #007BFF, stop: 1 white);
                                           """)
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

        #Adiciona a imagem do informtivo (100x100)
        self.info_image_label.setFixedSize(100,100)
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
        self.reset_media_container_constraints()

        # Área de vídeo no topo (mantendo proporção 16:9)
        # Calculamos a altura para manter a proporção do vídeo, cerca de 31% da tela se não me engano
        video_height = int(self.screen_width * 9/16)  # Proporção 16:9
        
        # Limitamos a altura para não ocupar mais de 40% da tela
        max_video_height = int(self.screen_height * 0.4)
        video_height = min(video_height, max_video_height)  
        
        self.media_container.setFixedHeight(video_height)
        main_layout.addWidget(self.media_container)

        # Área central para informativos
        info_widget = QWidget()
        info_widget.setStyleSheet("background-color: white; padding: 20px;")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(15)

        # Título do informativo (aviso)
        info_header = QWidget()
        info_header_layout = QHBoxLayout(info_header)
        info_header_layout.setContentsMargins(0, 0, 0, 0)
        info_header_layout.addWidget(self.condo_info_label)
        
        # Detalhes do informativo
        info_layout.addWidget(info_header)
        info_layout.addWidget(self.info_details_label)

        # Adiciona a imagem do informativo
        self.info_image_label.setFixedSize(854,480)
        info_layout.addWidget(self.info_image_label, 0, Qt.AlignCenter)

        print("Diretório atual:", os.getcwd())
        print("Caminho completo", os.path.abspath("fotos/foto.png"))

        if os.path.exists("v9_foto/fotos/foto.jpg"):
            pixmap = QPixmap("v9_foto/fotos/foto.jpg")
            self.info_image_label.setPixmap(pixmap.scaled(1920, 1080, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.info_image_label.show()
            print("Imagem encontrada")
        else:
            self.info_image_label.hide()
            print("Nao achei a imagem")
        
        # Calculamos o espaço disponível para a área de informações
        # (altura total - altura do vídeo - altura do rodapé)
        footer_height = int(self.screen_height * 0.05)
        info_height = self.screen_height - video_height - footer_height
        info_widget.setMinimumHeight(info_height)
        
        main_layout.addWidget(info_widget, 1)  # Expande para preencher o espaço disponível

        # Rodapé (5% da altura)
        footer_widget = QWidget()
        footer_widget.setFixedHeight(footer_height)
        footer_widget.setStyleSheet(f"""background-color: #222;
                                        background: qlineargradient(x1: 1, y1: 0, x2: 0, y2: 0,
                                stop: 0 #007BFF, stop: 1 white);
                                    """)
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(20, 5, 20, 5)
        footer_layout.setSpacing(15)

        # Adiciona os widgets de informação com espaçamento
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

        self.heartbeat_api_thread = HeartbeatApiThread(self)
        self.heartbeat_api_thread.error_signal.connect(self.handle_api_error)
        self.heartbeat_api_thread.start()

    def init_timers(self):
        self.informativo_rotation_timer = QTimer(self)
        self.informativo_rotation_timer.timeout.connect(self.display_next_informativo)

        self.datetime_timer = QTimer(self)
        self.datetime_timer.timeout.connect(self.update_datetime_label)
        self.datetime_timer.start(DATETIME_UPDATE_INTERVAL_MS)
        self.update_datetime_label()

        # Timer para reportar exibições pendentes
        self.report_timer = QTimer(self)
        self.report_timer.timeout.connect(self.report_counts)
        self.report_timer.start(REPORT_INTERVAL_MS)

        self.senhas_auto_scroll_timer = QTimer(self)
        self.senhas_auto_scroll_timer.timeout.connect(self.scroll_senhas_chamada_list)

    def update_formato_tela(self, formato_tela):
        """Atualiza o formato da tela e recria a interface"""
        if self.is_closing:
            return

        print(f"formato recebido: {formato_tela}")

        if formato_tela not in [1, 2, 3, 4]:
            print(f"Formato de tela inválido ignorado: {formato_tela}")
            return

        previous_formato_tela = self.formato_tela

        if previous_formato_tela == formato_tela:
            return

        self.formato_tela = formato_tela
        print(f"Alterando para formato de tela: {formato_tela}")

        if formato_tela == 4:
            self.start_senhas_chamada_thread()
        else:
            self.stop_senhas_chamada_thread()
            self.senhas_chamada = []
            self.senhas_chamada_empty_since = None
            self.senhas_chamada_panel_active = False
            if hasattr(self, 'senhas_auto_scroll_timer'):
                self.senhas_auto_scroll_timer.stop()

        current_media_id = self.last_played_media_id
        was_playing_video = self.video_widget.isVisible()

        if hasattr(self, 'player') and self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()

        self.init_ui()

        if previous_formato_tela is None:
            if self.playlist:
                self.play_next_media()
        elif current_media_id is not None and current_media_id in self.media_data:
            self.restore_current_media_after_layout_change(was_playing_video)

    def handle_api_error(self, error_message):
        print(f"Erro de API: {error_message}")
        self.api_error_count += 1

    def update_playlist_publicidade(self, new_playlist):
        if self.is_closing:
            return

        print("Recebida playlist de publicidade atualizada.")
        self.playlist = new_playlist
        # Atualiza self.media_data com base na nova playlist
        # Mantém dados existentes e adiciona novas mídias
        current_ids = set(self.media_data.keys())
        new_ids = set(item['id_conteudo'] for item in new_playlist)

        # Remove mídias que não estão mais na playlist
        ids_to_remove = current_ids - new_ids
        for media_id in ids_to_remove:
            if media_id in self.media_data:
                 del self.media_data[media_id]

        # Verifica/baixa as mídias da nova playlist
        print("Verificando/baixando mídias de publicidade...")
        for item in new_playlist:
            id_conteudo = item['id_conteudo']
            url = item['url']
            
            # Se é uma mídia nova, inicializa os dados locais
            if id_conteudo not in self.media_data:
                self.media_data[id_conteudo] = {'url': url, 'path': None}
            
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
        if self.formato_tela is not None and self.current_playlist_index == -1:
            self.play_next_media()

    def update_informativos(self, new_informativos):
        if self.is_closing:
            return

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
        if self.is_closing:
            return

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
        if self.is_closing:
            return

        now = QDateTime.currentDateTime()
        formatted_datetime = now.toString("dd/MM/yyyy HH:mm:ss")
        self.datetime_label.setText(formatted_datetime)

    def start_senhas_chamada_thread(self):
        if self.senhas_chamada_api_thread is not None and self.senhas_chamada_api_thread.isRunning():
            return

        self.senhas_chamada_api_thread = SenhasChamadaApiThread(self)
        self.senhas_chamada_api_thread.senhas_updated.connect(self.update_senhas_chamada)
        self.senhas_chamada_api_thread.error_signal.connect(self.handle_api_error)
        self.senhas_chamada_api_thread.start()

    def stop_senhas_chamada_thread(self):
        if self.senhas_chamada_api_thread is None:
            return

        self.senhas_chamada_api_thread.stop()
        self.senhas_chamada_api_thread = None

    def format_cliente_nome_chamada(self, cliente_nome):
        partes_nome = [parte for parte in str(cliente_nome or "").split() if parte]

        if len(partes_nome) <= 2:
            return " ".join(partes_nome)

        abreviacoes = [f"{parte[0].upper()}." for parte in partes_nome[1:-1] if parte]
        return " ".join([partes_nome[0], *abreviacoes, partes_nome[-1]])

    def format_qtd_pessoas_chamada(self, qtd_pessoas):
        if qtd_pessoas in (None, ""):
            return ""

        return f"{qtd_pessoas} pessoa(s)"

    def format_senha_chamada_text(self, senha, destaque=False):
        senha_codigo = str(senha.get("senha", "--"))
        cliente_nome = self.format_cliente_nome_chamada(senha.get("cliente_nome", ""))

        if destaque:
            partes = [f"SENHA {senha_codigo}"]
            if cliente_nome:
                partes.append(cliente_nome)
            return "  |  ".join(partes)

        linhas = [f"SENHA {senha_codigo}"]
        if cliente_nome:
            linhas.append(cliente_nome)
        return "\n".join(linhas)

    def create_senha_chamada_item_widget(self, senha):
        item_widget = QWidget()
        item_widget.setMinimumHeight(self.senhas_item_min_height)
        item_widget.setStyleSheet("""
            QWidget {
                background-color: #f1f5f9;
                border: 1px solid #d9e2ec;
                border-radius: 6px;
            }
        """)

        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(0)

        item_padding = max(10, int(self.senhas_item_min_height * 0.08))
        details_horizontal_margin = max(14, int(self.senhas_item_min_height * 0.10))
        details_vertical_margin = max(8, int(self.senhas_item_min_height * 0.06))
        details_spacing = max(4, int(self.senhas_item_min_height * 0.04))

        senha_widget = QWidget()
        senha_widget.setStyleSheet("""
            background-color: #111827;
            border: none;
            border-radius: 6px;
        """)
        senha_layout = QVBoxLayout(senha_widget)
        senha_layout.setContentsMargins(item_padding, item_padding, item_padding, item_padding)
        senha_layout.setSpacing(max(2, int(self.senhas_item_min_height * 0.02)))

        senha_title_label = QLabel("SENHA")
        senha_title_label.setAlignment(Qt.AlignCenter | Qt.AlignBottom)
        senha_title_label.setStyleSheet(f"""
            color: white;
            background-color: transparent;
            border: none;
            font-size: {self.senhas_item_senha_font_size}px;
            font-weight: bold;
        """)

        senha_codigo = str(senha.get("senha", "--"))
        senha_codigo_label = ElidedLabel(senha_codigo)
        senha_codigo_label.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        senha_codigo_label.setStyleSheet(f"""
            color: white;
            background-color: transparent;
            border: none;
            font-size: {self.senhas_item_senha_font_size}px;
            font-weight: bold;
        """)

        senha_layout.addWidget(senha_title_label, 1)
        senha_layout.addWidget(senha_codigo_label, 1)
        item_layout.addWidget(senha_widget, 1)

        details_widget = QWidget()
        details_widget.setStyleSheet("background-color: transparent; border: none;")
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(
            details_horizontal_margin,
            details_vertical_margin,
            details_horizontal_margin,
            details_vertical_margin,
        )
        details_layout.setSpacing(details_spacing)

        nome_label = ElidedLabel(self.format_cliente_nome_chamada(senha.get("cliente_nome", "")))
        nome_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        nome_label.setStyleSheet(f"""
            color: #111827;
            background-color: transparent;
            border: none;
            font-size: {self.senhas_item_nome_font_size}px;
            font-weight: bold;
        """)

        pessoas_label = ElidedLabel(self.format_qtd_pessoas_chamada(senha.get("qtd_pessoas", "")))
        pessoas_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        pessoas_label.setStyleSheet(f"""
            color: #475569;
            background-color: transparent;
            border: none;
            font-size: {self.senhas_item_pessoas_font_size}px;
            font-weight: bold;
        """)

        details_layout.addWidget(nome_label, 1)
        details_layout.addWidget(pessoas_label, 1)
        item_layout.addWidget(details_widget, 1)

        return item_widget

    def render_senhas_chamada(self):
        while self.senhas_list_layout.count():
            item = self.senhas_list_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        if self.senhas_chamada:
            for senha in self.senhas_chamada:
                self.senhas_list_layout.addWidget(self.create_senha_chamada_item_widget(senha))
        else:
            empty_label = QLabel("Aguarde sua senha ser chamada")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setWordWrap(True)
            empty_label.setStyleSheet(f"""
                color: #475569;
                background-color: transparent;
                border: none;
                font-size: {self.senhas_item_nome_font_size}px;
                font-weight: bold;
            """)
            self.senhas_list_layout.addWidget(empty_label, 1)

        self.senhas_list_layout.addStretch(1)

        if self.senhas_chamada:
            self.senhas_bottom_label.setText(self.format_senha_chamada_text(self.senhas_chamada[0], destaque=True))
        else:
            self.senhas_bottom_label.setText("Aguarde sua senha ser chamada")

        QTimer.singleShot(0, self.update_senhas_auto_scroll)

    def update_senhas_auto_scroll(self):
        if not hasattr(self, 'senhas_auto_scroll_timer'):
            return

        scroll_bar = self.senhas_scroll_area.verticalScrollBar()

        if self.formato_tela == 4 and self.senhas_chamada_panel_active and scroll_bar.maximum() > 0:
            if not self.senhas_auto_scroll_timer.isActive():
                self.senhas_scroll_direction = 1
                self.senhas_auto_scroll_timer.start(45)
        else:
            self.senhas_auto_scroll_timer.stop()
            scroll_bar.setValue(0)

    def scroll_senhas_chamada_list(self):
        scroll_bar = self.senhas_scroll_area.verticalScrollBar()
        maximum = scroll_bar.maximum()

        if maximum <= 0:
            self.senhas_auto_scroll_timer.stop()
            return

        current_value = scroll_bar.value()

        if current_value >= maximum:
            self.senhas_scroll_direction = -1
        elif current_value <= 0:
            self.senhas_scroll_direction = 1

        scroll_bar.setValue(current_value + self.senhas_scroll_direction)

    def restore_current_media_after_layout_change(self, was_playing_video=None):
        current_media_id = self.last_played_media_id

        if current_media_id is None or current_media_id not in self.media_data:
            return

        current_media_path = self.media_data[current_media_id].get('path')

        if not current_media_path:
            return

        if was_playing_video is None:
            was_playing_video = current_media_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))

        if was_playing_video:
            self.play_video(current_media_path)
        else:
            self.show_image(current_media_path)

    def update_senhas_chamada(self, new_senhas, request_ok=True):
        if self.is_closing:
            return

        if self.formato_tela != 4:
            return

        now_monotonic = time.monotonic()

        if new_senhas:
            senhas_changed = new_senhas != self.senhas_chamada
            previous_senhas_keys = {senha_chamada_key(item) for item in self.senhas_chamada}
            senhas_para_audio = [
                item
                for item in new_senhas
                if senha_chamada_key(item) not in previous_senhas_keys
            ]

            for senha in senhas_para_audio:
                self.senha_speech_manager.enqueue_senha(senha)
            self.senhas_chamada = new_senhas
            self.senhas_chamada_empty_since = None
            layout_changed = False

            if not self.senhas_chamada_panel_active:
                print("Senhas recebidas. Exibindo painel de chamadas.")
                self.senhas_chamada_panel_active = True
                layout_changed = True
                was_playing_video = self.video_widget.isVisible()
                self.init_ui()
                self.restore_current_media_after_layout_change(was_playing_video)

            if senhas_changed and not layout_changed:
                self.render_senhas_chamada()
            return

        if request_ok and self.senhas_chamada:
            print("API de Senhas retornou lista vazia. Limpando chamadas exibidas.")
            self.senhas_chamada = []
            if self.senhas_chamada_panel_active:
                self.render_senhas_chamada()

        if self.senhas_chamada_empty_since is None:
            self.senhas_chamada_empty_since = now_monotonic

        empty_elapsed_ms = (now_monotonic - self.senhas_chamada_empty_since) * 1000

        if self.senhas_chamada_panel_active and empty_elapsed_ms >= SENHAS_CHAMADA_FULLSCREEN_TIMEOUT_MS:
            print("Sem senhas por 10 minutos. Voltando ao fullscreen.")
            self.senhas_chamada = []
            self.senhas_chamada_panel_active = False
            self.update_senhas_auto_scroll()
            was_playing_video = self.video_widget.isVisible()
            self.init_ui()
            self.restore_current_media_after_layout_change(was_playing_video)

    def play_next_media(self):
        if self.is_closing:
            return

        if self.formato_tela is None:
            print("Formato de tela ainda nao definido. Aguardando API para iniciar midias...")
            return

        if not self.playlist:
            print("Playlist vazia. Aguardando atualização...")
            return
        
        for _ in range(len(self.playlist)):
            self.current_playlist_index = (self.current_playlist_index + 1) % len(self.playlist)
            item = self.playlist[self.current_playlist_index]
            id_conteudo = item['id_conteudo']

            if id_conteudo not in self.media_data or not self.media_data[id_conteudo]['path']:
                print(f"Mídia não encontrada localmente: {item['url']}")
                continue

            local_path = self.media_data[id_conteudo]['path']
            self.last_played_media_id = id_conteudo  # Armazena o ID da mídia atual

            if local_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                self.play_video(local_path)
                return
            if local_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                self.show_image(local_path)
                return

            print(f"Formato de arquivo não suportado: {local_path}")

        print("Nenhuma mídia local válida disponível para reproduzir.")

    def play_video(self, video_path):
        print(f"Reproduzindo vídeo: {video_path}")
        self.current_image_pixmap = None
        self.image_label.hide()
        self.video_widget.show()
        
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(video_path)))
        self.player.play()

    def update_image_pixmap(self):
        if self.current_image_pixmap is None or self.current_image_pixmap.isNull():
            return

        target_size = self.image_label.size()

        if target_size.width() <= 0 or target_size.height() <= 0:
            target_size = self.media_container.size()

        if target_size.width() <= 0 or target_size.height() <= 0:
            return

        scaled_pixmap = self.current_image_pixmap.scaled(
            target_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)

    def show_image(self, image_path):
        print(f"Exibindo imagem: {image_path}")
        self.video_widget.hide()
        
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.current_image_pixmap = pixmap
            self.image_label.show()
            QTimer.singleShot(0, self.update_image_pixmap)
            
            # Configura o timer para avançar após o tempo definido
            self.playback_timer.start(IMAGE_DISPLAY_TIME_MS)
        else:
            self.current_image_pixmap = None
            print(f"Erro ao carregar imagem: {image_path}")
            self.play_next_media()  # Pula para o próximo

    def media_status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.finish_current_media()

    def finish_current_media(self):
        if self.is_closing:
            return

        # Registra uma exibição individual da mídia que acabou de ser exibida.
        if self.last_played_media_id is not None and self.last_played_media_id in self.media_data:
            exibido_em = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.pending_exibicoes.append({
                'id_conteudo': self.last_played_media_id,
                'exibido_em': exibido_em
            })
            print(f"Exibição pendente registrada para mídia ID {self.last_played_media_id} em {exibido_em}.")
        
        # Avança para a próxima mídia
        self.play_next_media()

    def report_counts(self, force=False):
        """Envia as exibições individuais pendentes para a API."""
        if self.is_closing and not force:
            return

        if not self.pending_exibicoes:
            print("Nenhuma exibição pendente para envio.")
            return

        exibicoes_to_send = self.pending_exibicoes[:MAX_EXIBICOES_INSERT_REQUESTS_PER_REPORT]
        unsent_exibicoes = self.pending_exibicoes[MAX_EXIBICOES_INSERT_REQUESTS_PER_REPORT:]
        failed_exibicoes = []

        print(
            f"Enviando {len(exibicoes_to_send)} de {len(self.pending_exibicoes)} "
            "exibição(ões) pendente(s)..."
        )

        failed_count = 0

        for exibicao in exibicoes_to_send:
            success = self.send_exibicao_to_api(exibicao)

            if not success:
                failed_exibicoes.append(exibicao)
                failed_count += 1

        sent_count = len(exibicoes_to_send) - failed_count
        self.pending_exibicoes = failed_exibicoes + unsent_exibicoes
        print(f"Exibições enviadas: {sent_count}. Pendentes: {len(self.pending_exibicoes)}.")

    def send_exibicao_to_api(self, exibicao):
        """Envia uma exibição individual para a API e retorna True se bem-sucedido."""
        try:
            params = {
                'id_local': ID_LOCAL,
                'id_conteudo': exibicao['id_conteudo'],
                'exibido_em': exibicao['exibido_em']
            }
            print(f"Enviando exibição para API: {params}")
            
            response = requests.get(API_INSERT_EXIBICOES_URL, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if isinstance(result, dict) and 'success' in result:
                print(f"Exibição enviada com sucesso para mídia ID {exibicao['id_conteudo']}")
                return True
            else:
                print(f"Resposta inesperada da API de exibição: {result}")
                return False
                
        except Exception as e:
            print(f"Erro ao enviar exibição para mídia ID {exibicao.get('id_conteudo')}: {e}")
            return False

    def handle_player_error(self, error):
        if self.is_closing:
            return

        print(f"Erro no player: {error}")
        self.play_next_media()  # Tenta a próxima mídia

    def close_from_q(self):
        if self.is_closing:
            return

        self.is_closing = True
        print("Tecla Q pressionada. Encerrando aplicação...")
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q:
            self.close_from_q()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.is_closing = True
        print("Encerrando aplicação...")

        for timer_name in [
            'playback_timer',
            'informativo_rotation_timer',
            'datetime_timer',
            'report_timer',
            'senhas_auto_scroll_timer',
        ]:
            timer = getattr(self, timer_name, None)
            if timer is not None:
                timer.stop()

        if hasattr(self, 'player'):
            self.player.stop()
        
        # Tenta enviar exibições finais
        print("Enviando exibições finais...")
        self.report_counts(force=True)
        
        # Para as threads
        if hasattr(self, 'publicidade_api_thread'):
            self.publicidade_api_thread.stop()
        if hasattr(self, 'informativo_api_thread'):
            self.informativo_api_thread.stop()
        if hasattr(self, 'posicao_tela_api_thread'):
            self.posicao_tela_api_thread.stop()
        if hasattr(self, 'heartbeat_api_thread'):
            self.heartbeat_api_thread.stop()
        if hasattr(self, 'senhas_chamada_api_thread') and self.senhas_chamada_api_thread is not None:
            self.senhas_chamada_api_thread.stop()
        if hasattr(self, 'senha_speech_manager') and self.senha_speech_manager is not None:
            self.senha_speech_manager.stop()
        if hasattr(self, 'configuracoes_api_thread') and self.configuracoes_api_thread is not None:
            self.configuracoes_api_thread.stop()
            
        # Aceita o evento de fechamento
        event.accept()

# --- Ponto de Entrada da Aplicação ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = PublicidadePlayer()
    sys.exit(app.exec_())
