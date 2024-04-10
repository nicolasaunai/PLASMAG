import numpy as np
from src.model.input_parameters import InputParameters
from src.model.strategies import CalculationStrategy
class AnalyticalResistanceStrategy(CalculationStrategy):
    def calculate(self, dependencies: dict, parameters: InputParameters):
        N = parameters.data['nb_spire']
        Rs = parameters.data['ray_spire']
        rho = parameters.data['rho_whire']
        value = N * (2 * np.pi * Rs) * rho

        return {
            "data": value,
            "labels" : ["Resistance"],
            "units" : ["Ohm"]
        }

    @staticmethod
    def get_dependencies():
        return ['nb_spire', 'ray_spire', 'rho_whire']

class AnalyticalResistanceStrategyv2(CalculationStrategy):
    def calculate(self, dependencies: dict, parameters: InputParameters):
        N = parameters.data['nb_spire']
        Rs = parameters.data['ray_spire']
        rho = parameters.data['rho_whire']
        value = N * (2 * np.pi * Rs) * rho

        return {
            "data": value/10,
            "labels" : ["Resistance"],
            "units" : ["Ohm"]
        }

    @staticmethod
    def get_dependencies():
        return ['nb_spire', 'ray_spire', 'rho_whire', "resistance"]



