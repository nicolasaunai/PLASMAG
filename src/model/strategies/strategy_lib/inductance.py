import numpy as np
from src.model.input_parameters import InputParameters
from src.model.strategies import CalculationStrategy

class AnalyticalInductanceStrategy(CalculationStrategy):


    def calculate(self, dependencies: dict, parameters: InputParameters):
        nb_spire = parameters.data['nb_spire']
        diam_coil = 2 * parameters.data['ray_spire']
        len_coil = parameters.data['len_coil']

        lambda_param = dependencies['lambda_param']['data']
        mu_app = dependencies['mu_app']['data']

        result = (4 * np.pi * 10**-7)* mu_app * (nb_spire ** 2) * ((np.pi * (diam_coil)**2 )/4) * lambda_param / len_coil

        return {
            "data": result,
            "labels": ["Inductance"],
            "units": ["H"]
        }
    @staticmethod
    def get_dependencies():
        return ['nb_spire', 'ray_spire', 'len_coil', 'lambda_param', 'mu_app']