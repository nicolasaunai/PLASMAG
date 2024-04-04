import numpy as np
from src.model.input_parameters import InputParameters
from src.model.strategies import CalculationStrategy
from scipy.constants import mu_0


# TODO : IMPLEMENTED from legacy code, need to be checked and corrected with the equations
class OLTF_Strategy_Non_Filtered(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        nb_spire = parameters.data['nb_spire']
        ray_spire = parameters.data['ray_spire']

        mu_app = dependencies['mu_app']['data']
        frequency_vector = dependencies['frequency_vector']['data']
        linear_TF_ASIC_Stage_1 = dependencies['TF_ASIC_Stage_1']['data'][:,1]
        inductance = dependencies['inductance']['data']
        capacitance = dependencies['capacitance']['data']
        resistance = dependencies['resistance']['data']

        vectorized_oltf = np.vectorize(self.calculate_oltf)
        oltf_values = vectorized_oltf(nb_spire, ray_spire, mu_app, frequency_vector, linear_TF_ASIC_Stage_1, inductance, capacitance, resistance)

        frequency_oltf_tensor = np.column_stack((frequency_vector, oltf_values))
        value =  frequency_oltf_tensor

        return {
            "data": value,
            "labels": ["Frequency", "Gain"],
            "units": ["Hz", ""]
        }

    def calculate_oltf(self,
                       nb_spire,
                       ray_spire,
                       mu_app,
                       f,
                       TF_ASIC_Stage_1_point, L, C, R):

        result = (nb_spire * (np.pi * (ray_spire)**2) * mu_app * 4 * np.pi * 10**-7 * TF_ASIC_Stage_1_point * (2* np.pi * f)) / ((1- L * C * (2*np.pi*f)**2)**2 + ((R * C * (2*np.pi*f))**2))**0.5
        return result



    @staticmethod
    def get_dependencies():
        return ['nb_spire', 'ray_spire', 'mu_app', 'frequency_vector', 'TF_ASIC_Stage_1', 'inductance', 'capacitance', 'resistance']



class OLTF_Strategy_Filtered(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        OLTF_Non_filtered = 20*np.log10(dependencies['OLTF_Non_filtered']['data'][:,1]) # linear
        TF_ASIC_Stage_2 = 20*np.log10(dependencies['TF_ASIC_Stage_2']['data'][:,1]) # linear

        result = (OLTF_Non_filtered + TF_ASIC_Stage_2)

        result = 10**(result/20)

        result = np.column_stack((dependencies['OLTF_Non_filtered']['data'][:,0], result))

        return {
            "data": result,
            "labels": ["Frequency", "Gain"],
            "units": ["Hz", ""]
        }

    @staticmethod
    def get_dependencies():
        return ['OLTF_Non_filtered', 'TF_ASIC_Stage_2']

