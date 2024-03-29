"""
src/view/gui.py
PLASMAG GUI module
"""
import json
import os
import sys
import time
import warnings
from pint import UnitRegistry
import numpy as np

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QLabel, \
    QGridLayout, QSlider, QCheckBox, QHBoxLayout, QSpacerItem, QSizePolicy, QComboBox, QScrollArea, QFileDialog, \
    QMessageBox
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QSplashScreen, QApplication

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from qtrangeslider import QRangeSlider
from src.controler.controller import CalculationController


ureg: UnitRegistry = UnitRegistry()


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

    def __init__(self):
        super().__init__()
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

        self.setWindowTitle("PLASMAG")
        self.setGeometry(100, 100, 2560, 1440)  # Adjust size as needed

        self.load_default_parameters()

        self.f_start_value = self.input_parameters["misc"]['f_start']['default']
        self.f_stop_value = self.input_parameters["misc"]['f_stop']['default']

        self.currently_selected_input = None

        self.init_ui()
        self.init_menu()

        self.showMaximized()

    def init_parameters_input(self):
        """
        Initializes the input fields for the parameters based on the loaded input parameters.
        Iterates over the input parameters dictionary and creates a QLabel and QLineEdit for each parameter in each
        section. The input fields are organized in a scrollable area for better visibility and usability.
        """
        self.inputs = {}

        for section_name, section_parameters in self.input_parameters.items():
            section_widget = QWidget()
            section_layout = QGridLayout()
            section_widget.setLayout(section_layout)
            section_layout.setSpacing(10)

            section_label = QLabel(f"<b>{section_name.replace('_', ' ').capitalize()}</b>")
            section_label.setStyleSheet("font-weight: bold; font-size: 16px")
            section_layout.addWidget(section_label, 0, 0, 1, 2)  # Span sur 2 colonnes

            section_row = 1
            for idx, (param_name, param_attrs) in enumerate(section_parameters.items()):

                if param_name == 'f_start' or param_name == 'f_stop':
                    continue

                label = QLabel(f"{param_name}:")
                line_edit = QLineEdit(str(param_attrs['default']))
                line_edit.setToolTip(param_attrs['description'])
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

    def load_default_parameters(self):
        """
        Loads the default input parameters from the 'data/default.json' file.
        :return:
        """
        current_dir = os.path.dirname(os.path.realpath(__file__))
        json_file_path = os.path.join(current_dir, '..', '..', 'data', 'default.json')
        json_file_path = os.path.normpath(json_file_path)

        try:
            with open(json_file_path, 'r', encoding="utf-8") as json_file:
                self.input_parameters = json.load(json_file)
        except FileNotFoundError:
            print(f"File{json_file_path} not found.")
        except json.JSONDecodeError:
            print(f"Error reading : {json_file_path}.")

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

    def init_controller(self):
        """
        Initializes the CalculationController for handling the calculation logic.
        :return:
        """
        self.controller = CalculationController()

        for parameter, line_edit in self.inputs.items():
            line_edit.mousePressEvent = (lambda event, le=line_edit,
                                                param=parameter: self.bind_slider_to_input(le, param))
            line_edit.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        self.slider_precision = 100

    def init_canvas(self, number_of_plots=3):
        """
        Initializes the matplotlib canvas for plotting the calculation results.
        Creates three separate canvases for different plots and adds them to the main layout.
        :return:
        """
        self.canvases = [MplCanvas() for _ in range(number_of_plots)]
        self.toolbars = []
        self.checkboxes = []
        self.comboboxes = []

        for canvas in self.canvases:
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
            combo_box.currentIndexChanged.connect(self.update_plot)
            self.comboboxes.append(combo_box)

            top_layout.addWidget(toolbar)
            top_layout.addWidget(checkbox)
            top_layout.addWidget(combo_box)

            canvas_layout.addWidget(canvas)

            left_spacer = QSpacerItem(1, 1, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
            top_layout.addSpacerItem(left_spacer)

            self.plot_layout.addLayout(canvas_layout)

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

        self.params_layout = QVBoxLayout()

        # Grid layout for parameters
        self.grid_layout = QGridLayout()
        self.init_parameters_input()

        # Add Reset Parameters button
        self.reset_params_btn = QPushButton('Reset Parameters')
        self.reset_params_btn.clicked.connect(self.reset_parameters)
        self.params_layout.addWidget(self.reset_params_btn)

        # Calculate button
        self.calculate_btn = QPushButton('Calculate')
        self.calculate_btn.clicked.connect(self.calculate)
        self.params_layout.addWidget(self.calculate_btn)

        self.init_sliders()

        self.plot_layout = QVBoxLayout()

        self.init_canvas()

        # set proportions
        self.main_layout.addLayout(self.params_layout, 3)
        self.main_layout.addLayout(self.plot_layout, 4)

        self.init_controller()

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
        fileName, _ = QFileDialog.getSaveFileName(self, "Save Parameters", "", "JSON Files (*.json)")
        if not fileName:
            return  # User canceled the dialog

        # Prepare the parameters with updated defaults based on current GUI inputs
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
                        print(f"Warning: Skipping parameter '{param_name}' with non-numeric input '{current_value}'.")

        # If a file name is selected, save the updated parameters to that file
        with open(fileName, 'w') as json_file:
            json.dump(updated_parameters, json_file, indent=4)

        print(f"Parameters exported to {fileName}")

    def import_parameters_from_json(self):
        """
        Imports input parameters from a JSON file.
        The user is prompted to select a file to import the parameters from.
        The imported parameters are then used to update the UI.
        :return:
        """
        # Show an open file dialog to the user
        fileName, _ = QFileDialog.getOpenFileName(self, "Import Parameters", "", "JSON Files (*.json)")
        if fileName:
            # If a file is selected, load the parameters from that file
            with open(fileName, 'r', encoding="utf-8") as json_file:
                self.input_parameters = json.load(json_file)
                self.reset_parameters()  # Update the UI with the imported parameters
            print(f"Parameters imported from {fileName}")


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

        line_edit.setText(f"{new_value:.3f}")  # Format with 3 decimal places
        self.calculation_timer.start()

    def calculate(self):
        """
        Gathers the current parameter values from the input fields, initiates the calculation process through
        the controller,
        and triggers the plotting of the results. Uses unit conversion for parameters requiring it.
        """
        # Retrieve parameters from inputs and convert units where necessary
        params_dict = {}
        for category, parameters in self.input_parameters.items():
            for param, attrs in parameters.items():
                if param in ['f_start', 'f_stop']:
                    params_dict[param] = getattr(self, f"{param}_value")
                    continue

                if param in self.inputs:
                    text = self.inputs[param].text()
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

        QMessageBox.critical(self, "Calculation Error", f"Calculation failed: {error_message}")





    def update_plot(self, index):
        """
        Updates the plot based on the selected key from the combo box and the state of the 'Show Old Curve' checkbox.
        :param index:
        :return:
        """
        for i, (canvas, combo_box, checkbox) in enumerate(zip(self.canvases, self.comboboxes, self.checkboxes)):
            selected_key = combo_box.currentText()
            if not selected_key:  # In case the combo box is empty
                continue

            current_results = self.controller.get_current_results()
            old_results = self.controller.get_old_results()

            if current_results is None:
                print("No current calculation results available.")
                continue

            current_data = current_results.get(selected_key)
            frequency_vector = current_results.get('frequency_vector')

            canvas.axes.clear()

            if current_data is not None:
                if np.isscalar(current_data):
                    # Scalar data plotting
                    y_values = np.full_like(frequency_vector, current_data)
                    canvas.axes.plot(frequency_vector, y_values, 'r', label='Current ' + selected_key)
                elif current_data.ndim == 1:
                    # 1D Vector data plotting
                    canvas.axes.plot(frequency_vector, current_data, label='Current ' + selected_key)
                elif current_data.ndim > 1:
                    # 2D Vector data plotting (assumes [X, Y] format)
                    x_data = current_data[:, 0]
                    y_data = current_data[:, 1]
                    canvas.axes.plot(x_data, y_data, label='Current ' + selected_key)

                    if "CLTF" in selected_key:
                        if "CLTF_Non_filtered" in selected_key:
                            oltf_key = 'OLTF_Non_filtered'
                        elif "CLTF_Filtered" in selected_key:
                            oltf_key = 'OLTF_Filtered'

                        oltf_data = current_results.get(oltf_key)
                        x_data_oltf = oltf_data[:, 0]
                        y_data_oltf = oltf_data[:, 1]
                        canvas.axes.plot(x_data_oltf, y_data_oltf, label=oltf_key, color='g')

                    if "OLTF" in selected_key:
                        if "OLTF_Non_filtered" in selected_key:
                            cltf_key = 'CLTF_Non_filtered'
                        elif "OLTF_Filtered" in selected_key:
                            cltf_key = 'CLTF_Filtered'

                        oltf_data = current_results.get(cltf_key)
                        x_data_oltf = oltf_data[:, 0]
                        y_data_oltf = oltf_data[:, 1]
                        canvas.axes.plot(x_data_oltf, y_data_oltf, label=cltf_key, color='g')

                    if "Display_all_PSD" in selected_key:
                        canvas.axes.clear()
                        x_data = current_data[:, 0]
                        PSD_R_cr = current_data[:, 1]
                        PSD_R_Coil = current_data[:, 2]
                        PSD_e_en = current_data[:, 3]
                        PSD_e_in = current_data[:, 4]
                        PSD_Total = current_data[:, 5]

                        canvas.axes.plot(x_data, PSD_R_cr, label='PSD_R_cr')
                        canvas.axes.plot(x_data, PSD_R_Coil, label='PSD_R_Coil')
                        canvas.axes.plot(x_data, PSD_e_en, label='PSD_e_en')
                        canvas.axes.plot(x_data, PSD_e_in, label='PSD_e_in')
                        canvas.axes.plot(x_data, PSD_Total, label='PSD_Total')

                    with warnings.catch_warnings():
                        warnings.simplefilter("error", UserWarning)  # Convert warnings to errors
                        try:
                            canvas.axes.set_yscale('log')
                        except UserWarning:
                            canvas.axes.set_yscale('linear')

                # Repeat plotting logic for old data if checkbox is checked
            if checkbox.isChecked() and old_results:
                old_data = old_results.get(selected_key)
                old_frequency_vector = old_results.get('frequency_vector')
                if old_data is not None:
                    if np.isscalar(old_data):
                        y_values = np.full_like(old_frequency_vector, old_data)
                        canvas.axes.plot(old_frequency_vector, y_values, 'g', label='Old ' + selected_key,
                                         linestyle='--')
                    elif old_data.ndim == 1:
                        canvas.axes.plot(old_frequency_vector, old_data, label='Old ' + selected_key, linestyle='--')
                    elif old_data.ndim > 1:
                        old_x_data = old_data[:, 0]
                        old_y_data = old_data[:, 1]
                        canvas.axes.plot(old_x_data, old_y_data, label='Old ' + selected_key, linestyle='--')

                        if "CLTF" in selected_key:
                            if "CLTF_Non_filtered" in selected_key:
                                oltf_key = 'OLTF_Non_filtered'
                                print(oltf_key)
                            elif "CLTF_Filtered" in selected_key:
                                oltf_key = 'OLTF_Filtered'
                                print(oltf_key)

                            oltf_data = old_results.get(oltf_key)
                            x_data_oltf = oltf_data[:, 0]
                            y_data_oltf = oltf_data[:, 1]
                            canvas.axes.plot(x_data_oltf, y_data_oltf, label="Old " + oltf_key, color='r',
                                             linestyle='--')

                        if "OLTF" in selected_key:
                            if "OLTF_Non_filtered" in selected_key:
                                cltf_key = 'CLTF_Non_filtered'
                            elif "OLTF_Filtered" in selected_key:
                                cltf_key = 'CLTF_Filtered'

                            oltf_data = old_results.get(cltf_key)
                            x_data_oltf = oltf_data[:, 0]
                            y_data_oltf = oltf_data[:, 1]
                            canvas.axes.plot(x_data_oltf, y_data_oltf, label="Old" + cltf_key, color='r',
                                             linestyle='--')

                        if "Display_all_PSD" in selected_key:
                            canvas.axes.clear()
                            x_data = current_data[:, 0]
                            PSD_R_cr = current_data[:, 1]
                            PSD_R_Coil = current_data[:, 2]
                            PSD_e_en = current_data[:, 3]
                            PSD_e_in = current_data[:, 4]
                            PSD_Total = current_data[:, 5]

                            x_data_old = old_data[:, 0]
                            PSD_R_cr_old = old_data[:, 1]
                            PSD_R_Coil_old = old_data[:, 2]
                            PSD_e_en_old = old_data[:, 3]
                            PSD_e_in_old = old_data[:, 4]
                            PSD_Total_old = old_data[:, 5]

                            canvas.axes.plot(x_data, PSD_R_cr, label='PSD_R_cr')
                            canvas.axes.plot(x_data, PSD_R_Coil, label='PSD_R_Coil')
                            canvas.axes.plot(x_data, PSD_e_en, label='PSD_e_en')
                            canvas.axes.plot(x_data, PSD_e_in, label='PSD_e_in')
                            canvas.axes.plot(x_data, PSD_Total, label='PSD_Total')

                            canvas.axes.plot(x_data_old, PSD_R_cr_old, label='Old PSD_R_cr', linestyle='--')
                            canvas.axes.plot(x_data_old, PSD_R_Coil_old, label='Old PSD_R_Coil', linestyle='--')
                            canvas.axes.plot(x_data_old, PSD_e_en_old, label='Old PSD_e_en', linestyle='--')
                            canvas.axes.plot(x_data_old, PSD_e_in_old, label='Old PSD_e_in', linestyle='--')
                            canvas.axes.plot(x_data_old, PSD_Total_old, label='Old PSD_Total', linestyle='--')

                        with warnings.catch_warnings():
                            warnings.simplefilter("error", UserWarning)  # Convert warnings to errors
                            try:
                                canvas.axes.set_yscale('log')
                            except UserWarning:
                                canvas.axes.set_yscale('linear')

            canvas.axes.set_xlabel('Frequency (Hz)')
            canvas.axes.set_ylabel(selected_key)
            canvas.axes.set_xscale('log')
            canvas.axes.grid(which='both')
            canvas.axes.legend()
            canvas.draw()

    def plot_results(self, calculation_results):
        """
        Plots the calculation results on the canvas based on the selected key from the combo box a
        nd the state of the 'Show Old Curve' checkbox.
        :param calculation_results:
        :return:
        """
        self.latest_results = calculation_results  # Store the latest results

        available_results = list(self.latest_results.keys())
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

    def reset_parameters(self):
        """
        Resets all input fields to their default values and adjusts the sliders to reflect these defaults.
        This method iterates through all parameters across categories, reverting any changes made by the user
        to the default state.
        """
        # Iterate through categories and their parameters
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
        except ValueError:
            # Indicate invalid input with a red background
            line_edit.setStyleSheet("background-color: #ffaaaa;")
            print(f"Invalid input for '{parameter}': '{text}' is not a valid number.")


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