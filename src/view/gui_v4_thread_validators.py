import sys

import numpy as np
from PyQt6.QtCore import Qt, QTimer, QThread
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QLabel, \
    QGridLayout, QSlider, QCheckBox
from isort.profiles import attrs

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.controler.controller import CalculationController
from qtrangeslider import QRangeSlider


# Default parameter values and ranges for the GUI
# TODO: Move this to a separate file


# dict parameters that is a merge of default_values and parameter_ranges

input_parameters = {
    'mu_insulator': {'default': 1, 'min': 0, 'max': 10},
    'len_coil': {'default': 155, 'min': 1, 'max': 200},
    'kapthon_thick': {'default': 30, 'min': 10, 'max': 300},
    'insulator_thick': {'default': 10, 'min': 1, 'max': 100},
    'diam_out_mandrel': {'default': 3.2, 'min': 1, 'max': 10},
    'diam_wire': {'default': 90, 'min': 10, 'max': 300},
    'capa_tuning': {'default': 1, 'min': 1, 'max': 1000},
    'capa_triwire': {'default': 150, 'min': 10, 'max': 1000},
    'len_core': {'default': 20, 'min': 1, 'max': 200},
    'diam_core': {'default': 3.2, 'min': 1, 'max': 100},
    'mu_r': {'default': 100000, 'min': 1, 'max': 1000000},
    'nb_spire': {'default': 12100, 'min': 1000, 'max': 20000},
    'ray_spire': {'default': 5, 'min': 1, 'max': 100},
    'rho_whire': {'default': 1.6, 'min': 1, 'max': 10},
    'coeff_expansion': {'default': 1, 'min': 1, 'max': 10},

    'f_start': {'default': 1, 'min': 1, 'max': 1000},
    'f_stop': {'default': 100000, 'min': 1000, 'max': 100000},
    'nb_points_per_decade': {'default': 100, 'min': 10, 'max': 1000},

}


class CalculationThread(QThread):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    def run(self):
        self.controller.run_calculation()

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
        self.setGeometry(100, 100, 800, 950)  # Adjust size as needed

        self.f_start_value = input_parameters['f_start']['default']
        self.f_stop_value = input_parameters['f_stop']['default']

        self.currently_selected_input = None
        self.init_ui()


    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        self.calculation_timer = QTimer(self)
        self.calculation_timer.setInterval(50)  # Delay in milliseconds
        self.calculation_timer.setSingleShot(True)
        self.calculation_timer.timeout.connect(self.delayed_calculate)

        # Grid layout for parameters
        self.grid_layout = QGridLayout()
        self.init_parameters_input()

        # Add Reset Parameters button
        self.reset_params_btn = QPushButton('Reset Parameters')
        self.reset_params_btn.clicked.connect(self.reset_parameters)
        self.main_layout.addWidget(self.reset_params_btn)

        # Calculate button
        self.calculate_btn = QPushButton('Calculate')
        self.calculate_btn.clicked.connect(self.calculate)
        self.main_layout.addWidget(self.calculate_btn)


        self.init_sliders()

        self.show_old_curve_checkbox = QCheckBox("Show Old Curve")
        self.main_layout.addWidget(self.show_old_curve_checkbox)

        self.show_old_curve_checkbox.stateChanged.connect(self.trigger_replot)

        # Plot area
        self.canvas = MplCanvas()
        self.main_layout.addWidget(self.canvas)

        self.controller = CalculationController()

        for parameter, line_edit in self.inputs.items():
            line_edit.mousePressEvent = lambda event, le=line_edit, param=parameter: self.bind_slider_to_input(le,
                                                                                                               param)
            line_edit.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        self.slider_precision = 100

    def trigger_replot(self):
        # Trigger the plot update
        self.plot_results()

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
        and triggers the plotting of the results. This function acts as the bridge between user input and the calculation logic,
        ensuring that the most up-to-date parameters are used for each calculation.
        """
        # Retrieve parameters from inputs
        params_dict = {
            'f_start': self.f_start_value,
            'f_stop': self.f_stop_value
        }
        for param, line_edit in self.inputs.items():
            text = line_edit.text()
            try:
                value = float(text)
                params_dict[param] = value
            except ValueError:
                # Check if input is a valid float with scientific notation
                try:
                    value = float(text[:-1]) if text.endswith('a') else float(text)
                    params_dict[param] = value
                except ValueError:
                    # Invalid input, notify the user or handle as appropriate
                    print(f"Invalid input for parameter '{param}': '{text}'. Skipping calculation.")
                    return

        # Convert other parameters requiring scientific notation
        params_dict['len_coil'] *= 10 ** -3
        params_dict['kapthon_thick'] *= 10 ** -6
        params_dict['insulator_thick'] *= 10 ** -6
        params_dict['diam_out_mandrel'] *= 10 ** -3
        params_dict['diam_wire'] *= 10 ** -6
        params_dict['capa_tuning'] *= 10 ** -12
        params_dict['capa_triwire'] *= 10 ** -12
        params_dict['len_core'] *= 10 ** -2
        params_dict['diam_core'] *= 10 ** -3
        params_dict['ray_spire'] *= 10 ** -3

        self.controller.update_parameters(params_dict)

        # Create and start the calculation thread
        self.calculation_thread = CalculationThread(self.controller)
        self.calculation_thread.finished.connect(self.plot_results)
        self.calculation_thread.start()

    def plot_results(self):
        """
        Retrieves the latest calculation results and plots them on the matplotlib canvas. This function is responsible
        for visualizing the impedance vs. frequency graph, allowing users to analyze the calculation outcomes.
        It handles the plotting of both the current and previous calculation results, providing a comparative view.
        """
        self.canvas.axes.clear()

        impedance_results = self.controller.engine.current_output_data.get_result('impedance')
        if impedance_results is not None:
            impedance = impedance_results[:, 1]
            frequencies = impedance_results[:, 0]
            self.canvas.axes.plot(frequencies, impedance, label='Current Impedance')
            self.canvas.axes.set_xlabel('Frequency (Hz)')
            self.canvas.axes.set_ylabel('Impedance')
            self.canvas.axes.set_xscale('log')
            self.canvas.axes.set_yscale('log')
            self.canvas.axes.grid(which='both')

        if self.show_old_curve_checkbox.isChecked():
            old_impedance_results = self.controller.engine.old_output_data.get_result('impedance')
            if old_impedance_results is not None:
                old_impedance = old_impedance_results[:, 1]
                old_frequencies = old_impedance_results[:, 0]
                self.canvas.axes.plot(old_frequencies, old_impedance, label='Old Impedance')

        self.canvas.axes.legend()
        self.canvas.draw()

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
        Validates the input of a QLineEdit widget.
        """
        text = line_edit.text()
        try:
            value = float(text)
            attrs = input_parameters[parameter]
            if value < attrs['min']:
                value = attrs['min']
            elif value > attrs['max']:
                value = attrs['max']
            line_edit.setText(str(value))
            line_edit.setStyleSheet("")
        except ValueError:
            line_edit.setStyleSheet("background-color: red;")

        except Exception as e:
            print("Error:", e)

    def init_parameters_input(self):
        row = 0  # Initialize grid row

        # Dynamically create input fields for parameters
        self.inputs = {}
        for idx, (parameter, attrs) in enumerate(input_parameters.items()):
            if parameter in ['f_start', 'f_stop']:
                continue

            label = QLabel(f"{parameter}:")
            line_edit = QLineEdit(str(attrs['default']))
            self.inputs[parameter] = line_edit

            line_edit.textChanged.connect(lambda text, le=line_edit, param=parameter: self.validate_input(le, param))

            # Calculate row and column positions
            col = (idx % 2) * 2  # This alternates between 0 for the first column and 2 for the second column
            if idx % 2 == 0 and idx != 0:
                row += 1  # Only increment row when filling the second column

            # Add label and line edit to the grid.
            # Labels in column 'col', line edits in column 'col+1'
            self.grid_layout.addWidget(label, row, col)  # Add label
            self.grid_layout.addWidget(line_edit, row, col + 1)  # Add line edit

        self.main_layout.addLayout(self.grid_layout)

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

        frequency_range_slider_label = QLabel("Plage de fréquence :")
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
        self.main_layout.addLayout(self.grid_layout)


def load_stylesheet(file_path):
    with open(file_path, "r") as file:
        return file.read()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainGUI()
    window.show()
    sys.exit(app.exec())


