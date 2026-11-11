import os
import requests
from PyQt5.QtCore import QUrl, QThread, pyqtSignal
from config.constants import API_PUBLICIDADE_URL, API_PUBLICIDADE_CHECK_INTERVAL_MS

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


