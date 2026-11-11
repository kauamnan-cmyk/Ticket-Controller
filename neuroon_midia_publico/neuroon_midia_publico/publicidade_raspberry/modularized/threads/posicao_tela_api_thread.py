import requests
from PyQt5.QtCore import QThread, pyqtSignal
from config.constants import API_POSICAO_TELA_URL, API_POSICAO_TELA_CHECK_INTERVAL_MS

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


