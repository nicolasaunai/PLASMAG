import sys
import unittest
from unittest.mock import patch
import os
import json
from PyQt6.QtWidgets import QApplication

from src.view.gui import MainGUI
app = QApplication.instance() or QApplication(sys.argv)


class TestMainGUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestMainGUI, cls).setUpClass()
        cls.real_data_path = os.path.join(os.getcwd(), 'test_data', 'real_data.json')

    def setUp(self):
        self.gui = MainGUI()

    @patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName')
    def test_export_parameters_to_json(self, mock_save_dialog):
        """Test exporting parameters to a JSON file using real data."""
        # Use the real data file path for the mock dialog return value
        mock_save_dialog.return_value = (self.real_data_path, 'JSON Files (*.json)')

        with open(self.real_data_path, 'r') as file:
            self.gui.input_parameters = json.load(file)

        # Perform export
        self.gui.export_parameters_to_json()

        self.assertTrue(os.path.exists(self.real_data_path))
        with open(self.real_data_path, 'r') as exported_file:
            data = json.load(exported_file)
            self.assertEqual(data, self.gui.input_parameters)

    @patch('PyQt6.QtWidgets.QFileDialog.getOpenFileName')
    def test_import_parameters_from_json(self, mock_open_dialog):
        """Test importing parameters from a JSON file using real data."""
        # Mock the file dialog to select the real data file
        mock_open_dialog.return_value = (self.real_data_path, 'JSON Files (*.json)')

        # Perform import
        self.gui.import_parameters_from_json()

        # Verify the imported parameters match the expected real data
        with open(self.real_data_path, 'r') as file:
            expected_data = json.load(file)
        self.assertEqual(self.gui.input_parameters, expected_data)


if __name__ == '__main__':
    unittest.main()
