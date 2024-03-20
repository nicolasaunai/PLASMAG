import numpy as np
from src.model.input_parameters import InputParameters
from src.model.strategies import CalculationStrategy
from scipy.constants import mu_0

class TF_ASIC_Stage_1_Strategy(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        gain_1 = parameters.data['gain_1'] # Gain of the first stage in dB
        stage_1_cutting_freq = parameters.data['stage_1_cutting_freq'] # Cutting frequency of the first stage in Hz
        frequency_vector = dependencies['frequency_vector']

        vectorized_tf_stage_1 = np.vectorize(self.calculate_tf_stage_1)
        tf_stage_1_values = vectorized_tf_stage_1(gain_1, stage_1_cutting_freq, frequency_vector)


        frequency_tf_stage_1_tensor = np.column_stack((frequency_vector, tf_stage_1_values))
        return frequency_tf_stage_1_tensor
    def calculate_tf_stage_1(self, gain_1, stage_1_cutting_freq, f):
        return (gain_1 +
                (20 * np.log10(
                    (1 /
                     (1 + (f / stage_1_cutting_freq)**2))
                    )
                 )
                )


    @staticmethod
    def get_dependencies():
        return ['gain_1', 'stage_1_cutting_freq', 'frequency_vector']


class TF_ASIC_Stage_2_Strategy(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        gain_2 = parameters.data['gain_2'] # Gain of the first stage in dB
        stage_2_cutting_freq = parameters.data['stage_2_cutting_freq'] # Cutting frequency of the second stage in Hz
        frequency_vector = dependencies['frequency_vector']

        vectorized_tf_stage_2 = np.vectorize(self.calculate_tf_stage_2)
        tf_stage_2_values = vectorized_tf_stage_2(gain_2, stage_2_cutting_freq, frequency_vector)


        frequency_tf_stage_2_tensor = np.column_stack((frequency_vector, tf_stage_2_values))
        return frequency_tf_stage_2_tensor
    def calculate_tf_stage_2(self, gain_2, stage_2_cutting_freq, f):
        return (gain_2 +
                (20 * np.log10(
                    (1 /
                     (1 + (f / stage_2_cutting_freq)**2))
                    )
                 )
                )


    @staticmethod
    def get_dependencies():
        return ['gain_2', 'stage_2_cutting_freq', 'frequency_vector']


class TF_ASIC_Strategy(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        TF_ASIC_Stage_1 = dependencies['TF_ASIC_Stage_1'][:,1]
        TF_ASIC_Stage_2 = dependencies['TF_ASIC_Stage_2'][:,1]

        frequency_vector = dependencies['frequency_vector']

        TF_ASICs_tensor = np.column_stack((frequency_vector, TF_ASIC_Stage_1 + TF_ASIC_Stage_2))

        return TF_ASICs_tensor
    @staticmethod
    def get_dependencies():
        return ['TF_ASIC_Stage_1', 'TF_ASIC_Stage_2', 'frequency_vector']





class TF_ASIC_Stage_1_Strategy_linear(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        gain_1 = parameters.data['gain_1_linear'] # Gain of the first stage in dB
        stage_1_cutting_freq = parameters.data['stage_1_cutting_freq'] # Cutting frequency of the first stage in Hz
        frequency_vector = dependencies['frequency_vector']

        vectorized_tf_stage_1 = np.vectorize(self.calculate_tf_stage_1)
        tf_stage_1_values = vectorized_tf_stage_1(gain_1, stage_1_cutting_freq, frequency_vector)


        frequency_tf_stage_1_tensor = np.column_stack((frequency_vector, tf_stage_1_values))
        return frequency_tf_stage_1_tensor

    def calculate_tf_stage_1(self, gain_1, stage_1_cutting_freq, f):
        return gain_1 * (1 / np.sqrt(1 + (f / stage_1_cutting_freq) ** 2))

    @staticmethod
    def get_dependencies():
        return ['gain_1_linear', 'stage_1_cutting_freq', 'frequency_vector']


class TF_ASIC_Stage_2_Strategy_linear(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        gain_2 = parameters.data['gain_2'] # Gain of the first stage in dB
        stage_2_cutting_freq = parameters.data['stage_2_cutting_freq'] # Cutting frequency of the second stage in Hz
        frequency_vector = dependencies['frequency_vector']

        vectorized_tf_stage_2 = np.vectorize(self.calculate_tf_stage_2)
        tf_stage_2_values = vectorized_tf_stage_2(gain_2, stage_2_cutting_freq, frequency_vector)


        frequency_tf_stage_2_tensor = np.column_stack((frequency_vector, tf_stage_2_values))
        return frequency_tf_stage_2_tensor

    def calculate_tf_stage_2(self, gain_2, stage_2_cutting_freq, f):
        return gain_2 * (1 / np.sqrt(1 + (f / stage_2_cutting_freq) ** 2))

    @staticmethod
    def get_dependencies():
        return ['gain_2_linear', 'stage_2_cutting_freq', 'frequency_vector']


class TF_ASIC_Strategy_linear(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        TF_ASIC_Stage_1_linear = dependencies['TF_ASIC_Stage_1_linear'][:,1]
        TF_ASIC_Stage_2_linear = dependencies['TF_ASIC_Stage_2_linear'][:,1]

        frequency_vector = dependencies['frequency_vector']

        TF_ASICs_tensor = np.column_stack((frequency_vector, TF_ASIC_Stage_1_linear + TF_ASIC_Stage_2_linear))

        return TF_ASICs_tensor
    @staticmethod
    def get_dependencies():
        return ['TF_ASIC_Stage_1_linear', 'TF_ASIC_Stage_2_linear', 'frequency_vector']
