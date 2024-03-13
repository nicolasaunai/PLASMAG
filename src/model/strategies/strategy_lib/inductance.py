import numpy as np
from model import InputParameters
from model.strategies import CalculationStrategy

class AnalyticalInductanceStrategy(CalculationStrategy):


    def calculate(self, dependencies: dict, parameters: InputParameters):
        nb_spire = parameters.data['nb_spire']
        diam_coil = 2 * parameters.data['ray_spire']
        len_coil = parameters.data['len_coil']

        lambda_param = dependencies['lambda_param']
        mu_app = dependencies['mu_app']

        return (4 * np.pi * 10**-7)* mu_app * (nb_spire ** 2) * ((np.pi * (diam_coil)**2 )/4) * lambda_param / len_coil
    @staticmethod
    def get_dependencies():
        return ['nb_spire', 'ray_spire', 'len_coil', 'lambda_param', 'mu_app']