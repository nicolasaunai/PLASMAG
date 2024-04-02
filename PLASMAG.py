import sys
from PyQt6.QtWidgets import QApplication
import json
from src.view.gui import MainGUI

if __name__ == "__main__":
    app = QApplication(sys.argv)

    with open("config.json", "r") as f:
        config_dict = json.load(f)



    window = MainGUI(config_dict=config_dict)
    window.show()
    sys.exit(app.exec())
