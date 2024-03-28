import numpy as np
from src.model.input_parameters import InputParameters
from src.model.strategies import CalculationStrategy
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
        coeff_expansion = parameters.data['coeff_expansion']
        nb_spire = parameters.data['nb_spire']

        mu_app = dependencies['mu_app']

        nb_spire_per_layer = int(len_coil / (diam_wire * coeff_expansion))
        nb_layer = int(nb_spire / nb_spire_per_layer) + 1

        return (
                (np.pi * (mu_0 * 4 * np.pi * 10**-7) * mu_insulator * len_coil) /
                ((kapthon_thick + 2 * insulator_thick) * nb_layer ** 2)
                * ((nb_layer - 1) * diam_out_mandrel * 1 / 2 + nb_layer * (nb_layer - 1) * (
                    diam_wire * kapthon_thick) / 2)
                + capa_tuning + capa_triwire
        )

    @staticmethod
    def get_dependencies():
        return ['mu_insulator', 'len_coil', 'kapthon_thick', 'insulator_thick', 'diam_out_mandrel',
                'diam_wire', 'capa_tuning', 'capa_triwire', 'coeff_expansion', 'nb_spire', 'mu_app']
