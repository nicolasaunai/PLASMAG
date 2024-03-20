import numpy as np
from src.model.input_parameters import InputParameters
from src.model.strategies import CalculationStrategy
from scipy.constants import mu_0

class OLTF_Strategy(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        nb_spire = parameters.data['nb_spire']
        diam_coil = parameters.data['diam_coil']
        mu_app = dependencies['mu_app']
        frequency_vector = dependencies['frequency_vector']
        TF_ASIC_Stage_1 = dependencies['TF_ASIC_Stage_1'][1,:]

        inductance = dependencies['inductance']
        capacitance = dependencies['capacitance']
        resistance = dependencies['resistance']
        mutual_inductance = parameters.data['mutual_inductance']
        feedback_resistance = parameters.data['feedback_resistance']
    def calculate_oltf(self,
                       nb_spire,
                       diam_coil,
                       mu_app,
                       f,
                       TF_ASIC_Stage_1):
        pass



    @staticmethod
    def get_dependencies():
        return ['gain_1', 'stage_1_cutting_freq', 'frequency_vector']


