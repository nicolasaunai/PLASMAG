import numpy as np
from model import InputParameters
from model.strategies import CalculationStrategy


class AnalyticalImpedanceStrategy(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        R = dependencies['resistance']
        L = dependencies['inductance']
        C = dependencies['capacitance']

        frequency_vector = dependencies['frequency_vector']


        vectorized_impedance = np.vectorize(self.calculate_impedance)
        impedance_values = vectorized_impedance(R, L, C, frequency_vector)

        frequency_impedance_tensor = np.column_stack((frequency_vector, impedance_values))
        return frequency_impedance_tensor
    def calculate_impedance(self, R, L, C, f):
        impedance_num = (R ** 2) + (L * 2 * np.pi * f) ** 2
        impedance_den = (1 - L * C * (2 * np.pi * f) ** 2) ** 2 + (R * C * (2 * np.pi * f)) ** 2
        return np.sqrt(impedance_num / impedance_den)

    @staticmethod
    def get_dependencies():
        return ['resistance', 'inductance', 'capacitance', 'frequency_vector']
