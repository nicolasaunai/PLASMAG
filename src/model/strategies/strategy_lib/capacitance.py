import numpy as np
from model import InputParameters
from model.strategies import CalculationStrategy
from scipy.constants import mu_0

class AnalyticalCapacitanceStrategy(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        mu_insulator = parameters.data['mu_insulator']
        len_coil = parameters.data['len_coil']
        kapthon_thick = parameters.data['kapthon_thick']
        insulator_thick = parameters.data['insulator_thick']
        diam_out_mandrel = parameters.data['diam_out_mandrel']
        diam_wire = parameters.data['diam_wire']
        capa_tuning = parameters.data['capa_tuning']
        capa_triwire = parameters.data['capa_triwire']

        lambda_param = dependencies['nb_layer']
        mu_app = dependencies['mu_app']

        return (4 * np.pi * 10**-7)* mu_app * (nb_spire ** 2) * ((np.pi * (diam_coil)**2 )/4) * lambda_param / len_coil
    @staticmethod
    def get_dependencies():
        return ['nb_spire', 'ray_spire', 'len_coil', 'lambda_param', 'mu_app']