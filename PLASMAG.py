import sys
from PyQt6.QtWidgets import QApplication

from src.view.gui import MainGUI

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainGUI()
    window.show()
    sys.exit(app.exec())
