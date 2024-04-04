import numpy as np
from src.model.input_parameters import InputParameters
from src.model.strategies import CalculationStrategy


class AnalyticalMu_appStrategy(CalculationStrategy):
    """
    TODO: Add description
    """

    def calculate(self, dependencies: dict, parameters: InputParameters):
        mu_r = parameters.data['mu_r']
        Nz = dependencies['Nz']['data']
        result = mu_r / (1 + (Nz * (mu_r - 1)))

        return {
            "data": result,
            "labels": ["Mu_app"],
            "units": [""]
        }

    @staticmethod
    def get_dependencies():
        return ['mu_r', 'Nz']
