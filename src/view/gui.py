"""
src/view/gui.py
PLASMAG GUI module
"""
import copy
import csv
import importlib
import json
import os
import sys
import time
import warnings
import webbrowser
from datetime import datetime

from pint import UnitRegistry
import numpy as np
import pandas as pd

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPoint, QEvent, QUrl
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QLabel, \
    QGridLayout, QSlider, QCheckBox, QHBoxLayout, QSpacerItem, QSizePolicy, QComboBox, QScrollArea, QFileDialog, \
    QMessageBox, QInputDialog, QTabWidget, QToolTip, QGroupBox, QSplitter, QDialog, QProgressDialog
from PyQt6.QtGui import QPixmap, QDesktopServices
from PyQt6.QtWidgets import QSplashScreen, QApplication

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from qtrangeslider import QRangeSlider
from src.controler.controller import CalculationController, STRATEGY_MAP

from src.model.visualisation.create_tree import create_tree, add_title_description

ureg: UnitRegistry = UnitRegistry()


class ResizableImageLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.original_pixmap = pixmap
        self.unresized_pixmap = pixmap
        self.setScaledContents(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.original_pixmap:
            size = self.size()
            scaled_size = self.original_pixmap.size()
            scaled_size.scale(size, Qt.AspectRatioMode.KeepAspectRatio)
            if not self.pixmap() or self.pixmap().size() != scaled_size:
                self.setPixmap(self.original_pixmap.scaled(scaled_size, Qt.AspectRatioMode.KeepAspectRatio,
                                                           Qt.TransformationMode.SmoothTransformation))

    def mousePressEvent(self, event):
        self.clicked.emit()

    def setPixmap(self, pixmap, unreized_pixmap=None):
        self.original_pixmap = pixmap
        if unreized_pixmap:
            self.unresized_pixmap = unreized_pixmap
        super().setPixmap(pixmap)

    def get_pixmap(self):
        return self.unresized_pixmap


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About PLASMAG")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        label = QLabel(f"""
PLASMAG is a simulation software 
specifically designed for space magnetometers. 
At its core, PLASMAG serves as a comprehensive tool 
for the parameters adjustment. 

Author: CNRS-LPP, France, Maxime Ronceray, Malik Mansour,
Claire Revillet, 
Version: 1.1.0

        """)
        layout.addWidget(label)

        # Ajoutez d'autres widgets selon vos besoins, par exemple un lien vers la documentation.
        doc_button = QPushButton("Open Documentation")
        doc_button.clicked.connect(self.open_documentation)
        layout.addWidget(doc_button)

        self.setLayout(layout)

    def open_documentation(self):
        QDesktopServices.openUrl(QUrl("https://forge-osuc.cnrs-orleans.fr/projects/plasmag/wiki/Wiki"))


class EnlargedImageDialog(QDialog):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("Enlarged ASIC Image")

        self.setModal(True)

        screen_size = QApplication.primaryScreen().size()
        max_width = screen_size.width() * 0.5
        max_height = screen_size.height() * 0.5

        scaled_pixmap = pixmap.scaled(max_width, max_height, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)

        layout = QVBoxLayout()
        self.closeButton = QPushButton("×")
        self.closeButton.setFixedSize(30, 30)
        self.closeButton.setStyleSheet(
            "QPushButton { font-size: 50px; border: none; color: black; } QPushButton:hover { color: red; }")
        self.closeButton.clicked.connect(self.close)
        layout.addWidget(self.closeButton, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        image_label = QLabel()
        image_label.setPixmap(scaled_pixmap)
        layout.addWidget(image_label)
        self.setLayout(layout)
        self.resize(
            scaled_pixmap.size())

        QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            self.accept()
            QApplication.instance().removeEventFilter(self)
            return True
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        # Ensure the event filter is removed when dialog closes
        QApplication.instance().removeEventFilter(self)
        super().closeEvent(event)


def convert_unit(value, from_unit, to_unit):
    """
    Converts the given value from one unit to another using Pint.
    Args:
        value (float): The value to convert.
        from_unit (str): The unit of the input value.
        to_unit (str): The target unit for the conversion.
    Returns:
        float: The converted value.
    """
    if from_unit and to_unit:
        return (value * ureg(from_unit)).to(ureg(to_unit)).magnitude
    return value


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(ClickableLabel, self).__init__(*args, **kwargs)

    def mousePressEvent(self, event):
        self.clicked.emit()


class ToolTipLineEdit(QLineEdit):
    def __init__(self, default_value="", tooltip_text="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.defaultValue = default_value
        self.tooltip_text = tooltip_text
        self.setText(self.defaultValue)
        self.textChanged.connect(self.showToolTip)
        self.focusInEvent = self.showCustomToolTip
        self.setPlaceholderText(f"Default: {default_value}")

    def showCustomToolTip(self, event):
        super().focusInEvent(event)
        self.showToolTip()

    def showToolTip(self):
        QToolTip.showText(self.mapToGlobal(QPoint(0, 0)), self.tooltip_text, self)


class CalculationThread(QThread):
    """
    A QThread subclass for running calculations in a separate thread to avoid blocking the main GUI thread.
    """
    calculation_finished = pyqtSignal(object)
    calculation_failed = pyqtSignal(str)

    def __init__(self, controller, params_dict=None):
        """
        Initializes the CalculationThread with the given controller and parameters dictionary.
        :param controller:
        :param params_dict:
        """
        super().__init__()
        self.controller = controller
        self.params_dict = params_dict

    def run(self):
        """
        Runs the calculation process in a separate thread.
        :return:
        """
        try:
            calculation_result = self.controller.update_parameters(self.params_dict)
            self.calculation_finished.emit(calculation_result)  # Emit result
        except Exception as error:
            self.calculation_failed.emit(str(error))  # Emit error message


class MplCanvas(FigureCanvas):
    """
    A custom matplotlib canvas for displaying plots in the GUI.
    """

    def __init__(self):
        fig = Figure(figsize=(5, 4), dpi=100)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)

    def add_curve(self, x_data, y_data, label=None):
        """
        Adds a curve to the plot with the given x and y data.
        :param x_data:
        :param y_data:
        :param label:
        :return:
        """
        self.axes.plot(x_data, y_data, label=label)
        self.draw()


class MainGUI(QMainWindow):
    """
        The MainGUI class is responsible for creating and managing the graphical user interface of the
        PLASMAG application.
        It sets up input fields for parameters, sliders for adjustments, a plotting area for visualization, and
         initiates calculations.

        Attributes:
            currently_selected_input (tuple): A tuple containing the currently selected QLineEdit and its parameter
             name.
            central_widget (QWidget): The central widget of the QMainWindow.
            main_layout (QVBoxLayout): The main layout containing all widgets.
            inputs (dict): Dictionary mapping parameter names to their respective QLineEdit widgets.
            global_slider_coarse (QSlider): The slider for coarse adjustments of parameter values.
            global_slider_fine (QSlider): The slider for fine adjustments of parameter values.
            calculate_btn (QPushButton): The button to trigger the calculation process.
            canvas (MplCanvas): The matplotlib canvas for plotting calculation results.
            controller (CalculationController): The controller handling the calculation logic.
    """

    def __init__(self, config_dict=None):
        super().__init__()
        self.background_buttons = None
        self.config_dict = config_dict
        self.slider_precision = None
        self.plot_layout = None
        self.calculate_btn = None
        self.reset_params_btn = None
        self.main_layout = None
        self.params_layout = None
        self.central_widget = None
        self.comboboxes = None
        self.checkboxes = None
        self.toolbars = None
        self.canvases = None
        self.controller = None
        self.calculation_timer = None
        self.input_parameters = None
        self.frequency_values_label = None
        self.frequency_range_slider = None
        self.global_slider_fine = None
        self.global_slider_fine_label = None
        self.global_slider_coarse = None
        self.global_slider_coarse_label = None
        self.grid_layout = None
        self.inputs = None
        self.latest_results = None
        self.background_curve_data = None
        self.reset_background_buttons = None
        self.button_states = {}
        self.saved_parameters = []
        self.block_calculation = False
        self.spice_configs = {}
        self.saved_spice_strategies = []
        self.saved_spice_parameters = []
        self.first_run = True

        self.setWindowTitle("PLASMAG")
        self.setGeometry(100, 100, 2560, 1440)  # Adjust size as needed

        self.load_default_parameters()
        self.load_spice_configs()

        self.f_start_value = self.input_parameters["misc"]['f_start']['default']
        self.f_stop_value = self.input_parameters["misc"]['f_stop']['default']

        self.currently_selected_input = None

        self.init_ui()
        self.init_menu()

        self.update_spice_parameters_ui(0)

        self.showMaximized()

        QTimer.singleShot(0, self.post_init_setup)

    def post_init_setup(self):
        index = self.spice_circuit_combo.findText(self.default_spice_circuit)
        self.spice_circuit_combo.setCurrentIndex(index)

    def show_about_dialog(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def load_spice_configs(self):
        try:
            current_dir = os.path.dirname(os.path.realpath(__file__))
            spice_config_path = os.path.join(current_dir, '..', '..', 'data', 'SPICE.json')
            spice_config_path = os.path.normpath(spice_config_path)
            with open(spice_config_path, 'r', encoding='utf-8') as file:
                self.spice_configs = json.load(file)['Circuits']
            print("SPICE configurations loaded successfully.")
        except FileNotFoundError:
            print(f"SPICE configuration file not found at {spice_config_path}.")
            self.spice_configs = {}
        except json.JSONDecodeError as e:
            print(f"Error decoding SPICE.json: {e}")
            self.spice_configs = {}

    def init_parameters_input(self):
        """
        Initializes the input fields for the parameters based on the loaded input parameters.
        Iterates over the input parameters dictionary and creates a QLabel and QLineEdit for each parameter in each
        section. The input fields are organized in a scrollable area for better visibility and usability.
        """
        self.inputs = {}

        for section_name, section_parameters in self.input_parameters.items():
            if section_name == 'SPICE' or section_name == 'SPICE_circuit':
                continue
            section_widget = QWidget()
            section_layout = QGridLayout()


            section_widget.setLayout(section_layout)
            section_layout.setSpacing(10)

            section_label = QLabel(f"<b>{section_name}</b>")
            section_label.setStyleSheet("font-weight: bold; font-size: 16px")
            section_layout.addWidget(section_label, 0, 0, 1, 2)  # Span sur 2 colonnes

            section_row = 1
            for idx, (param_name, param_attrs) in enumerate(section_parameters.items()):

                if param_name == 'f_start' or param_name == 'f_stop':
                    continue

                label = QLabel(f"{param_name}:")
                default_value = str(param_attrs['default'])
                tooltip_text = param_attrs['description']
                line_edit = ToolTipLineEdit(default_value, tooltip_text)
                line_edit.returnPressed.connect(self.calculate)
                self.inputs[param_name] = line_edit

                line_edit.textChanged.connect(lambda _, le=line_edit, param=param_name: self.validate_input(le, param))

                col = idx % 2 * 2
                if idx % 2 == 0 and idx > 0:
                    section_row += 1

                section_layout.addWidget(label, section_row, col)
                section_layout.addWidget(line_edit, section_row, col + 1)

            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setWidget(section_widget)
            scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding,
                                      QSizePolicy.Policy.Preferred)

            self.params_layout.addWidget(scroll_area)

    def init_sliders(self):
        """
        Initializes the global sliders for frequency, coarse and fine adjustments of parameter values.
        The sliders are set up with appropriate ranges and connected to the update methods for parameter values.

        """
        # Create a grid layout
        self.grid_layout = QGridLayout()

        # Add the label and the coarse global slider
        self.global_slider_coarse_label = QLabel("Coarse Adjustment")
        self.grid_layout.addWidget(self.global_slider_coarse_label, 0, 0)
        self.global_slider_coarse = QSlider(Qt.Orientation.Horizontal)
        self.global_slider_coarse.valueChanged.connect(lambda: self.update_selected_input_value('coarse'))
        self.grid_layout.addWidget(self.global_slider_coarse, 0, 1)

        # Add the label and the fine global slider
        self.global_slider_fine_label = QLabel("Fine Adjustment")
        self.grid_layout.addWidget(self.global_slider_fine_label, 1, 0)
        self.global_slider_fine = QSlider(Qt.Orientation.Horizontal)
        self.global_slider_fine.valueChanged.connect(lambda: self.update_selected_input_value('fine'))
        self.grid_layout.addWidget(self.global_slider_fine, 1, 1)

        frequency_range_slider_label = QLabel("Frequency range :")
        self.grid_layout.addWidget(frequency_range_slider_label, 2,
                                   0)

        self.frequency_range_slider = QRangeSlider()
        self.frequency_range_slider.setOrientation(Qt.Orientation.Horizontal)
        self.frequency_range_slider.setMinimum(self.input_parameters["misc"]['f_start']['min'])
        self.frequency_range_slider.setMaximum(self.input_parameters["misc"]['f_stop']['max'])
        self.frequency_range_slider.setValue(
            (self.input_parameters["misc"]['f_start']["default"], self.input_parameters["misc"]['f_stop']["default"]))
        self.frequency_range_slider.valueChanged.connect(self.update_frequency_range)
        self.grid_layout.addWidget(self.frequency_range_slider, 2, 1)

        self.frequency_values_label = QLabel(
            f"F_start : {self.input_parameters['misc']['f_start']['default']}, "
            f"F_stop: {self.input_parameters['misc']['f_stop']['default']}")
        self.grid_layout.addWidget(self.frequency_values_label, 3, 0, 1, 2)

        # Set the spacing between elements in the grid
        self.grid_layout.setSpacing(5)

        # Add the grid layout to the main layout
        self.params_layout.addLayout(self.grid_layout)

    def load_default_parameters(self, reload=True):
        """
        Loads the default input parameters from the 'data/default.json' file.
        :return:
        """
        if reload:
            current_dir = os.path.dirname(os.path.realpath(__file__))
            if "default_file" in self.config_dict:
                json_file_path = os.path.join(current_dir, '..', '..', 'data', self.config_dict["default_file"])
            else:
                json_file_path = os.path.join(current_dir, '..', '..', 'data', 'default.json')
            json_file_path = os.path.normpath(json_file_path)

            print("Loading default parameters from: ", json_file_path)

            try:
                with open(json_file_path, 'r', encoding="utf-8") as json_file:
                    self.input_parameters = json.load(json_file)

                    try :
                        self.default_spice_circuit = self.input_parameters['SPICE_circuit']
                    except KeyError:
                        self.default_spice_circuit = "NO Circuit Selected"

                    # Remove the SPICE_circuit key from the input parameters
                    self.input_parameters.pop('SPICE_circuit', None)
            except FileNotFoundError:
                print(f"File{json_file_path} not found.")
            except json.JSONDecodeError:
                print(f"Error reading : {json_file_path}.")
        else:
            self.input_parameters = self.input_parameters
            self.default_spice_circuit = self.input_parameters['SPICE_circuit']

            # Remove the SPICE_circuit key from the input parameters
            self.input_parameters.pop('SPICE_circuit', None)

            #get the index of the default circuit in the combobox
            index = self.spice_circuit_combo.findText(self.default_spice_circuit)
            self.spice_circuit_combo.setCurrentIndex(index)




    def init_timer(self, timer_value=50):
        """
        Initializes the calculation timer with a delay of XX milliseconds.
        Used to trigger the calculation process after a delay to avoid lag during slider adjustments.
        :return:
        """
        self.calculation_timer = QTimer(self)
        self.calculation_timer.setInterval(timer_value)  # Delay in milliseconds
        self.calculation_timer.setSingleShot(True)
        self.calculation_timer.timeout.connect(self.delayed_calculate)

    def init_controller(self, backups_count=3):
        """
        Initializes the CalculationController for handling the calculation logic.
        :return:
        """
        self.controller = CalculationController(backups_count=backups_count)

        for parameter, line_edit in self.inputs.items():
            line_edit.mousePressEvent = (lambda event, le=line_edit,
                                                param=parameter: self.bind_slider_to_input(le, param))
            line_edit.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        self.slider_precision = 100

    def clear_plot_layout(self):
        while self.plot_layout.count():
            child = self.plot_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                while child.layout().count():
                    grand_child = child.layout().takeAt(0)
                    if grand_child.widget():
                        grand_child.widget().deleteLater()

    def clear_saved_results(self):
        # reset all buttons colors
        for buttons in self.all_buttons:
            for button in buttons:
                button.setStyleSheet("background-color: none")
        self.controller.clear_calculation_results()

        for i in range(len(self.saved_parameters)):
            self.saved_parameters[i] = None
            self.button_states[i] = 0

        self.plot_results(self.latest_results)

    def init_canvas(self, number_of_plots=3, number_of_buttons=3):
        """
        Initializes the matplotlib canvas for plotting the calculation results.
        Creates three separate canvases for different plots and adds them to the main layout.
        :return:
        """
        self.clear_plot_layout()

        self.canvases = [MplCanvas() for _ in range(number_of_plots)]
        self.toolbars = []
        self.checkboxes = []
        self.comboboxes = []
        self.background_buttons = []
        self.background_curve_data = [None] * number_of_plots
        self.reset_background_buttons = []
        self.all_buttons = []

        buttons_labels = [str(i) for i in range(1, number_of_buttons + 1)]
        btn_list = []

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(0)

        btn_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        for label in buttons_labels:
            btn1 = QPushButton(label)
            btn1.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
            btn1.setMaximumHeight(40)
            btn_list.append(btn1)

        btnC = QPushButton("Clear")
        btnC.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        btnC.clicked.connect(lambda _: self.clear_saved_results())
        btnC.setMaximumHeight(40)
        btn_list.append(btnC)

        # Add the buttons to the layout
        for btn in btn_list:
            btn_layout.addWidget(btn)

        for index, btn in enumerate(btn_list[:-1]):
            btn.clicked.connect(lambda _, b=btn, i=index: self.save_results(i, b))
            self.button_states[index] = 0
            self.saved_parameters.append(None)

        btn_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        btn_layout.setContentsMargins(0, 0, 0, 0)

        self.plot_layout.addLayout(btn_layout)
        self.all_buttons.append(btn_list)

        for i, canvas in enumerate(self.canvases):
            canvas_layout = QVBoxLayout()

            top_layout = QHBoxLayout()
            canvas_layout.addLayout(top_layout)

            left_spacer = QSpacerItem(1, 1, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
            top_layout.addSpacerItem(left_spacer)

            toolbar = NavigationToolbar(canvas, self)
            self.toolbars.append(toolbar)

            checkbox = QCheckBox("Show Old Curve")
            self.checkboxes.append(checkbox)
            checkbox.stateChanged.connect(self.update_plot)

            combo_box = QComboBox()
            combo_box.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
            combo_box.currentIndexChanged.connect(self.update_plot)
            self.comboboxes.append(combo_box)

            background_button = QPushButton("Load Background curve")
            self.background_buttons.append(background_button)
            background_button.clicked.connect(lambda _, idx=i: self.load_background_curve(idx))

            reset_background_button = QPushButton("Reset Background curve")
            self.reset_background_buttons.append(reset_background_button)
            reset_background_button.clicked.connect(lambda _, idx=i: self.reset_background_curve(idx))

            top_layout.addWidget(toolbar)
            top_layout.addWidget(checkbox)

            top_layout.addWidget(combo_box)
            top_layout.addWidget(background_button)
            top_layout.addWidget(reset_background_button)

            canvas_layout.addWidget(canvas)

            left_spacer = QSpacerItem(1, 1, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
            top_layout.addSpacerItem(left_spacer)

            self.plot_layout.addLayout(canvas_layout)

    def show_enlarged_image(self, pixmap):
        dialog = EnlargedImageDialog(pixmap, self)
        QApplication.instance().installEventFilter(dialog)
        dialog.exec()
        QApplication.instance().removeEventFilter(dialog)

    def init_spice_settings(self):
        spice_group_box = QGroupBox("SPICE")
        spice_layout = QVBoxLayout()

        self.toggle_spice_button = QPushButton("+")
        self.toggle_spice_button.setFixedWidth(30)
        self.toggle_spice_button.clicked.connect(self.toggle_spice_visibility)
        spice_layout.addWidget(self.toggle_spice_button)

        self.spice_contents = QWidget()
        spice_contents_layout = QVBoxLayout(self.spice_contents)
        self.spice_circuit_combo = QComboBox()
        self.spice_circuit_combo.addItems(self.spice_configs.keys())
        self.spice_circuit_combo.currentIndexChanged.connect(self.update_spice_parameters_ui)
        spice_contents_layout.addWidget(self.spice_circuit_combo)

        # Create a sub-layout for parameters only
        self.spice_params_layout = QGridLayout()
        spice_contents_layout.addLayout(self.spice_params_layout)

        print("Init spice settings")
        print(self.spice_configs)

        print(self.input_parameters)
        row = 0  # Initialize row counter
        if 'SPICE' in self.input_parameters:
            spice_params = self.input_parameters['SPICE']
            for param_name, param_info in spice_params.items():
                label = QLabel(f"{param_name}:")
                default_value = str(param_info['default'])
                tooltip_text = param_info.get('description', '')
                line_edit = ToolTipLineEdit(default_value, tooltip_text)
                line_edit.returnPressed.connect(self.calculate)
                self.inputs[param_name] = line_edit

                line_edit.textChanged.connect(lambda _, le=line_edit, param=param_name: self.validate_input(le, param))

                self.spice_params_layout.addWidget(label, row, 0)  # Add label to the grid
                self.spice_params_layout.addWidget(line_edit, row, 1)  # Add line edit next to label
                row += 1

        self.circuit_image_label = ResizableImageLabel(QPixmap("ASIC_image_1.png"))
        self.circuit_image_label.clicked.connect(
            lambda: self.show_enlarged_image(self.circuit_image_label.get_pixmap()))
        spice_contents_layout.addWidget(self.circuit_image_label)

        self.spice_contents.setHidden(True)
        spice_layout.addWidget(self.spice_contents)
        spice_group_box.setLayout(spice_layout)

        return spice_group_box

    def update_spice_parameters_ui(self, index):
        circuit_name = self.spice_circuit_combo.itemText(index)  # Get selected circuit name
        self.merge_spice_parameters(circuit_name)
        circuit_config = self.spice_configs[circuit_name]  # Get the configuration for the selected circuit
        self.saved_circuit_name = circuit_name  # Store the selected circuit name

        if not self.first_run:
            strategy = circuit_config.get('strategies', None)
            num_strategies = len(strategy) if strategy else 0
            progress_dialog = QProgressDialog("Loading strategies...", "Cancel", 0, num_strategies, self)
            progress_dialog.setModal(True)
            progress_dialog.setMinimumDuration(0)
            progress_value = 0
            QApplication.processEvents()

        if len(self.saved_spice_parameters) > 0:
            self.saved_spice_strategies += self.saved_spice_parameters
            print(self.saved_spice_strategies)
            self.saved_spice_parameters = []

        # get the "current" spice strategies
        if len(self.saved_spice_strategies) > 0:
            self.controller.delete_spice_nodes(self.saved_spice_strategies)
            self.saved_spice_strategies = []
            print(self.controller.engine.nodes)

        for i in reversed(range(self.spice_params_layout.count())):
            widget = self.spice_params_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
                if widget.objectName() in self.inputs:
                    del self.inputs[widget.objectName()]

        row = 0
        for param_name, param_info in circuit_config['parameters'].items():
            self.saved_spice_parameters.append(param_name)
            label = QLabel(f"{param_name}:")
            default_value = str(param_info['default'])
            tooltip_text = param_info.get('description', '')
            line_edit = ToolTipLineEdit(default_value, tooltip_text)
            line_edit.setObjectName(param_name)
            line_edit.returnPressed.connect(self.calculate)
            self.inputs[param_name] = line_edit

            line_edit.textChanged.connect(lambda _, le=line_edit, param=param_name: self.validate_input(le, param))
            line_edit.mousePressEvent = lambda event, le=line_edit, param=param_name: self.bind_slider_to_input(le,
                                                                                                                param)
            self.spice_params_layout.addWidget(label, row, 0)
            self.spice_params_layout.addWidget(line_edit, row, 1)
            row += 1

        self.reload_pixmap()

        # get the "strategy" key from the circuit configuration
        strategy = circuit_config.get('strategies', None)
        if strategy is not None:
            strategies_loaded = self.load_strategy(strategy)
            if strategies_loaded:
                for strategy_name, strategy_instance in strategies_loaded.items():
                    self.saved_spice_strategies.append(strategy_name)
                    print(f"Loaded strategy {strategy_name}")
                    print(type(strategy_instance))
                    print(strategy_instance)
                    self.update_node_strategy(strategy_name, strategy_instance)

                    if not self.first_run:
                        progress_value += 1
                        progress_dialog.setValue(progress_value)
                        QApplication.processEvents()

        if not self.first_run:
            progress_dialog.setValue(num_strategies)
            QApplication.processEvents()
            progress_dialog.close()


        self.first_run = False

        self.calculate()




    def reload_pixmap(self):
        circuit_name = self.spice_circuit_combo.currentText()
        circuit_config = self.spice_configs[circuit_name]
        image_path = "ressources" + os.sep + circuit_config['image']

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print("Failed to load image from:", image_path)
        else:
            self.circuit_image_label.setPixmap(
                pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation),
                unreized_pixmap=pixmap)
            print("Image loaded successfully from:", image_path)

    def toggle_spice_visibility(self):
        show = self.spice_contents.isHidden()
        self.spice_contents.setVisible(show)
        self.toggle_spice_button.setText("-" if show else "+")
        self.adjust_spice_splitter(show)
        self.reload_pixmap()

    def merge_spice_parameters(self, selected_circuit_name):
        if 'SPICE' not in self.input_parameters:
            self.input_parameters['SPICE'] = {}
        self.input_parameters['SPICE'].clear()

        if selected_circuit_name in self.spice_configs:
            circuit_details = self.spice_configs[selected_circuit_name]
            if 'parameters' in circuit_details:
                self.input_parameters['SPICE'].update(circuit_details['parameters'])
                print(f"Parameters for {selected_circuit_name} merged successfully.")
            else:
                print(f"No parameters found for {selected_circuit_name}.")
        else:
            print(f"{selected_circuit_name} not found in SPICE configurations.")

    def adjust_spice_splitter(self, show):
        sizes = self.main_splitter.sizes()
        if show:
            sizes[1] = self.width() * 0.2
        else:
            sizes[1] = 50

        self.main_splitter.setSizes(sizes)

    def adjust_splitter_for_spice_hidden(self):
        sizes = self.main_splitter.sizes()
        total = sum(sizes)
        new_sizes = [total - 30, 30, sizes[2]]
        self.main_splitter.setSizes(new_sizes)

    def adjust_splitter_for_spice_visible(self):
        sizes = self.main_splitter.sizes()
        total = sum(sizes)
        new_sizes = [total * 0.7, total * 0.3, sizes[2]]
        self.main_splitter.setSizes(new_sizes)

    def init_ui(self):
        """
        Initializes the graphical user interface by setting up the main layout, input fields,
        sliders, and plotting area.
        :return:
        """
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        self.init_timer()

        # Creating a QTabWidget for organizing parameters and  other tabs
        self.tabs = QTabWidget()
        self.param_tab = QWidget()  # QWidget that will contain the parameters layout as a tab
        self.strategy_tab = QWidget()  # QWidget that will contain the strategy selection layout as a tab
        self.spice_tab = QWidget()  # QWidget that will contain the spice layout as a tab
        self.optimisation_tab = QWidget()  # QWidget that will contain the optimisation layout as a tab
        self.EMC_tab = QWidget()  # QWidget that will contain the EMC layout as a tab

        self.params_layout = QVBoxLayout(self.param_tab)
        self.strategy_layout = QVBoxLayout(self.strategy_tab)
        self.spice_layout = QVBoxLayout(self.spice_tab)
        self.optimisation_layout = QVBoxLayout(self.optimisation_tab)
        self.EMC_layout = QVBoxLayout(self.EMC_tab)

        # Grid layout for parameter inputs
        self.grid_layout = QGridLayout()  # Grid layout for global sliders
        self.init_parameters_input()
        self.init_strategy_selection()
        self.init_sliders()
        self.spice_group_box = self.init_spice_settings()

        self.reset_params_btn = QPushButton('Reset Parameters')
        self.reset_params_btn.clicked.connect(lambda _: self.reset_parameters(reload=True))
        self.params_layout.addWidget(self.reset_params_btn)

        self.calculate_btn = QPushButton('Calculate')
        self.calculate_btn.clicked.connect(self.calculate)
        self.params_layout.addWidget(self.calculate_btn)

        self.tabs.addTab(self.param_tab, "Parameters")
        self.tabs.addTab(self.strategy_tab, "Strategy Selection")
        self.tabs.addTab(self.spice_tab, "Spice Simulation")
        self.tabs.addTab(self.optimisation_tab, "Optimisation")
        self.tabs.addTab(self.EMC_tab, "EMC")

        self.plot_layout = QVBoxLayout()

        # Initialize canvas based on configuration, if provided
        if self.config_dict is not None:
            try:
                self.init_canvas(self.config_dict["number_of_plots"])
            except KeyError:
                self.init_canvas(3)
        else:
            self.init_canvas()

        self.plot_widget = QWidget()
        self.plot_widget.setLayout(self.plot_layout)

        param_proportion = 2  # Default proportion for parameter layout
        plot_proportion = 4  # Default proportion for plot layout
        # Set proportions based on configuration, if available
        try:
            if self.config_dict is not None:
                param_proportion = self.config_dict["param_proportion"]
                plot_proportion = self.config_dict["plot_proportion"]
        except KeyError:
            print("Error while setting proportions")

        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.main_splitter)

        self.main_splitter.addWidget(self.tabs)
        self.main_splitter.addWidget(self.spice_group_box)
        self.main_splitter.addWidget(self.plot_widget)

        self.main_splitter.setStretchFactor(0, 3)
        self.main_splitter.setStretchFactor(1, 1)

        self.main_splitter.setStretchFactor(2, 4)

        # Initialize controllers, assuming there are as many save buttons as there are canvases
        self.init_controller(backups_count=3)

    def init_menu(self):
        """
        Initializes the menu bar with options for exporting and importing parameters.
        :return:
        """
        main_menu = self.menuBar()
        file_menu = main_menu.addMenu('&File')

        export_action = file_menu.addAction('&Export Parameters')
        export_action.triggered.connect(self.export_parameters_to_json)

        import_action = file_menu.addAction('&Import Parameters')
        import_action.triggered.connect(self.import_parameters_from_json)

        import_specific_action = file_menu.addAction('&Import Flicker Params')
        import_specific_action.triggered.connect(self.import_flicker_data_from_json)

        export_results_btn = file_menu.addAction('&Export results')
        export_results_btn.triggered.connect(self.export_results)

        options_menu = self.menuBar().addMenu('&Options')
        change_plot_count_action = options_menu.addAction('Change Plot Count')
        change_plot_count_action.triggered.connect(self.change_plot_count)

        help_menu = main_menu.addMenu('&Help')
        about_action = help_menu.addAction('&About PLASMAG')
        about_action.triggered.connect(self.show_about_dialog)

        export_dep_tree_action = help_menu.addAction('&Export Dependency Tree')
        export_dep_tree_action.triggered.connect(self.export_dependency_tree)

        display_graph_action = help_menu.addAction('Display Community Graph ')
        display_graph_action.triggered.connect(self.display_graph_community)

        display_graph_distance_action = help_menu.addAction('Display Distance Graph ')
        display_graph_distance_action.triggered.connect(self.display_graph_distance)

        display_graph_degree_action = help_menu.addAction('Display Degree Graph ')
        display_graph_degree_action.triggered.connect(self.display_graph_degree)

    def display_graph_community(self):
        self.display_graph(clustering_type="community")

    def display_graph_distance(self):
        self.display_graph(clustering_type="distance")

    def display_graph_degree(self):
        self.display_graph(clustering_type="degree")

    def display_graph(self, clustering_type="degree"):
        """
           Opens an HTML file in the default system web browser.

           Args:
               file_path (str): The path to the HTML file to open.
           """
        print("Displaying graph : " + clustering_type)
        path = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + "/output/visualisation_graph/"
        date = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")

        description = "This graph represents the structure of the dependency tree.<br>Exported with the following strategies for each node:<br><ul>"

        for node in self.controller.engine.nodes:
            node_strategy = self.controller.engine.nodes[node].get_strategy().__class__.__name__
            if node_strategy == "NoneType":
                node_strategy = "Leaf"
            description += f"<li><b>Node {node} : </b> {node_strategy}</li>"

        description += "</ul>"

        if clustering_type == "community":
            data = self.controller.engine.build_dependency_tree()
            file_title = "network_community" + date + ".html"
            title = "Community Graph - " + date
            create_tree(data, path + file_title, type="community", skip_frequency_vector=False)
            add_title_description(path + file_title, title, description)
            full_path = path + file_title
            webbrowser.open(full_path)

        elif clustering_type == "distance":
            data = self.controller.engine.build_dependency_tree()
            file_title = "network_distance" + date + ".html"
            title = "Distance Graph - " + date
            create_tree(data, path + file_title, type="distance", skip_frequency_vector=False)
            add_title_description(path + file_title, title, description)
            full_path = path + file_title
            webbrowser.open(full_path)

        elif clustering_type == "degree":
            data = self.controller.engine.build_dependency_tree()
            file_title = "network_degree" + date + ".html"
            title = "Degree Graph - " + date
            create_tree(data, path + file_title, type="degree", skip_frequency_vector=False)
            add_title_description(path + file_title, title, description)
            full_path = path + file_title
            webbrowser.open(full_path)
        else:
            QMessageBox.critical(self, "Error", "The specified clustering type is not valid.")


    def export_dependency_tree(self):
        try:
            # Get the path to save the dependency tree
            path, _ = QFileDialog.getSaveFileName(self, "Export Dependency Tree", "", "json Files (*.json)")
            print(f"Exporting dependency tree to {path}")
            dependency_tree = self.controller.engine.build_dependency_tree(path)
            QMessageBox.information(self, "Export Successful", "The dependency tree has been exported successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed",
                                 f"An error occurred while exporting the dependency tree: {str(e)}")

    def change_plot_count(self):
        num, ok = QInputDialog.getInt(self, "Change Plot Count", "Number of Plots:", min=1, max=5, step=1)
        if ok and num != len(self.canvases):
            self.update_canvas_count(num)

    def update_canvas_count(self, num_plots):
        for toolbar in self.toolbars:
            toolbar.setParent(None)
            toolbar.deleteLater()
        for button in self.background_buttons:
            button.setParent(None)
            button.deleteLater()
        for button in self.reset_background_buttons:
            button.setParent(None)
            button.deleteLater()
        for checkbox in self.checkboxes:
            checkbox.setParent(None)
            checkbox.deleteLater()
        for combobox in self.comboboxes:
            combobox.setParent(None)
            combobox.deleteLater()

        self.toolbars.clear()
        self.background_buttons.clear()
        self.reset_background_buttons.clear()
        self.checkboxes.clear()
        self.comboboxes.clear()

        self.clear_plot_layout()

        self.init_canvas(num_plots)

    def load_background_curve(self, canvas_index):
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Background Curve File", "", "CSV Files (*.csv)")
            if file_path:
                x_data, y_data = self.load_and_normalize_curve(file_path)
                self.background_curve_data[canvas_index] = (x_data, y_data)
                print(f"Background curve loaded from {file_path} for plot {canvas_index}")
                print(f"Background curve loaded for plot {canvas_index}")
                self.update_plot(canvas_index)
        except Exception as e:
            self.display_error(f"Error loading background curve: {e}")
            self.reset_background_curve(canvas_index)

    def reset_background_curve(self, canvas_index):
        self.background_curve_data[canvas_index] = None
        self.update_plot(canvas_index)
        print(f"Background curve reset for plot {canvas_index}")

    def export_results(self):
        """
        Exports the latest calculation results to a CSV file.
        The user is prompted to select a file location for the export.
        :return: None
        """
        fileName, _ = QFileDialog.getSaveFileName(self, "Export Results", "", "CSV Files (*.csv)")
        if not fileName:
            return  # User canceled the dialog

        frequency_vector = (self.latest_results.get('frequency_vector', []))["data"]
        headers = ['Frequency'] if len(frequency_vector) else []
        data = [frequency_vector] if len(frequency_vector) else []

        # Process each result to structure the data for CSV writing
        for key, value in self.latest_results.items():
            units = value.get('units', [])
            value = value.get('data', [])

            if key == 'frequency_vector':  # Skip the frequency vector itself
                continue
            if key == 'Display_all_PSD':
                continue
            if key == 'Display_all_PSD_filtered':
                continue
            if key == 'Display_CLTF_OLTF':
                continue

            if np.isscalar(value):
                # Handle scalars by repeating the value for each frequency
                headers.append(key)
                if len(data) == 0:  # No frequency vector, just a single row for the scalar
                    data.append(f"{[value]} ( {units[0]} )")
                else:
                    data.append([value] * len(frequency_vector))
            elif value.ndim == 1:  # Vector
                headers.append(f"{key}( {units[0]} )")
                data.append(value)
            elif value.ndim == 2:  # Matrix, skip the frequency column (column 0)
                for col_index in range(1, value.shape[1]):
                    headers.append(f"{key}_{col_index}( {units[col_index]} )")
                    data.append(value[:, col_index])

        # Transpose data for CSV writing
        data = zip(*data)

        with open(fileName, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            for row in data:
                writer.writerow(row)

    def import_flicker_data_from_json(self):
        """
        Imports specific data from a JSON.
        The json file should be exported from the Flicker tuning module
        :return:
        """
        fileName, _ = QFileDialog.getOpenFileName(self, "Import Flicker Data", "", "JSON Files (*.json)")
        if fileName:
            with open(fileName, 'r', encoding="utf-8") as json_file:
                specific_data = json.load(json_file)

            self.apply_flicker_data_to_parameters(specific_data)
            print(f"Specific data imported from {fileName}")

    def apply_flicker_data_to_parameters(self, specific_data):
        """
        Applies the flicker loaded data to the input parameters fields in the UI.
        :param specific_data: dict containing the flicker parameters to apply
        :return:
        """
        for param, value in specific_data.items():
            if param in self.inputs:
                self.inputs[param].setText(str(value))
        self.calculate()

    def export_parameters_to_json(self):
        """
        Exports the current input parameters to a JSON file.
        The user is prompted to select a file location for the export.
        Exported parameters can be imported back into the application.
        :return:
        """
        try:
            fileName, _ = QFileDialog.getSaveFileName(self, "Save Parameters", "", "JSON Files (*.json)")
            if not fileName:
                return  # User canceled the dialog

            # Prepare the parameters with updated defaults based on current GUI inputs
            print(self.input_parameters)
            updated_parameters = self.input_parameters.copy()
            for section_name, parameters in updated_parameters.items():
                for param_name in parameters:
                    # Check if this parameter has an input field in the GUI
                    if param_name in self.inputs:
                        line_edit = self.inputs[param_name]
                        current_value = line_edit.text()

                        # Attempt to convert the current value to a float, if possible
                        try:
                            current_value_float = float(current_value)
                            # Update the "default" value for this parameter
                            parameters[param_name]['default'] = current_value_float
                        except ValueError:
                            # Handle the case where the current value is not a valid float
                            print(
                                f"Warning: Skipping parameter '{param_name}' with non-numeric input '{current_value}'.")

            try :
                # Retrieve the currelnly selected SPICE circuit from the combo box
                selected_circuit = self.spice_circuit_combo.currentText()

                # Add the selected SPICE circuit to the updated parameters
                updated_parameters["SPICE_circuit"] = selected_circuit
            except Exception as e:
                print(f"Error adding SPICE circuit to updated parameters: {e}")
                pass

            # If a file name is selected, save the updated parameters to that file
            with open(fileName, 'w') as json_file:
                json.dump(updated_parameters, json_file, indent=4)
        except Exception as e:
            self.display_error(f"Error exporting parameters: {e}")

    def import_parameters_from_json(self):
        """
        Imports input parameters from a JSON file.
        The user is prompted to select a file to import the parameters from.
        The imported parameters are then used to update the UI.
        :return:
        """
        # Show an open file dialog to the user
        try:
            fileName, _ = QFileDialog.getOpenFileName(self, "Import Parameters", "", "JSON Files (*.json)")
            if fileName:
                # If a file is selected, load the parameters from that file
                with open(fileName, 'r', encoding="utf-8") as json_file:
                    self.input_parameters = json.load(json_file)
                    self.reset_parameters(reload=False)  # Update the UI with the imported parameters
                print(f"Parameters imported from {fileName}")
        except Exception as e:
            self.display_error(f"Error importing parameters: {e}")
            self.reset_parameters()

    def load_and_normalize_curve(self, file_path):
        """
        Loads a curve from a CSV file and return x and y data.
        :param file_path: FULL path to the CSV file
        :return: x_data, y_data
        """
        df = pd.read_csv(file_path)
        x_data = df.iloc[:, 0].values
        y_data = df.iloc[:, 1].values
        return x_data, y_data

    def log_scale(self, value, min_val, max_val, min_log, max_log):
        """Converts a linear slider value to a logarithmic frequency value."""
        log_range = np.log10(max_log) - np.log10(min_log)
        scale = log_range / (max_val - min_val)
        return np.power(10, np.log10(min_log) + scale * (value - min_val))

    def linear_scale(self, log_value, min_val, max_val, min_log, max_log):
        """Converts a logarithmic frequency value back to a linear slider value."""
        log_min = np.log10(min_log)
        log_max = np.log10(max_log)
        log_range = log_max - log_min
        scale = (max_val - min_val) / log_range
        return min_val + scale * (np.log10(log_value) - log_min)

    def update_frequency_range(self, value):
        """
        Updates the frequency range values based on the slider position.
        :param value:
        :return:
        """
        linear_start, linear_stop = value
        slider_min = self.frequency_range_slider.minimum()
        slider_max = self.frequency_range_slider.maximum()
        freq_min = self.input_parameters['misc']['f_start']['min']
        freq_max = self.input_parameters['misc']['f_stop']['max']
        self.f_start_value = self.log_scale(linear_start, slider_min, slider_max, freq_min, freq_max)
        self.f_stop_value = self.log_scale(linear_stop, slider_min, slider_max, freq_min, freq_max)

        self.frequency_values_label.setText(
            f"Frequency Start: {self.f_start_value}, Frequency Stop: {self.f_stop_value}")
        self.calculation_timer.start()

    def delayed_calculate(self):
        """
        Performs calculation after a delay to avoid UI lag during slider adjustments.
        This method is triggered by the calculation_timer's timeout signal.
        """
        self.calculate()

    def bind_slider_to_input(self, line_edit, parameter):
        """
        Binds the coarse and fine sliders to a selected input field, allowing for parameter adjustment.
        It sets the sliders' ranges based on the parameter's defined range and adjusts them to reflect the input's
        current value.

        Args:
            line_edit (QLineEdit): The QLineEdit widget representing the input field for the parameter.
            parameter (str): The name of the parameter associated with the input field.

        This method calculates the initial positions of both sliders based on the current value of the input field
        and adjusts the sliders to reflect both the integral and decimal parts of this value.
        """
        self.currently_selected_input = (line_edit, parameter)
        text = line_edit.text()
        try:
            value = float(text)
        except ValueError:
            # Invalid input, notify the user or handle as appropriate
            print(f"Invalid input for parameter '{parameter}': '{text}'. Skipping slider binding.")
            return

        # Find the parameter info from the nested structure
        for category, parameters in self.input_parameters.items():
            if parameter in parameters:
                range_info = parameters[parameter]
                break
        else:
            print(f"Parameter {parameter} not found in input_parameters.")
            return

        # Coarse slider setup
        self.global_slider_coarse.setMinimum(range_info['min'])
        self.global_slider_coarse.setMaximum(range_info['max'])
        slider_value = self.calculate_slider_value(value, range_info['min'], range_info['max'])
        self.global_slider_coarse.setValue(slider_value)

        # Fine slider setup
        decimal_part = value - int(value)
        self.global_slider_fine.setMinimum(0)
        self.global_slider_fine.setMaximum(999)
        self.global_slider_fine.setValue(int(decimal_part * 1000))

    def calculate_slider_value(self, value, min_val, max_val):
        """
        Converts the parameter value to a slider position, considering the parameter's range.
        For linear parameters, it returns the value itself.
        For logarithmic scaling, still need to adjust this method to calculate the slider position appropriately.
        """
        return int(value)

    def adjust_slider_properties(self, parameter):
        """
                Adjusts the properties (minimum, maximum, and current value) of the global sliders based on the
                selected parameter.
                This method is crucial for ensuring that the sliders provide a meaningful and constrained range of
                adjustment
                for the parameter's value.

                Args:
                    parameter (str): The name of the parameter for which to adjust the slider properties.

                Note:
                    The coarse slider is adjusted to cover the entire range of the parameter, allowing for broad
                    adjustments.
                    The fine slider is designed to fine-tune the parameter value, focusing on the decimal part for
                    precise control.
        """
        if parameter in self.input_parameters:
            range_info = self.input_parameters[parameter]
            self.global_slider_coarse.setMinimum(range_info['min'] * self.slider_precision)
            self.global_slider_coarse.setMaximum(range_info['max'] * self.slider_precision)
        else:
            self.global_slider_coarse.setMinimum(0)
            self.global_slider_coarse.setMaximum(100)

    def update_selected_input_value(self, slider_type):
        """
               Updates the value of the currently selected input field based on the slider movement.
               This method ensures that changes made using the sliders are immediately reflected in the input field,
               providing a responsive and interactive experience for adjusting parameters.

               Args:
                   slider_type (str): Indicates whether the adjustment is made with the 'coarse' or 'fine' slider.

               Depending on the slider type, this method calculates the new value for the input field by combining
               the integral part from the coarse slider and the decimal part from the fine slider,
               maintaining precision.
       """
        if not self.currently_selected_input:
            return

        line_edit, _ = self.currently_selected_input
        coarse_value = self.global_slider_coarse.value()
        fine_value = self.global_slider_fine.value() / 1000

        if slider_type == 'coarse':
            new_value = coarse_value + fine_value
        else:  # fine adjustment, preserve integer part from coarse slider
            new_value = int(coarse_value) + fine_value

        try:
            line_edit.setText(f"{new_value:.3f}")  # Format with 3 decimal places
            self.calculation_timer.start()
        except RuntimeError as e:
            print(f"Error updating input value: {e}")

    def retrieve_parameters(self):
        params_dict = {}

        for category, parameters in self.input_parameters.items():
            for param, attrs in parameters.items():
                if param in ['f_start', 'f_stop']:
                    params_dict[param] = getattr(self, f"{param}_value")
                    continue

                if param in self.inputs:
                    try:
                        text = self.inputs[param].text()
                    except RuntimeError as e:
                        print(param, e)
                        print(f"Error retrieving input value: {e}")
                        continue
                    try:
                        value = float(text)
                        input_unit = attrs.get('input_unit', '')
                        target_unit = attrs.get('target_unit', '')
                        if input_unit and target_unit:
                            value_converted = convert_unit(value, input_unit, target_unit)
                        else:
                            value_converted = value
                        params_dict[param] = value_converted
                    except ValueError:
                        print(f"Invalid input for parameter '{param}': '{text}'. Skipping calculation.")
                        return None

        return params_dict

    def calculate(self):
        """
        Gathers the current parameter values from the input fields, initiates the calculation process through
        the controller,
        and triggers the plotting of the results. Uses unit conversion for parameters requiring it.
        """
        # Retrieve parameters from inputs and convert units where necessary

        if self.block_calculation:
            return
        params_dict = self.retrieve_parameters()

        if hasattr(self.controller, 'update_parameters'):
            self.controller.update_parameters(params_dict)

        self.on_calculation_finished(self.controller.get_current_results())

    def on_calculation_finished(self, calculation_results):
        """
        Callback method for handling the completion of the calculation process.
        :param calculation_results:
        :return:
        """
        self.latest_results = calculation_results  # Store the latest results
        self.plot_results(calculation_results)
        print("Calculation completed successfully.")

    def display_error(self, error_message):
        """
        Triggered when an error occurs during the calculation process.
        :param error_message:
        :return:
        """
        # Show an error message to the user
        print(f"Calculation failed: {error_message}")
        # use a QMessageBox for GUI error display

        QMessageBox.critical(self, "An error occurred", f"Calculation failed: {error_message}")

    def update_plot(self, index):
        def plot_curve(data_with_meta, x_vector, linestyle='-', color=None):
            """Plot a curve with metadata based on either frequency or time."""
            data = data_with_meta["data"]
            labels = data_with_meta.get("labels", ["", ""])
            units = data_with_meta.get("units", ["", ""])

            if np.isscalar(data):
                y_values = np.full_like(x_vector, data)
                canvas.axes.plot(x_vector, y_values, label=f"{labels[0]} ({units[0]})", linestyle=linestyle,
                                 color=color)
            elif isinstance(data, np.ndarray) and data.ndim == 1:
                if len(data) == len(x_vector):  # Ensure matching lengths
                    canvas.axes.plot(x_vector, data, label=f"{labels[0]} ({units[0]})", linestyle=linestyle,
                                     color=color)
            elif isinstance(data, np.ndarray) and data.ndim > 1:
                for col_index in range(1, data.shape[1]):
                    y_values = data[:, col_index]
                    if len(y_values) == len(x_vector):  # Ensure matching lengths
                        canvas.axes.plot(x_vector, y_values, label=f"{labels[col_index]} ({units[col_index]})",
                                         linestyle=linestyle, color=color)

        def get_x_vector(data_meta, default_vector):
            if "Time" in data_meta.get("labels", []):
                return data_meta["data"][:, 0]  # Use the first column as the time vector
            return default_vector

        for i, (canvas, combo_box, checkbox) in enumerate(zip(self.canvases, self.comboboxes, self.checkboxes)):
            selected_key = combo_box.currentText()
            if not selected_key:
                continue

            canvas.axes.clear()  # Clear the canvas for new plotting

            current_results = self.controller.get_current_results()
            old_results = self.controller.get_old_results()

            frequency_vector = current_results.get('frequency_vector', [])["data"]
            default_x_vector = frequency_vector

            # Plot Current Data
            current_data_meta = current_results.get(selected_key, {})
            current_x_vector = get_x_vector(current_data_meta, default_x_vector)
            if current_data_meta:
                plot_curve(current_data_meta, current_x_vector, linestyle='-')
                self.set_labels(current_data_meta, canvas)

            # Plot Old Data if checkbox is checked
            if checkbox.isChecked() and old_results:
                old_data_meta = old_results.get(selected_key, {})
                old_x_vector = get_x_vector(old_data_meta, default_x_vector)
                if old_data_meta:
                    plot_curve(old_data_meta, old_x_vector, linestyle=':', color='gray')

            # Plot Saved Data from saved_data_results
            for saved_index, saved_results in enumerate(self.controller.engine.saved_data_results):
                saved_data_meta = saved_results.results.get(selected_key, {})
                saved_x_vector = get_x_vector(saved_data_meta, default_x_vector)
                if saved_data_meta:
                    plot_curve(saved_data_meta, saved_x_vector, linestyle='--', color=None)

            # Plot Background Curve if available
            if self.background_curve_data[i] is not None:
                x_background, y_background = self.background_curve_data[i]
                mask = (x_background >= min(frequency_vector)) & (x_background <= max(frequency_vector))
                x_background_filtered = x_background[mask]
                y_background_filtered = y_background[mask]
                canvas.axes.plot(x_background_filtered, y_background_filtered, label='Background Curve', linestyle='-',
                                 color='black')

            canvas.axes.grid(which='both')
            canvas.axes.legend()
            canvas.draw()

    def set_labels(self, data_meta, canvas):
        """Set labels and scales based on data type."""
        labels = data_meta.get("labels", [])
        if "Time" in labels:
            canvas.axes.set_xlabel("Time (s)")
            canvas.axes.set_yscale('linear')
            canvas.axes.set_xscale('linear')

        else:
            canvas.axes.set_xlabel("Frequency (Hz)")
            canvas.axes.set_yscale('log')
            canvas.axes.set_xscale('log')

    def plot_results(self, calculation_results):
        """
        Plots the calculation results on the canvas based on the selected key from the combo box a
        nd the state of the 'Show Old Curve' checkbox.
        :param calculation_results:
        :return:
        """
        self.latest_results = calculation_results  # Store the latest results

        if self.latest_results is not None:
            available_results = list(self.latest_results.keys())
        else:
            available_results = None
        if 'frequency_vector' in available_results:
            available_results.remove('frequency_vector')

        # Loop through each plot and remember the current selection
        previous_selections = [combo_box.currentText() for combo_box in self.comboboxes]

        for i, combo_box in enumerate(self.comboboxes):
            if available_results:
                combo_box.blockSignals(True)
                combo_box.clear()
                combo_box.addItems(available_results)

                # Restore the previous selection if it's still available; otherwise, use the first available result
                if previous_selections[i] in available_results:
                    combo_box.setCurrentText(previous_selections[i])
                else:
                    combo_box.setCurrentIndex(0)  # or handle differently as needed

                combo_box.blockSignals(False)

                # Trigger update_plot now with the restored or updated selection
                self.update_plot(i)

    def reset_parameters(self, reload=True):
        """
        Resets all input fields to their default values and adjusts the sliders to reflect these defaults.
        This method iterates through all parameters across categories, reverting any changes made by the user
        to the default state.
        """
        # Iterate through categories and their parameters
        print(f"reset params {reload}")
        self.load_default_parameters(reload=reload)
        selected_circuit = self.spice_circuit_combo.currentText()
        self.merge_spice_parameters(selected_circuit)
        for category, parameters in self.input_parameters.items():
            for parameter in parameters:
                if parameter in self.inputs:
                    default_value = str(parameters[parameter]['default'])
                    self.inputs[parameter].setText(default_value)

                    # If the currently selected input is being reset, update the sliders too
                    if self.currently_selected_input and self.currently_selected_input[1] == parameter:
                        self.bind_slider_to_input(self.inputs[parameter], parameter)

        # Optionally, trigger a recalculation if you want immediate feedback on the reset values
        self.calculate()

    def validate_input(self, line_edit, parameter):
        """
        Validates the input of a QLineEdit widget, ensuring it's a valid number within the specified range for
        the given parameter.
        Adjusts the input value to the nearest valid value if it falls outside the allowed range and visually
        indicates invalid inputs.
        """
        text = line_edit.text()
        found = False

        # Search for the parameter in the nested dictionary
        for category, parameters in self.input_parameters.items():
            if parameter in parameters:
                attrs = parameters[parameter]
                found = True
                break

        if not found:
            print(f"Parameter '{parameter}' not found in any category.")
            return

        try:
            value = float(text)
            min_val = attrs['min']
            max_val = attrs['max']

            # Clamp the value to the nearest valid boundary if out of range
            if value < min_val:
                raise ValueError(f"Value {value} is below minimum {min_val} for '{parameter}'.")
            elif value > max_val:
                raise ValueError(f"Value {value} exceeds maximum {max_val} for '{parameter}'.")

            # Reset background color if the input is within the valid range
            line_edit.setStyleSheet("")
            self.block_calculation = False
        except ValueError:
            # Indicate invalid input with a red background
            line_edit.setStyleSheet("background-color: #ffaaaa;")
            self.block_calculation = True
            print(f"Invalid input for '{parameter}': '{text}' is not a valid number.")

    def init_strategy_selection(self):
        strategy_selection_widget = QWidget()
        strategy_selection_layout = QGridLayout()
        strategy_selection_widget.setLayout(strategy_selection_layout)

        strategy_selection_layout.setSpacing(10)

        row = 0
        for node_name, strategies_info in STRATEGY_MAP.items():
            if len(strategies_info["strategies"]) > 1:
                label = QLabel(f"{node_name} strategy:")
                label.setStyleSheet("font-weight: bold; font-size: 14px")

                combo_box = QComboBox()
                for strategy in strategies_info["strategies"]:
                    combo_box.addItem(strategy.__name__, strategy)
                default_strategy = strategies_info["default"]
                combo_box.setCurrentIndex(combo_box.findText(default_strategy.__name__))

                combo_box.currentIndexChanged.connect(
                    lambda index, name=node_name, cb=combo_box: self.update_node_strategy(name, cb.currentData()))

                strategy_selection_layout.addWidget(label, row, 0)
                strategy_selection_layout.addWidget(combo_box, row, 1)
                row += 1

        strategy_selection_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding), row, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(strategy_selection_widget)
        self.strategy_tab.setLayout(QVBoxLayout())
        self.strategy_tab.layout().addWidget(scroll_area)

    def update_node_strategy(self, node_name, strategy_class):
        print("update")
        print(strategy_class)
        print(type(strategy_class))
        print(f"Gui - try to update strategy for {node_name} to {strategy_class.__name__}")

        params_dict = {}
        for category, parameters in self.input_parameters.items():
            for param, attrs in parameters.items():
                if param in ['f_start', 'f_stop']:
                    params_dict[param] = getattr(self, f"{param}_value")
                    continue

                if param in self.inputs:
                    try:
                        text = self.inputs[param].text()
                    except RuntimeError:
                        pass
                    try:
                        value = float(text)
                        input_unit = attrs.get('input_unit', '')
                        target_unit = attrs.get('target_unit', '')
                        if input_unit and target_unit:
                            value_converted = convert_unit(value, input_unit, target_unit)
                        else:
                            value_converted = value
                        params_dict[param] = value_converted
                    except ValueError:
                        print(f"Invalid input for parameter '{param}': '{text}'. Skipping calculation.")
                        return

        self.controller.set_node_strategy(node_name, strategy_class, params_dict)
        self.calculate()

    def save_results(self, index, button):
        if self.button_states[index] == 0:
            button.setStyleSheet("background-color: green")
            self.button_states[index] = 1

            current_parameters = self.input_parameters.copy()
            for section_name, parameters in current_parameters.items():
                for param_name in parameters:
                    if param_name in self.inputs:
                        line_edit = self.inputs[param_name]
                        current_value = line_edit.text()

                        try:
                            current_value_float = float(current_value)
                            parameters[param_name]['default'] = current_value_float
                        except ValueError:
                            print(
                                f"Warning: Skipping parameter '{param_name}' with non-numeric input '{current_value}'.")
            self.controller.save_current_results(index)
            self.saved_parameters[index] = copy.deepcopy(current_parameters)

        else:
            if self.saved_parameters[index] is not None:
                for category, parameters in self.input_parameters.items():
                    for parameter in parameters:

                        if parameter == 'f_start' or parameter == 'f_stop':
                            continue
                        if parameter in self.saved_parameters[index][category].keys():
                            default_value = str(self.saved_parameters[index][category][parameter]['default'])
                            self.inputs[parameter].setText(default_value)

                            # If the currently selected input is being reset, update the sliders too
                            if self.currently_selected_input and self.currently_selected_input[1] == parameter:
                                self.bind_slider_to_input(self.inputs[parameter], parameter)
                print(f"Params reset to saved state {index}")
                self.calculate()

    def load_strategy(self, strategies_info) -> dict:

        strategies_instances = {}

        for strategy_name, strategy_info in strategies_info.items():
            module_path = strategy_info["file"].replace(".py", "").replace("/", ".")
            class_name = strategy_name

            try:
                module = importlib.import_module(module_path)
            except ImportError as e:
                print(f"Failed to import module {module_path}: {e}")
                continue

            try:
                strategy_class = getattr(module, class_name)
            except AttributeError as e:
                print(f"Failed to get class {class_name} from module {module_path}: {e}")
                continue

            try:
                strategy_instance = strategy_class
                strategies_instances[strategy_name] = strategy_instance
                print(f"Loaded strategy {strategy_name}")
            except Exception as e:
                print(f"Failed to instantiate {class_name}: {e}")

        return strategies_instances


if __name__ == "__main__":
    app = QApplication(sys.argv)

    original_pixmap = QPixmap("/home/ronceray/Documents/PLASMAG/PLASMAG/ressources/PLASMAG_logo_v1.png")
    scaled_pixmap = original_pixmap.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio)

    splash = QSplashScreen(scaled_pixmap)
    splash.showMessage("Loading...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    splash.show()

    app.processEvents()


    def initialize_main_window():
        global window
        window = MainGUI()
        window.show()
        splash.finish(window)


    QTimer.singleShot(1000, initialize_main_window)

    sys.exit(app.exec())
