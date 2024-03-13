import numpy as np
from model import InputParameters
from model.strategies import CalculationStrategy


class AnalyticalMu_appStrategy(CalculationStrategy):
    """
    TODO: Add description
    """

    def calculate(self, dependencies: dict, parameters: InputParameters):
        mu_r = parameters.data['mu_r']
        Nz = dependencies['Nz']
        return mu_r / (1 + (Nz * (mu_r - 1)))

    @staticmethod
    def get_dependencies():
        return ['mu_r', 'Nz']
