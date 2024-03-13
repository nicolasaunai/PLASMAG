import numpy as np
from model import InputParameters
from model.strategies import CalculationStrategy


class AnalyticalLambdaStrategy(CalculationStrategy):
    """
    TODo: Add description
    """

    def calculate(self, dependencies: dict, parameters: InputParameters):
        len_coil = parameters.data['len_coil']
        len_core = parameters.data['len_core']
        return (len_coil / len_core) ** (-2 / 5)

    @staticmethod
    def get_dependencies():
        return ['len_coil', 'len_core']
