import numpy as np
from src.model.input_parameters import InputParameters
from src.model.strategies import CalculationStrategy


class AnalyticalImpedanceStrategy(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        R = dependencies['resistance']['data']
        L = dependencies['inductance']['data']
        C = dependencies['capacitance']['data']

        frequency_vector = dependencies['frequency_vector']['data']


        vectorized_impedance = np.vectorize(self.calculate_impedance)
        impedance_values = vectorized_impedance(R, L, C, frequency_vector)
        frequency_impedance_tensor = np.column_stack((frequency_vector, impedance_values))
        result = frequency_impedance_tensor

        return {
            "data": result,
            "labels": ["Frequency", "Impedance"],
            "units": ["Hz", "Ohm"]
        }
    def calculate_impedance(self, R, L, C, f):
        impedance_num = (R ** 2) + (L * 2 * np.pi * f) ** 2
        impedance_den = (1 - L * C * (2 * np.pi * f) ** 2) ** 2 + (R * C * (2 * np.pi * f)) ** 2
        return np.sqrt(impedance_num / impedance_den)

    @staticmethod
    def get_dependencies():
        return ['resistance', 'inductance', 'capacitance', 'frequency_vector']
