import numpy as np
from src.model.input_parameters import InputParameters
from src.model.strategies import CalculationStrategy
from scipy.constants import mu_0


# TODO : IMPLEMENTED from legacy code, need to be checked and corrected with the equations
class CLTF_Strategy_Non_Filtered(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        nb_spire = parameters.data['nb_spire']
        ray_spire = parameters.data['ray_spire']
        mu_app = dependencies['mu_app']
        frequency_vector = dependencies['frequency_vector']
        TF_ASIC_Stage_1_linear = dependencies['TF_ASIC_Stage_1_linear'][:,1]

        inductance = dependencies['inductance']
        capacitance = dependencies['capacitance']
        resistance = dependencies['resistance']

        mutual_inductance = parameters.data['mutual_inductance']
        feedback_resistance = parameters.data['feedback_resistance']

        vectorized_oltf = np.vectorize(self.calculate_cltf)
        oltf_values = vectorized_oltf(nb_spire, ray_spire, mu_app, frequency_vector, TF_ASIC_Stage_1_linear, inductance, capacitance, resistance, mutual_inductance, feedback_resistance)

        frequency_oltf_tensor = np.column_stack((frequency_vector, oltf_values))
        return frequency_oltf_tensor

    def calculate_cltf(self,
                       nb_spire,
                       ray_spire,
                       mu_app,
                       f,
                       TF_ASIC_Stage_1_point, L, C, R,
                       mutual_inductance, feedback_resistance):
        result = (((nb_spire * (np.pi * (ray_spire)**2) * mu_app * 4 * np.pi * 10**-7 * (2* np.pi * f)) - ((2* np.pi * f) * mutual_inductance * (TF_ASIC_Stage_1_point/feedback_resistance)))**2)**0.5  / ((1- L * C * (2*np.pi*f)**2)**2 + ((R * C * (2*np.pi*f))**2))**0.5
        return result





    @staticmethod
    def get_dependencies():
        return ['nb_spire', 'ray_spire', 'mu_app', 'frequency_vector', 'TF_ASIC_Stage_1_linear', 'inductance', 'capacitance', 'resistance', 'mutual_inductance', 'feedback_resistance']

class CLTF_Strategy_Non_Filtered_legacy(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        nb_spire = parameters.data['nb_spire']
        ray_spire = parameters.data['ray_spire']
        mu_app = dependencies['mu_app']
        frequency_vector = dependencies['frequency_vector']
        TF_ASIC_Stage_1_linear = dependencies['TF_ASIC_Stage_1_linear'][:,1]

        inductance = dependencies['inductance']
        capacitance = dependencies['capacitance']
        resistance = dependencies['resistance']

        mutual_inductance = parameters.data['mutual_inductance']
        feedback_resistance = parameters.data['feedback_resistance']

        vectorized_oltf = np.vectorize(self.calculate_cltf)
        oltf_values = vectorized_oltf(nb_spire, ray_spire, mu_app, frequency_vector, TF_ASIC_Stage_1_linear, inductance, capacitance, resistance, mutual_inductance, feedback_resistance)

        frequency_oltf_tensor = np.column_stack((frequency_vector, oltf_values))
        return frequency_oltf_tensor

    def calculate_cltf(self,
                       nb_spire,
                       ray_spire,
                       mu_app,
                       f,
                       TF_ASIC_Stage_1_point, L, C, R,
                       mutual_inductance, feedback_resistance):
        result = (nb_spire * (np.pi * (ray_spire)**2) * mu_app * 4 * np.pi * 10**-7 * (2* np.pi * f)* TF_ASIC_Stage_1_point)  / ((1- L * C * (2*np.pi*f)**2)**2 + (((2*np.pi*f)*R*C + (2*np.pi*f)*mutual_inductance * TF_ASIC_Stage_1_point/feedback_resistance)**2))**0.5
        return result





    @staticmethod
    def get_dependencies():
        return ['nb_spire', 'ray_spire', 'mu_app', 'frequency_vector', 'TF_ASIC_Stage_1_linear', 'inductance', 'capacitance', 'resistance', 'mutual_inductance', 'feedback_resistance']



class CLTF_Strategy_Filtered(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        OLTF_Non_filtered = 20*np.log10(dependencies['OLTF_Non_filtered'][:,1]) # linear
        TF_ASIC_Stage_2_linear = 20*np.log10(dependencies['TF_ASIC_Stage_2_linear'][:,1]) # linear

        result = OLTF_Non_filtered + TF_ASIC_Stage_2_linear
        result = 10**(result/20)
        return np.column_stack((dependencies['OLTF_Non_filtered'][:,0], result))

    @staticmethod
    def get_dependencies():
        return ['OLTF_Non_filtered', 'TF_ASIC_Stage_2_linear']

