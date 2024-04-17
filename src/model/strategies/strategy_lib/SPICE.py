import numpy as np
from src.model.input_parameters import InputParameters
from src.model.strategies import CalculationStrategy

import PySpice
import PySpice.Logging.Logging as Logging
import numpy as np
from PySpice.Spice.Netlist import Circuit, SubCircuit
from PySpice.Unit import *
from matplotlib import pyplot as plt


class SPICE_test(CalculationStrategy):
    def calculate(self, dependencies: dict, parameters: InputParameters):
        temperature = parameters.data['temperature']
        f_start = parameters.data['f_start']
        f_stop = parameters.data['f_stop']
        spice_resistance_test = parameters.data['spice_resistance_test']

        frequency_vector = dependencies['frequency_vector']['data']
        logger = Logging.setup_logging()

        # convert temperature to degrees Celsius
        temperature = temperature - 273.15

        if sys.platform.startswith("linux"):
            PySpice.Spice.Simulation.CircuitSimulator.DEFAULT_SIMULATOR = 'ngspice-subprocess'
        else:
            pass

        circuit = Circuit('AC analysis Circuit')

        circuit.model("CustomDiode", 'D', IS=4.352 @ u_nA, RS=0.6459 @ u_Ohm, BV=110 @ u_V, IBV=0.0001 @ u_V, N=1.906)

        # circuit.V('input', 'n1', circuit.gnd, 10@u_V) # DC input voltage
        Vac = circuit.SinusoidalVoltageSource("input", 'n1', circuit.gnd, amplitude=1@ u_V,
                                              frequency=100@u_Hz)  # AC input voltage
        R = circuit.R(1, 'n1', 'n2', spice_resistance_test@u_Ohm)
        C = circuit.C(1, 'n2', circuit.gnd, 1@ u_uF)
        circuit.Diode(1, 'n2', 'n3', model='CustomDiode')
        circuit.R(2, 'n3', circuit.gnd, 1 @u_kOhm)

        simulator = circuit.simulator(temperature=temperature, nominal_temperature=25)

        analysis = simulator.ac(start_frequency=f_start@ u_Hz, stop_frequency=f_stop@u_Hz, number_of_points=10,
                                variation='dec')  # 1 to 1MHz, 10 points per decade

        gain_node_1 = np.absolute(analysis.n1)
        gain_node_2 = np.absolute(analysis.n2)
        gain_node_3 = np.absolute(analysis.n3)

        analysis_freq = np.array(analysis.frequency)

        interpolated_gain_1 = np.interp(frequency_vector, analysis_freq, gain_node_1)
        interpolated_gain_2 = np.interp(frequency_vector, analysis_freq, gain_node_2)
        interpolated_gain_3 = np.interp(frequency_vector, analysis_freq, gain_node_3)

        result = np.column_stack((frequency_vector, interpolated_gain_1, interpolated_gain_2, interpolated_gain_3))

        #

        return {
            "data": result,
            "labels": ["Frequency", "Gain Node 1", "Gain Node 2", "Gain Node 3"],
            "units": ["Hz", "V/V", "V/V", "V/V"]
        }



    @staticmethod
    def get_dependencies():
        return ['frequency_vector', "f_start", "f_stop", "spice_resistance_test", "temperature"]

class SPICE_test2(CalculationStrategy):
    def calculate(self, dependencies: dict, parameters: InputParameters):
        temperature = parameters.data['temperature']
        f_start = parameters.data['f_start']
        f_stop = parameters.data['f_stop']
        spice_resistance_test = parameters.data['spice_resistance_test']

        frequency_vector = dependencies['frequency_vector']['data']
        logger = Logging.setup_logging()

        # convert temperature to degrees Celsius
        temperature = temperature - 273.15

        if sys.platform.startswith("linux"):
            PySpice.Spice.Simulation.CircuitSimulator.DEFAULT_SIMULATOR = 'ngspice-subprocess'
        else:
            pass

        circuit = Circuit('AC analysis Circuit')

        circuit.model("CustomDiode", 'D', IS=4.352 @ u_nA, RS=0.6459 @ u_Ohm, BV=110 @ u_V, IBV=0.0001 @ u_V, N=1.906)

        # circuit.V('input', 'n1', circuit.gnd, 10@u_V) # DC input voltage
        Vac = circuit.SinusoidalVoltageSource("input", 'n1', circuit.gnd, amplitude=1@ u_V,
                                              frequency=100@u_Hz)  # AC input voltage
        R = circuit.R(1, 'n1', 'n2', spice_resistance_test@u_Ohm)
        C = circuit.C(1, 'n2', circuit.gnd, 1@ u_uF)
        circuit.Diode(1, 'n2', 'n3', model='CustomDiode')
        circuit.R(2, 'n3', circuit.gnd, 1 @u_kOhm)

        simulator = circuit.simulator(temperature=temperature, nominal_temperature=25)

        analysis = simulator.ac(start_frequency=f_start@ u_Hz, stop_frequency=f_stop@u_Hz, number_of_points=10,
                                variation='dec')  # 1 to 1MHz, 10 points per decade

        gain_node_1 = np.absolute(analysis.n1)
        gain_node_2 = np.absolute(analysis.n2)
        gain_node_3 = np.absolute(analysis.n3)

        analysis_freq = np.array(analysis.frequency)

        interpolated_gain_1 = np.interp(frequency_vector, analysis_freq, gain_node_1)
        interpolated_gain_2 = np.interp(frequency_vector, analysis_freq, gain_node_2)
        interpolated_gain_3 = np.interp(frequency_vector, analysis_freq, gain_node_3)

        result = np.column_stack((frequency_vector, interpolated_gain_1, interpolated_gain_2, interpolated_gain_3))

        #

        return {
            "data": result,
            "labels": ["Frequency", "Gain Node 1", "Gain Node 2", "Gain Node 3"],
            "units": ["Hz", "V/V", "V/V", "V/V"]
        }



    @staticmethod
    def get_dependencies():
        return ['frequency_vector', "f_start", "f_stop", "spice_resistance_test", "temperature"]



