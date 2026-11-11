import sys
from PyQt5.QtWidgets import QApplication
from core.main import PublicidadePlayer

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = PublicidadePlayer()
    sys.exit(app.exec_())


