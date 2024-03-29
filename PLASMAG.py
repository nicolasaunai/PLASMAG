import sys
from PyQt6.QtWidgets import QApplication
import json
from src.view.gui import MainGUI

if __name__ == "__main__":
    app = QApplication(sys.argv)

    config_dict = {"number_of_plots": 2}


    window = MainGUI(config_dict=config_dict)
    window.show()
    sys.exit(app.exec())
