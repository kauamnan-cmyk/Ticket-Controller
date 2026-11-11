import os

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
# Ajuste para que MEDIA_DIR e ICON_DIR estejam no diretório raiz do projeto
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
MEDIA_DIR = os.path.join(PROJECT_ROOT, "midias")
ICON_DIR = os.path.join(PROJECT_ROOT, "icons") # Caminho para ícones

# --- Intervalos e Tempos ---
API_PUBLICIDADE_CHECK_INTERVAL_MS = 10000  # 10 segundos
API_INFORMATIVO_CHECK_INTERVAL_MS = 300000 # 5 minutos
API_POSICAO_TELA_CHECK_INTERVAL_MS = 60000 # 1 minutos
IMAGE_DISPLAY_TIME_MS = 10000 # 10 segundos
INFORMATIVO_DISPLAY_TIME_MS = 120000 # 2 minutos
DATETIME_UPDATE_INTERVAL_MS = 1000 # 1 segundo
# Intervalo para reportar contagem de exibições: 1 minuto
REPORT_INTERVAL_MS = 6000000 # 1 * 60 * 1000 ms

# --- Tamanhos de Fonte em Pixels ---
FONT_SIZE_TITULO = 24
FONT_SIZE_SUBTITULO = 18
FONT_SIZE_TEXTO = 14
FONT_SIZE_AVISO = 24 # Tamanho da fonte para o informativo_aviso
FONT_SIZE_ICON = 20


