import numpy as np
from src.model.input_parameters import InputParameters
from src.model.strategies import CalculationStrategy
from scipy.constants import mu_0


# TODO : IMPLEMENTED from legacy code, need to be checked and corrected with the equations
class OLTF_Strategy_Non_Filtered(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        nb_spire = parameters.data['nb_spire']
        ray_spire = parameters.data['ray_spire']
        mu_app = dependencies['mu_app']
        frequency_vector = dependencies['frequency_vector']
        TF_ASIC_Stage_1 = dependencies['TF_ASIC_Stage_1'][:,1]

        print(TF_ASIC_Stage_1.shape)
        print(frequency_vector.shape)

        linear_TF_ASIC_Stage_1 = 10**(TF_ASIC_Stage_1/20) # Convert the gain of the first stage in linear



        inductance = dependencies['inductance']
        capacitance = dependencies['capacitance']
        resistance = dependencies['resistance']

        vectorized_oltf = np.vectorize(self.calculate_oltf)
        oltf_values = vectorized_oltf(nb_spire, ray_spire, mu_app, frequency_vector, linear_TF_ASIC_Stage_1, inductance, capacitance, resistance)

        frequency_oltf_tensor = np.column_stack((frequency_vector, oltf_values))
        return frequency_oltf_tensor

    def calculate_oltf(self,
                       nb_spire,
                       ray_spire,
                       mu_app,
                       f,
                       TF_ASIC_Stage_1_point, L, C, R):

        result = (nb_spire * (np.pi * (ray_spire)**2) * mu_app * TF_ASIC_Stage_1_point * (2* np.pi * f)) / ((1- L * C * (2*np.pi*f)**2)**2 + ((R * C * (2*np.pi*f))**2))**0.5
        return result



    @staticmethod
    def get_dependencies():
        return ['nb_spire', 'ray_spire', 'mu_app', 'frequency_vector', 'TF_ASIC_Stage_1', 'inductance', 'capacitance', 'resistance']



class OLTF_Strategy_Filtered(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        OLTF_Non_filtered = dependencies['OLTF_Non_filtered'][:,1] # dB
        TF_ASIC_Stage_2 = dependencies['TF_ASIC_Stage_2'][:,1] # dB

        return OLTF_Non_filtered + TF_ASIC_Stage_2

    @staticmethod
    def get_dependencies():
        return ['OLTF_Non_filtered', 'TF_ASIC_Stage_2']

