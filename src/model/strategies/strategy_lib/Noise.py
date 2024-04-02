import numpy as np
from src.model.input_parameters import InputParameters
from src.model.strategies import CalculationStrategy
from scipy.constants import k

class PSD_R_cr(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        temperature = parameters.data['temperature']
        feedback_resistance = parameters.data['feedback_resistance']
        frequency_vector = dependencies['frequency_vector']
        result = self.calculate_psd(temperature, feedback_resistance)

        ones = np.ones(len(frequency_vector))
        result = result * ones
        return np.column_stack((frequency_vector, result))

    def calculate_psd(self, temperature, feedback_resistance):

        result = 4 * k * temperature * feedback_resistance
        return result**0.5

    @staticmethod
    def get_dependencies():
        return ['temperature', "feedback_resistance", "frequency_vector"]

class PSD_R_cr_filtered(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        PSD_R_cr_non_filtered = 20*np.log10(dependencies['PSD_R_cr'][:,1])
        TF_ASIC_Stage_2_linear = 20*np.log10(dependencies['TF_ASIC_Stage_2_linear'][:,1])

        result = (PSD_R_cr_non_filtered + TF_ASIC_Stage_2_linear)
        result = 10**(result/20)
        return np.column_stack((dependencies['PSD_R_cr'][:,0], result))


    @staticmethod
    def get_dependencies():
        return ['TF_ASIC_Stage_2_linear', "PSD_R_cr",]

class PSD_R_Coil(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        temperature = parameters.data['temperature']
        resistance = dependencies['resistance']
        frequency_vector = dependencies['frequency_vector']
        TF_ASIC_Stage_1_linear = dependencies['TF_ASIC_Stage_1_linear'][:,1]
        inductance = dependencies['inductance']
        capacitance = dependencies['capacitance']
        mutual_inductance = parameters.data['mutual_inductance']
        feedback_resistance = parameters.data['feedback_resistance']

        vectorized_psd_r_coil = np.vectorize(self.calculate_psd)
        psd_r_coil_values = vectorized_psd_r_coil(temperature, resistance, k, frequency_vector, TF_ASIC_Stage_1_linear, inductance, capacitance, mutual_inductance, feedback_resistance)
        frequency_psd_r_coil_tensor = np.column_stack((frequency_vector, psd_r_coil_values))
        return frequency_psd_r_coil_tensor

    def calculate_psd(self, temperature, resistance, k, f, TF_ASIC_Stage_1_point, inductance, capacitance, mutual_inductance, feedback_resistance):

        psd_r_coil_num = (4 * k * temperature * resistance) * TF_ASIC_Stage_1_point**2
        psd_r_coil_den = (
        (1 - inductance * capacitance * (2 * np.pi * f)**2)**2
        + ((resistance * capacitance * 2 * np.pi * f) + ((TF_ASIC_Stage_1_point * mutual_inductance * 2 * np.pi * f) / feedback_resistance))**2
    )

        result = (psd_r_coil_num / psd_r_coil_den)**0.5
        return result

    @staticmethod
    def get_dependencies():
        return ['temperature', "feedback_resistance", "frequency_vector", "TF_ASIC_Stage_1_linear", "inductance", "capacitance", "resistance", "mutual_inductance", "feedback_resistance", "frequency_vector"]

class PSD_R_Coil_filtered(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        PSD_R_Coil_non_filtered = 20*np.log10(dependencies['PSD_R_Coil'][:,1])
        TF_ASIC_Stage_2_linear = 20*np.log10(dependencies['TF_ASIC_Stage_2_linear'][:,1])

        result = (PSD_R_Coil_non_filtered + TF_ASIC_Stage_2_linear)
        result = 10**(result/20)
        return np.column_stack((dependencies['PSD_R_Coil'][:,0], result))

    @staticmethod
    def get_dependencies():
        return ['TF_ASIC_Stage_2_linear', "PSD_R_Coil"]


class PSD_Flicker(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        Para_A = parameters.data['Para_A']
        Para_B = parameters.data['Para_B']
        Alpha = parameters.data['Alpha']
        e_en = parameters.data['e_en']
        frequency_vector = dependencies['frequency_vector']

        vectorized_psd_flicker = np.vectorize(self.calculate_psd_flicker)
        psd_flicker_values = vectorized_psd_flicker(Para_A, Para_B, Alpha, e_en, frequency_vector)
        frequency_psd_flicker_tensor = np.column_stack((frequency_vector, psd_flicker_values))
        return frequency_psd_flicker_tensor

    @staticmethod
    def get_dependencies():
        return ['frequency_vector', "Para_A", "Para_B", "Alpha", "e_en"]

    def calculate_psd_flicker(self, Para_A, Para_B, Alpha, e_en, f):
        return Para_A * (1 / (Para_B * 10**(9) *  (f ** (Alpha/10)))) + (e_en * 10 ** (-9))

class PSD_e_en(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        PSD_Flicker = dependencies['PSD_Flicker'][:,1]
        TF_ASIC_Stage_1_linear = dependencies['TF_ASIC_Stage_1_linear'][:,1]
        inductance = dependencies['inductance']
        capacitance = dependencies['capacitance']
        frequency_vector = dependencies['frequency_vector']
        resistance = dependencies['resistance']
        feedback_resistance = parameters.data['feedback_resistance']
        mutual_inductance = parameters.data['mutual_inductance']

        vectorized_psd_e_en = np.vectorize(self.calculate_psd_e_en)
        psd_e_en_values = vectorized_psd_e_en(PSD_Flicker, TF_ASIC_Stage_1_linear, inductance, capacitance, frequency_vector, resistance, feedback_resistance, mutual_inductance)
        frequency_psd_e_en_tensor = np.column_stack((frequency_vector, psd_e_en_values))
        return frequency_psd_e_en_tensor

    def calculate_psd_e_en(self, PSD_Flicker_point, TF_ASIC_Stage_1_point, L, C, f, R, feedback_resistance, mutual_inductance):
        PSD_e_en_Num = (
                (PSD_Flicker_point ** 2 * TF_ASIC_Stage_1_point ** 2)
                * ((1 - L * C * (2 * np.pi * f) ** 2) ** 2 + (
                    R * C * 2 * np.pi * f) ** 2)
        )

        PSD_e_en_Den = (
                (1 - L * C * (2 * np.pi * f) ** 2) ** 2
                + ((R * C * 2 * np.pi * f) + (
                    (TF_ASIC_Stage_1_point * mutual_inductance * 2 * np.pi * f) / feedback_resistance)) ** 2
        )

        return (PSD_e_en_Num / PSD_e_en_Den) ** 0.5

    @staticmethod
    def get_dependencies():
        return ['PSD_Flicker', 'TF_ASIC_Stage_1_linear', 'inductance', 'capacitance', 'frequency_vector', 'resistance', 'feedback_resistance', 'mutual_inductance']

class PSD_e_en_filtered(CalculationStrategy):

        def calculate(self, dependencies: dict, parameters: InputParameters):
            PSD_e_en = 20*np.log10(dependencies['PSD_e_en'][:,1])
            TF_ASIC_Stage_2_linear = 20*np.log10(dependencies['TF_ASIC_Stage_2_linear'][:,1])

            result = (PSD_e_en + TF_ASIC_Stage_2_linear)
            result = 10**(result/20)
            return np.column_stack((dependencies['PSD_e_en'][:,0], result))

        @staticmethod
        def get_dependencies():
            return ['TF_ASIC_Stage_2_linear', "PSD_e_en"]


class PSD_e_in(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        impedance = dependencies['impedance'][:,1]
        e_in = parameters.data['e_in']
        frequency_vector = dependencies['frequency_vector']
        TF_ASIC_Stage_1_linear = dependencies['TF_ASIC_Stage_1_linear'][:,1]
        capacitance = dependencies['capacitance']
        resistance = dependencies['resistance']
        inductance = dependencies['inductance']
        feedback_resistance = parameters.data['feedback_resistance']
        mutual_inductance = parameters.data['mutual_inductance']

        vectorized_psd_e_in = np.vectorize(self.calculate_psd_e_in)
        psd_e_in_values = vectorized_psd_e_in(impedance, e_in, frequency_vector, TF_ASIC_Stage_1_linear, inductance, capacitance, resistance, feedback_resistance, mutual_inductance)
        frequency_psd_e_in_tensor = np.column_stack((frequency_vector, psd_e_in_values))
        return frequency_psd_e_in_tensor

    def calculate_psd_e_in(self, impedance_point, e_in, f, TF_ASIC_Stage_1_point, L, C, R, feedback_resistance, mutual_inductance):
        PSD_e_in_Num = impedance_point ** 2 * (e_in * 1e-15) ** 2 * TF_ASIC_Stage_1_point ** 2 * (
                (1 - L * C * (2 * np.pi * f) ** 2) ** 2 + (
                    R * C * 2 * np.pi * f) ** 2
        )

        PSD_e_in_Den = (
                (1 - L * C * (2 * np.pi * f) ** 2) ** 2
                + ((R * C * 2 * np.pi * f) + (
                    (TF_ASIC_Stage_1_point * mutual_inductance * 2 * np.pi * f) / feedback_resistance)) ** 2
        )

        return (PSD_e_in_Num / PSD_e_in_Den) ** 0.5

    @staticmethod
    def get_dependencies():
        return ['impedance', 'e_in', 'frequency_vector', 'TF_ASIC_Stage_1_linear', 'inductance', 'capacitance', 'resistance', 'feedback_resistance', 'mutual_inductance']

class PSD_e_in_filtered(CalculationStrategy):

        def calculate(self, dependencies: dict, parameters: InputParameters):
            PSD_e_in = 20*np.log10(dependencies['PSD_e_in'][:,1])
            TF_ASIC_Stage_2_linear = 20*np.log10(dependencies['TF_ASIC_Stage_2_linear'][:,1])

            result = (PSD_e_in + TF_ASIC_Stage_2_linear)
            result = 10**(result/20)
            return np.column_stack((dependencies['PSD_e_in'][:,0], result))

        @staticmethod
        def get_dependencies():
            return ['TF_ASIC_Stage_2_linear', "PSD_e_in"]

class PSD_Total(CalculationStrategy):
    def calculate(self, dependencies: dict, parameters: InputParameters):
        PSD_e_in = dependencies['PSD_e_in'][:,1]
        PSD_e_en = dependencies['PSD_e_en'][:,1]
        PSD_R_Coil = dependencies['PSD_R_Coil'][:,1]
        PSD_R_cr = dependencies['PSD_R_cr'][:,1]
        frequency_vector = dependencies['frequency_vector']

        result = (PSD_e_in**2 + PSD_e_en**2 + PSD_R_Coil**2 + PSD_R_cr**2)**0.5
        return np.column_stack((frequency_vector, result))

    @staticmethod
    def get_dependencies():
        return ['PSD_e_in', 'PSD_e_en', 'PSD_R_Coil', 'PSD_R_cr', 'frequency_vector']

class Display_all_PSD(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        PSD_e_in = dependencies['PSD_e_in'][:,1]
        PSD_e_en = dependencies['PSD_e_en'][:,1]
        PSD_R_Coil = dependencies['PSD_R_Coil'][:,1]
        PSD_R_cr = dependencies['PSD_R_cr'][:,1]
        PSD_Total = dependencies['PSD_Total'][:,1]
        frequency_vector = dependencies['frequency_vector']

        return np.column_stack((frequency_vector, PSD_R_cr, PSD_R_Coil, PSD_e_en, PSD_e_in, PSD_Total))

    @staticmethod
    def get_dependencies():
        return ['PSD_e_in', 'PSD_e_en', 'PSD_R_Coil', 'PSD_R_cr', 'frequency_vector', "PSD_Total"]


class PSD_Total_filtered(CalculationStrategy):

        def calculate(self, dependencies: dict, parameters: InputParameters):
            PSD_Total = 20*np.log10(dependencies['PSD_Total'][:,1])
            TF_ASIC_Stage_2_linear = 20*np.log10(dependencies['TF_ASIC_Stage_2_linear'][:,1])

            result = (PSD_Total + TF_ASIC_Stage_2_linear)
            result = 10**(result/20)
            return np.column_stack((dependencies['PSD_Total'][:,0], result))

        @staticmethod
        def get_dependencies():
            return ['TF_ASIC_Stage_2_linear', "PSD_Total"]


class NEMI(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        PSD_Total = dependencies['PSD_Total'][:,1]
        CLTF_Non_filtered = dependencies['CLTF_Non_filtered'][:,1]
        frequency_vector = dependencies['frequency_vector']

        PSD_Total = 20*np.log10(PSD_Total)
        CLTF_Non_filtered = 20*np.log10(CLTF_Non_filtered)

        result = (PSD_Total - CLTF_Non_filtered)

        result = 10**(result/20)

        return np.column_stack((frequency_vector, result))

    @staticmethod
    def get_dependencies():
        return ['PSD_Total', 'CLTF_Non_filtered', 'frequency_vector']
