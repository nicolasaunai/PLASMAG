import sys
import warnings

import numpy as np
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QLabel, \
    QGridLayout, QSlider, QCheckBox, QHBoxLayout, QSpacerItem, QSizePolicy, QComboBox
from isort.profiles import attrs
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.controler.controller import CalculationController
from qtrangeslider import QRangeSlider

from pint import UnitRegistry
ureg = UnitRegistry()

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

# dict parameters that is a merge of default_values and parameter_ranges

input_parameters = {
    'mu_insulator': {
        'default': 1, 'min': 0, 'max': 10,
        'description': "Permeability of the insulator",
        'input_unit': '', 'target_unit': ''
    },
    'len_coil': {
        'default': 155, 'min': 1, 'max': 200,
        'description': "Length of the coil in millimeters",
        'input_unit': 'millimeter', 'target_unit': 'meter'
    },
    'kapthon_thick': {
        'default': 30, 'min': 10, 'max': 300,
        'description': "Thickness of the kapthon in micrometers",
        'input_unit': 'micrometer', 'target_unit': 'meter'
    },
    'insulator_thick': {
        'default': 10, 'min': 1, 'max': 100,
        'description': "Thickness of the insulator in micrometers",
        'input_unit': 'micrometer', 'target_unit': 'meter'
    },
    'diam_out_mandrel': {
        'default': 3.2, 'min': 1, 'max': 10,
        'description': "Diameter of the outer mandrel in millimeters",
        'input_unit': 'millimeter', 'target_unit': 'meter'
    },
    'diam_wire': {
        'default': 90, 'min': 10, 'max': 300,
        'description': "Diameter of the wire in micrometers",
        'input_unit': 'micrometer', 'target_unit': 'meter'
    },
    'capa_tuning': {
        'default': 1, 'min': 1, 'max': 1000,
        'description': "Tuning capacitance in picofarads",
        'input_unit': 'picofarad', 'target_unit': 'farad'
    },
    'capa_triwire': {
        'default': 150, 'min': 10, 'max': 1000,
        'description': "Triwire capacitance in picofarads",
        'input_unit': 'picofarad', 'target_unit': 'farad'
    },
    'len_core': {
        'default': 20, 'min': 1, 'max': 200,
        'description': "Length of the core in centimeters",
        'input_unit': 'centimeter', 'target_unit': 'meter'
    },
    'diam_core': {
        'default': 3.2, 'min': 1, 'max': 100,
        'description': "Diameter of the core in millimeters",
        'input_unit': 'millimeter', 'target_unit': 'meter'
    },
    'mu_r': {
        'default': 100000, 'min': 1, 'max': 1000000,
        'description': "Relative permeability",
        'input_unit': '', 'target_unit': ''
    },
    'nb_spire': {
        'default': 12100, 'min': 1000, 'max': 20000,
        'description': "Number of spires",
        'input_unit': '', 'target_unit': ''
    },
    'ray_spire': {
        'default': 5, 'min': 1, 'max': 100,
        'description': "Radius of the spire in millimeters",
        'input_unit': 'millimeter', 'target_unit': 'meter'
    },
    'rho_whire': {
        'default': 1.6, 'min': 1, 'max': 10,
        'description': "Resistivity of the wire",
        'input_unit': '', 'target_unit': ''
    },
    'coeff_expansion': {
        'default': 1, 'min': 1, 'max': 10,
        'description': "Expansion coefficient",
        'input_unit': '', 'target_unit': ''
    },
    'gain_1': {
        'default': 0, 'min': -100, 'max': 100,
        'description': "Gain of the first stage in dBV",
        'input_unit': '', 'target_unit': ''
    },

    'stage_1_cutting_freq': {
        'default': 100, 'min': 1, 'max': 1000000,
        'description': "Cutting frequency of the first stage in Hertz",
        'input_unit': 'hertz', 'target_unit': 'hertz'
    },

    'gain_1_linear': {
        'default': 1, 'min': 0, 'max': 10,
        'description': "Gain of the first stage in linear",
        'input_unit': '', 'target_unit': ''
    },
    'gain_2_linear': {
        'default': 1.259, 'min': 0, 'max': 10,
        'description': "Gain of the second stage in linear",
        'input_unit': '', 'target_unit': ''
    },

    'gain_2': {
        'default': 2, 'min': -100, 'max': 100,
        'description': "Gain of the second stage in dBV",
        'input_unit': '', 'target_unit': ''
    },
    'stage_2_cutting_freq': {
        'default': 20000, 'min': 1, 'max': 1000000,
        'description': "Cutting frequency of the second stage in Hertz",
        'input_unit': 'hertz', 'target_unit': 'hertz'
    },

    'feedback_resistance': {
        'default': 1000, 'min': 1, 'max': 100000,
        'description': "Feedback resistance in Ohms",
        'input_unit': 'ohm', 'target_unit': 'ohm'
    },
    'mutual_inductance': {
        'default': 1, 'min': 0, 'max': 1,
        'description': "Mutual inductance",
        'input_unit': '', 'target_unit': ''
    },


    'f_start': {
        'default': 1, 'min': 1, 'max': 1000,
        'description': "Start frequency in Hertz",
        'input_unit': 'hertz', 'target_unit': 'hertz'
    },
    'f_stop': {
        'default': 100000, 'min': 1000, 'max': 100000,
        'description': "Stop frequency in Hertz",
        'input_unit': 'hertz', 'target_unit': 'hertz'
    },
    'nb_points_per_decade': {
        'default': 100, 'min': 10, 'max': 1000,
        'description': "Number of points per decade",
        'input_unit': '', 'target_unit': ''
    },
}


class CalculationThread(QThread):
    calculation_finished = pyqtSignal(object)
    calculation_failed = pyqtSignal(str)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    def run(self):
        try:
            calculation_result = self.controller.run_calculation()
            self.calculation_finished.emit(calculation_result)  # Emit result
        except Exception as e:
            self.calculation_failed.emit(str(e))  # Emit error message

class MplCanvas(FigureCanvas):
    def __init__(self):
        fig = Figure(figsize=(5, 4), dpi=100)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


class MainGUI(QMainWindow):
    """
        The MainGUI class is responsible for creating and managing the graphical user interface of the PLASMAG application.
        It sets up input fields for parameters, sliders for adjustments, a plotting area for visualization, and initiates calculations.

        Attributes:
            currently_selected_input (tuple): A tuple containing the currently selected QLineEdit and its parameter name.
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
        self.setWindowTitle("PLASMAG")
        self.setGeometry(100, 100, 2560, 1440)  # Adjust size as needed

        self.f_start_value = input_parameters['f_start']['default']
        self.f_stop_value = input_parameters['f_stop']['default']

        self.currently_selected_input = None
        self.init_ui()

        self.showMaximized()
    def init_parameters_input(self):
        row = 0  # Initialize grid row

        # Dynamically create input fields for parameters
        self.inputs = {}
        for idx, (parameter, attrs) in enumerate(input_parameters.items()):
            if parameter in ['f_start', 'f_stop']:
                continue

            label = QLabel(f"{parameter}:")
            line_edit = QLineEdit(str(attrs['default']))
            line_edit.setToolTip(attrs['description'])
            self.inputs[parameter] = line_edit

            line_edit.textChanged.connect(lambda _, le=line_edit, param=parameter: self.validate_input(le, param))

            # Calculate row and column positions
            col = (idx % 2) * 2  # This alternates between 0 for the first column and 2 for the second column
            if idx % 2 == 0 and idx != 0:
                row += 1  # Only increment row when filling the second column

            # Add label and line edit to the grid.
            # Labels in column 'col', line edits in column 'col+1'
            self.grid_layout.addWidget(label, row, col)  # Add label
            self.grid_layout.addWidget(line_edit, row, col + 1)  # Add line edit

        self.params_layout.addLayout(self.grid_layout)

    def init_sliders(self):
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
        self.frequency_range_slider.setMinimum(input_parameters['f_start']['min'])
        self.frequency_range_slider.setMaximum(input_parameters['f_stop']['max'])
        self.frequency_range_slider.setValue((input_parameters['f_start']["default"], input_parameters['f_stop']["default"]))
        self.frequency_range_slider.valueChanged.connect(self.update_frequency_range)
        self.grid_layout.addWidget(self.frequency_range_slider, 2, 1)

        self.frequency_values_label = QLabel(
            f"F_start : {input_parameters['f_start']['default']}, F_stop: {input_parameters['f_stop']['default']}")
        self.grid_layout.addWidget(self.frequency_values_label, 3, 0, 1, 2)

        # Set the spacing between elements in the grid
        self.grid_layout.setSpacing(5)

        # Add the grid layout to the main layout
        self.params_layout.addLayout(self.grid_layout)

    def init_timer(self):
        self.calculation_timer = QTimer(self)
        self.calculation_timer.setInterval(50)  # Delay in milliseconds
        self.calculation_timer.setSingleShot(True)
        self.calculation_timer.timeout.connect(self.delayed_calculate)

    def init_controller(self):
        self.controller = CalculationController()

        for parameter, line_edit in self.inputs.items():
            line_edit.mousePressEvent = lambda event, le=line_edit, param=parameter: self.bind_slider_to_input(le,
                                                                                                               param)
            line_edit.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        self.slider_precision = 100

    def init_canvas(self):
        self.canvases = [MplCanvas() for _ in range(3)]
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

            # Ajout du canvas au canvas_layout
            canvas_layout.addWidget(canvas)

            left_spacer = QSpacerItem(1, 1, QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
            top_layout.addSpacerItem(left_spacer)

            # Ajout du canvas_layout complet au plot_layout principal
            self.plot_layout.addLayout(canvas_layout)
    def init_ui(self):
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
        linear_start, linear_stop = value
        slider_min = self.frequency_range_slider.minimum()
        slider_max = self.frequency_range_slider.maximum()
        freq_min = input_parameters['f_start']['min']
        freq_max = input_parameters['f_stop']['max']
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
        It sets the sliders' ranges based on the parameter's defined range and adjusts them to reflect the input's current value.

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
            # Check if input is a valid float with scientific notation
            try:
                value = float(text[:-1]) if text.endswith('a') else float(text)
            except ValueError:
                # Invalid input, notify the user or handle as appropriate
                print(f"Invalid input for parameter '{parameter}': '{text}'. Skipping slider binding.")
                return

        range_info = input_parameters.get(parameter, {'min': 0, 'max': 100})

        # Coarse slider setup
        self.global_slider_coarse.setMinimum(range_info['min'])
        self.global_slider_coarse.setMaximum(range_info['max'])
        self.global_slider_coarse.setValue(int(value))

        # Fine slider setup
        decimal_part = value - int(value)
        self.global_slider_fine.setMinimum(0)
        self.global_slider_fine.setMaximum(999)
        self.global_slider_fine.setValue(int(decimal_part * 1000))

    def adjust_slider_properties(self, parameter):
        """
                Adjusts the properties (minimum, maximum, and current value) of the global sliders based on the selected parameter.
                This method is crucial for ensuring that the sliders provide a meaningful and constrained range of adjustment
                for the parameter's value.

                Args:
                    parameter (str): The name of the parameter for which to adjust the slider properties.

                Note:
                    The coarse slider is adjusted to cover the entire range of the parameter, allowing for broad adjustments.
                    The fine slider is designed to fine-tune the parameter value, focusing on the decimal part for precise control.
        """
        if parameter in input_parameters:
            range_info = input_parameters[parameter]
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
               the integral part from the coarse slider and the decimal part from the fine slider, maintaining precision.
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
        Gathers the current parameter values from the input fields, initiates the calculation process through the controller,
        and triggers the plotting of the results. Uses unit conversion for parameters requiring it.
        """
        # Retrieve parameters from inputs and convert units where necessary
        params_dict = {}
        for param, attrs in input_parameters.items():
            if param in self.inputs:  # Check if param has a corresponding QLineEdit
                text = self.inputs[param].text()
                try:
                    value = float(text)


                    # Convert units if required
                    input_unit = attrs.get('input_unit', '')
                    target_unit = attrs.get('target_unit', '')

                    # Perform unit conversion if both input and target units are provided
                    if input_unit and target_unit:
                        value_converted = convert_unit(value, input_unit, target_unit)
                    else:
                        value_converted = value
                    params_dict[param] = value_converted


                except ValueError:
                    print(f"Invalid input for parameter '{param}': '{text}'. Skipping calculation.")
                    return
            elif param in ['f_start', 'f_stop']:  # Directly use the values for f_start and f_stop
                params_dict[param] = getattr(self, f"{param}_value")

        # Example of using converted values (assuming you have a controller method setup)
        # This is where you would typically use params_dict with converted values for calculations
        if hasattr(self.controller, 'update_parameters'):
            self.controller.update_parameters(params_dict)

        self.calculation_thread = CalculationThread(self.controller)
        self.calculation_thread.calculation_finished.connect(self.on_calculation_finished)

        self.calculation_thread.calculation_failed.connect(
            self.display_error)
        self.calculation_thread.start()

    def on_calculation_finished(self, calculation_results):
        self.latest_results = calculation_results  # Store the latest results
        self.plot_results(calculation_results)
        print("Calculation completed successfully.")

    def display_error(self, error_message):
        # Show an error message to the user
        print(f"Calculation failed: {error_message}")
        # TODO: use a QMessageBox for GUI error display

    def update_plot(self, index):
        for i, (canvas, combo_box, checkbox) in enumerate(zip(self.canvases, self.comboboxes, self.checkboxes)):
            selected_key = combo_box.currentText()
            if not selected_key:  # In case the combo box is empty
                continue

            current_results = self.controller.get_current_results()
            old_results = self.controller.get_old_results()  # Assume you have a method to get old results

            if current_results is None:
                print("No current calculation results available.")
                continue

            current_data = current_results.get(selected_key)

            canvas.axes.clear()

            if current_data is not None:
                if np.isscalar(current_data):
                    # Scalar data plotting
                    canvas.axes.axhline(y=current_data, color='r', label='Current ' + selected_key)
                elif current_data.ndim == 1:
                    # 1D Vector data plotting
                    canvas.axes.plot(current_data, label='Current ' + selected_key)
                elif current_data.ndim > 1:
                    # 2D Vector data plotting (assumes [X, Y] format)
                    x_data = current_data[:, 0]
                    y_data = current_data[:, 1]
                    canvas.axes.plot(x_data, y_data, label='Current ' + selected_key)
                    with warnings.catch_warnings():
                        warnings.simplefilter("error", UserWarning)  # Convert warnings to errors
                        try:
                            canvas.axes.set_yscale('log')
                        except UserWarning:
                            canvas.axes.set_yscale('linear')

                # Repeat plotting logic for old data if checkbox is checked
            if checkbox.isChecked() and old_results:
                old_data = old_results.get(selected_key)
                if old_data is not None:
                    if np.isscalar(old_data):
                        canvas.axes.axhline(y=old_data, color='g', label='Old ' + selected_key)
                    elif old_data.ndim == 1:
                        canvas.axes.plot(old_data, label='Old ' + selected_key, linestyle='--')
                    elif old_data.ndim > 1:
                        old_x_data = old_data[:, 0]
                        old_y_data = old_data[:, 1]
                        canvas.axes.plot(old_x_data, old_y_data, label='Old ' + selected_key, linestyle='--')

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
        This method provides a way to quickly revert any changes made by the user to the initial state.
        """
        # Reset each input field to its default value
        for parameter, line_edit in self.inputs.items():
            if parameter in input_parameters:
                default_value = str(input_parameters[parameter]['default'])
                line_edit.setText(default_value)

                # If the currently selected input is being reset, update the sliders too
                if self.currently_selected_input and self.currently_selected_input[1] == parameter:
                    self.bind_slider_to_input(line_edit, parameter)

        # Optionally, trigger a recalculation if you want immediate feedback on the reset values
        self.calculate()

    def validate_input(self, line_edit, parameter):
        """
        Validates the input of a QLineEdit widget, ensuring it's a valid number within the specified range.
        Sets the background to red if invalid and corrects the value if out of range.
        """
        text = line_edit.text()
        try:
            value = float(text)
            min_val = input_parameters[parameter]['min']
            max_val = input_parameters[parameter]['max']

            # Correct the value if it's out of range
            if value < min_val:
                value = min_val
                line_edit.setText(str(value))
            elif value > max_val:
                value = max_val
                line_edit.setText(str(value))

            # Reset the background color if input is valid
            line_edit.setStyleSheet("")
        except ValueError:
            # Set the background color to red if input is invalid
            line_edit.setStyleSheet("background-color: #ffaaaa;")

        except Exception as e:
            print("Error validating input:", e)



def load_stylesheet(file_path):
    with open(file_path, "r") as file:
        return file.read()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainGUI()
    window.show()
    sys.exit(app.exec())


