import numpy as np
from src.model.input_parameters import InputParameters
from src.model.strategies import CalculationStrategy

class TF_ASIC_Stage_1_Strategy_linear(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        gain_1 = parameters.data['gain_1_linear']
        stage_1_cutting_freq = parameters.data['stage_1_cutting_freq']
        frequency_vector = dependencies['frequency_vector']['data']

        vectorized_tf_stage_1 = np.vectorize(self.calculate_tf_stage_1)
        tf_stage_1_values = vectorized_tf_stage_1(gain_1, stage_1_cutting_freq, frequency_vector)


        frequency_tf_stage_1_tensor = np.column_stack((frequency_vector, tf_stage_1_values))
        value = frequency_tf_stage_1_tensor

        return {
            "data": value,
            "labels": ["Frequency", "Gain"],
            "units": ["Hz", ""]
        }

    def calculate_tf_stage_1(self, gain_1, stage_1_cutting_freq, f):
        return gain_1 * (1 / np.sqrt(1 + (f / stage_1_cutting_freq) ** 2))

    @staticmethod
    def get_dependencies():
        return ['gain_1_linear', 'stage_1_cutting_freq', 'frequency_vector']


class TF_ASIC_Stage_2_Strategy_linear(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        gain_2 = parameters.data['gain_2_linear']
        stage_2_cutting_freq = parameters.data['stage_2_cutting_freq'] # Cutting frequency of the second stage in Hz
        frequency_vector = dependencies['frequency_vector']['data']

        vectorized_tf_stage_2 = np.vectorize(self.calculate_tf_stage_2)
        tf_stage_2_values = vectorized_tf_stage_2(gain_2, stage_2_cutting_freq, frequency_vector)


        frequency_tf_stage_2_tensor = np.column_stack((frequency_vector, tf_stage_2_values))
        value = frequency_tf_stage_2_tensor

        return {
            "data": value,
            "labels": ["Frequency", "Gain"],
            "units": ["Hz", ""]
        }

    def calculate_tf_stage_2(self, gain_2, stage_2_cutting_freq, f):
        return gain_2 * (1 / np.sqrt(1 + (f / stage_2_cutting_freq) ** 2))

    @staticmethod
    def get_dependencies():
        return ['gain_2_linear', 'stage_2_cutting_freq', 'frequency_vector']


class TF_ASIC_Strategy_linear(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        TF_ASIC_Stage_1_linear = dependencies['TF_ASIC_Stage_1']['data'][:,1]
        TF_ASIC_Stage_2 = dependencies['TF_ASIC_Stage_2']['data'][:,1]

        frequency_vector = dependencies['frequency_vector']['data']

        TF_ASICs_tensor = np.column_stack((frequency_vector, TF_ASIC_Stage_1_linear * TF_ASIC_Stage_2))

        value = TF_ASICs_tensor

        return {
            "data": value,
            "labels": ["Frequency", "Gain"],
            "units": ["Hz", ""]
        }

    @staticmethod
    def get_dependencies():
        return ['TF_ASIC_Stage_1', 'TF_ASIC_Stage_2', 'frequency_vector']
