import numpy as np
from src.model.input_parameters import InputParameters
from src.model.strategies import CalculationStrategy
class AnalyticalResistanceStrategy(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        N = parameters.data['nb_spire']
        Rs = parameters.data['ray_spire']
        rho = parameters.data['rho_whire']
        return N * (2 * np.pi * Rs) * rho

    @staticmethod
    def get_dependencies():
        return ['nb_spire', 'ray_spire', 'rho_whire']