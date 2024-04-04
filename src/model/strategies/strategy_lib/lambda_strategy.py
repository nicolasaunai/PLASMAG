import numpy as np
from src.model.input_parameters import InputParameters
from src.model.strategies import CalculationStrategy


class AnalyticalLambdaStrategy(CalculationStrategy):
    """
    TODo: Add description
    """

    def calculate(self, dependencies: dict, parameters: InputParameters):
        len_coil = parameters.data['len_coil']
        len_core = parameters.data['len_core']
        result = (len_coil / len_core) ** (-2 / 5)

        return {
            "data": result,
            "labels": ["Lambda"],
            "units": [""]
        }

    @staticmethod
    def get_dependencies():
        return ['len_coil', 'len_core']
