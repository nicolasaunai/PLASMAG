import sys
from PyQt5.QtWidgets import QApplication

from src.view.gui_v4_thread_validators import MainGUI

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainGUI()
    window.show()
    sys.exit(app.exec())
