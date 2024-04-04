import numpy as np
from src.model.input_parameters import InputParameters
from src.model.strategies import CalculationStrategy
from scipy.constants import k

class PSD_R_cr(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        temperature = parameters.data['temperature']
        feedback_resistance = parameters.data['feedback_resistance']

        frequency_vector = dependencies['frequency_vector']["data"]
        result = self.calculate_psd(temperature, feedback_resistance)

        ones = np.ones(len(frequency_vector))
        result = result * ones
        results = np.column_stack((frequency_vector, result))

        return {
            "data": results,
            "labels": ["Frequency", "PSD_R_cr"],
            "units": ["Hz", "V/sqrt(Hz)"]
        }

    def calculate_psd(self, temperature, feedback_resistance):

        result = 4 * k * temperature * feedback_resistance
        return result**0.5

    @staticmethod
    def get_dependencies():
        return ['temperature', "feedback_resistance", "frequency_vector"]

class PSD_R_cr_filtered(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        PSD_R_cr_non_filtered = 20*np.log10(dependencies['PSD_R_cr']["data"][:,1])
        TF_ASIC_Stage_2 = 20*np.log10(dependencies['TF_ASIC_Stage_2']["data"][:,1])

        result = (PSD_R_cr_non_filtered + TF_ASIC_Stage_2)
        result = 10**(result/20)
        results = np.column_stack((dependencies['PSD_R_cr']["data"][:,0], result))

        return {
            "data": results,
            "labels": ["Frequency", "PSD_R_cr"],
            "units": ["Hz", "V/sqrt(Hz)"]
        }


    @staticmethod
    def get_dependencies():
        return ['TF_ASIC_Stage_2', "PSD_R_cr",]

class PSD_R_Coil(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        temperature = parameters.data['temperature']
        mutual_inductance = parameters.data['mutual_inductance']
        feedback_resistance = parameters.data['feedback_resistance']
        
        resistance = dependencies['resistance']["data"]
        frequency_vector = dependencies['frequency_vector']["data"]
        TF_ASIC_Stage_1 = dependencies['TF_ASIC_Stage_1']["data"][:,1]
        inductance = dependencies['inductance']["data"]
        capacitance = dependencies['capacitance']["data"]
        


        vectorized_psd_r_coil = np.vectorize(self.calculate_psd)
        psd_r_coil_values = vectorized_psd_r_coil(temperature, resistance, k, frequency_vector, TF_ASIC_Stage_1, inductance, capacitance, mutual_inductance, feedback_resistance)
        frequency_psd_r_coil_tensor = np.column_stack((frequency_vector, psd_r_coil_values))
        results = frequency_psd_r_coil_tensor
        
        return {
            "data": results,
            "labels": ["Frequency", "PSD_R_Coil"],
            "units": ["Hz", "V/sqrt(Hz)"]
        }

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
        return ['temperature', "feedback_resistance", "frequency_vector", "TF_ASIC_Stage_1", "inductance", "capacitance", "resistance", "mutual_inductance", "feedback_resistance", "frequency_vector"]

class PSD_R_Coil_filtered(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        PSD_R_Coil_non_filtered = 20*np.log10(dependencies['PSD_R_Coil']["data"][:,1])
        TF_ASIC_Stage_2 = 20*np.log10(dependencies['TF_ASIC_Stage_2']["data"][:,1])

        result = (PSD_R_Coil_non_filtered + TF_ASIC_Stage_2)
        result = 10**(result/20)
        values = np.column_stack((dependencies['PSD_R_Coil']["data"][:,0], result))

        return {
            "data": values,
            "labels": ["Frequency", "PSD_R_Coil"],
            "units": ["Hz", "V/sqrt(Hz)"]
        }

    @staticmethod
    def get_dependencies():
        return ['TF_ASIC_Stage_2', "PSD_R_Coil"]


class PSD_Flicker(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        Para_A = parameters.data['Para_A']
        Para_B = parameters.data['Para_B']
        Alpha = parameters.data['Alpha']
        e_en = parameters.data['e_en']
        frequency_vector = dependencies['frequency_vector']["data"]

        vectorized_psd_flicker = np.vectorize(self.calculate_psd_flicker)
        psd_flicker_values = vectorized_psd_flicker(Para_A, Para_B, Alpha, e_en, frequency_vector)
        frequency_psd_flicker_tensor = np.column_stack((frequency_vector, psd_flicker_values))
        values = frequency_psd_flicker_tensor

        return {
            "data": values,
            "labels": ["Frequency", "PSD_Flicker"],
            "units": ["Hz", "V/sqrt(Hz)"]
        }

    @staticmethod
    def get_dependencies():
        return ['frequency_vector', "Para_A", "Para_B", "Alpha", "e_en"]

    def calculate_psd_flicker(self, Para_A, Para_B, Alpha, e_en, f):
        return Para_A * (1 / (Para_B * 10**(9) *  (f ** (Alpha/10)))) + (e_en * 10 ** (-9))

class PSD_e_en(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        PSD_Flicker = dependencies['PSD_Flicker']["data"][:,1]
        TF_ASIC_Stage_1 = dependencies['TF_ASIC_Stage_1']["data"][:,1]

        inductance = dependencies['inductance']["data"]
        capacitance = dependencies['capacitance']["data"]
        frequency_vector = dependencies['frequency_vector']["data"]
        resistance = dependencies['resistance']["data"]

        feedback_resistance = parameters.data['feedback_resistance']
        mutual_inductance = parameters.data['mutual_inductance']

        vectorized_psd_e_en = np.vectorize(self.calculate_psd_e_en)
        psd_e_en_values = vectorized_psd_e_en(PSD_Flicker, TF_ASIC_Stage_1, inductance, capacitance, frequency_vector, resistance, feedback_resistance, mutual_inductance)
        frequency_psd_e_en_tensor = np.column_stack((frequency_vector, psd_e_en_values))
        values = frequency_psd_e_en_tensor

        return {
            "data": values,
            "labels": ["Frequency", "PSD_e_en"],
            "units": ["Hz", "V/sqrt(Hz)"]
        }

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
        return ['PSD_Flicker', 'TF_ASIC_Stage_1', 'inductance', 'capacitance', 'frequency_vector', 'resistance', 'feedback_resistance', 'mutual_inductance']

class PSD_e_en_filtered(CalculationStrategy):

        def calculate(self, dependencies: dict, parameters: InputParameters):
            PSD_e_en = 20*np.log10(dependencies['PSD_e_en']["data"][:,1])
            TF_ASIC_Stage_2 = 20*np.log10(dependencies['TF_ASIC_Stage_2']["data"][:,1])

            result = (PSD_e_en + TF_ASIC_Stage_2)
            result = 10**(result/20)
            values = np.column_stack((dependencies['PSD_e_en']["data"][:,0], result))

            return {
                "data": values,
                "labels": ["Frequency", "PSD_e_en"],
                "units": ["Hz", "V/sqrt(Hz)"]
            }

        @staticmethod
        def get_dependencies():
            return ['TF_ASIC_Stage_2', "PSD_e_en"]


class PSD_e_in(CalculationStrategy):
    def calculate(self, dependencies: dict, parameters: InputParameters):
        e_in = parameters.data['e_in']
        feedback_resistance = parameters.data['feedback_resistance']
        mutual_inductance = parameters.data['mutual_inductance']

        impedance = dependencies['impedance']["data"][:,1]
        frequency_vector = dependencies['frequency_vector']["data"]
        TF_ASIC_Stage_1 = dependencies['TF_ASIC_Stage_1']["data"][:,1]
        capacitance = dependencies['capacitance']["data"]
        resistance = dependencies['resistance']["data"]
        inductance = dependencies['inductance']["data"]


        vectorized_psd_e_in = np.vectorize(self.calculate_psd_e_in)
        psd_e_in_values = vectorized_psd_e_in(impedance, e_in, frequency_vector, TF_ASIC_Stage_1, inductance, capacitance, resistance, feedback_resistance, mutual_inductance)
        frequency_psd_e_in_tensor = np.column_stack((frequency_vector, psd_e_in_values))
        values = frequency_psd_e_in_tensor

        return {
            "data": values,
            "labels": ["Frequency", "PSD_e_in"],
            "units": ["Hz", "V/sqrt(Hz)"]
        }

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
        return ['impedance', 'e_in', 'frequency_vector', 'TF_ASIC_Stage_1', 'inductance', 'capacitance', 'resistance', 'feedback_resistance', 'mutual_inductance']

class PSD_e_in_filtered(CalculationStrategy):

        def calculate(self, dependencies: dict, parameters: InputParameters):
            PSD_e_in = 20*np.log10(dependencies['PSD_e_in']["data"][:,1])
            TF_ASIC_Stage_2 = 20*np.log10(dependencies['TF_ASIC_Stage_2']["data"][:,1])

            result = (PSD_e_in + TF_ASIC_Stage_2)
            result = 10**(result/20)
            values = np.column_stack((dependencies['PSD_e_in']["data"][:,0], result))

            return {
                "data": values,
                "labels": ["Frequency", "PSD_e_in"],
                "units": ["Hz", "V/sqrt(Hz)"]
            }


        @staticmethod
        def get_dependencies():
            return ['TF_ASIC_Stage_2', "PSD_e_in"]

class PSD_Total(CalculationStrategy):
    def calculate(self, dependencies: dict, parameters: InputParameters):
        PSD_e_in = dependencies['PSD_e_in']["data"][:,1]
        PSD_e_en = dependencies['PSD_e_en']["data"][:,1]
        PSD_R_Coil = dependencies['PSD_R_Coil']["data"][:,1]
        PSD_R_cr = dependencies['PSD_R_cr']["data"][:,1]
        frequency_vector = dependencies['frequency_vector']["data"]

        result = (PSD_e_in**2 + PSD_e_en**2 + PSD_R_Coil**2 + PSD_R_cr**2)**0.5
        values = np.column_stack((frequency_vector, result))

        return {
            "data": values,
            "labels": ["Frequency", "PSD_Total"],
            "units": ["Hz", "V/sqrt(Hz)"]
        }

    @staticmethod
    def get_dependencies():
        return ['PSD_e_in', 'PSD_e_en', 'PSD_R_Coil', 'PSD_R_cr', 'frequency_vector']

class PSD_Total_filtered(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        PSD_Total = 20 * np.log10(dependencies['PSD_Total']["data"][:, 1])
        TF_ASIC_Stage_2 = 20 * np.log10(dependencies['TF_ASIC_Stage_2']["data"][:, 1])

        result = (PSD_Total + TF_ASIC_Stage_2)
        result = 10 ** (result / 20)
        values = np.column_stack((dependencies['PSD_Total']["data"][:, 0], result))

        return {
            "data": values,
            "labels": ["Frequency", "PSD_Total"],
            "units": ["Hz", "V/sqrt(Hz)"]
        }

    @staticmethod
    def get_dependencies():
        return ['TF_ASIC_Stage_2', "PSD_Total"]


class Display_all_PSD(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        PSD_e_in = dependencies['PSD_e_in']["data"][:,1]
        PSD_e_en = dependencies['PSD_e_en']["data"][:,1]
        PSD_R_Coil = dependencies['PSD_R_Coil']["data"][:,1]
        PSD_R_cr = dependencies['PSD_R_cr']["data"][:,1]
        PSD_Total = dependencies['PSD_Total']["data"][:,1]
        frequency_vector = dependencies['frequency_vector']["data"]

        values = np.column_stack((frequency_vector, PSD_R_cr, PSD_R_Coil, PSD_e_en, PSD_e_in, PSD_Total))

        return {
            "data": values,
            "labels": ["Frequency", "PSD_R_cr", "PSD_R_Coil", "PSD_e_en", "PSD_e_in", "PSD_Total"],
            "units": ["Hz", "V/sqrt(Hz)", "V/sqrt(Hz)", "V/sqrt(Hz)", "V/sqrt(Hz)", "V/sqrt(Hz)"]
        }

    @staticmethod
    def get_dependencies():
        return ['PSD_e_in', 'PSD_e_en', 'PSD_R_Coil', 'PSD_R_cr', 'frequency_vector', "PSD_Total"]

class Display_all_PSD_filtered(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        PSD_e_in_filtered = dependencies['PSD_e_in_filtered']["data"][:,1]
        PSD_e_en_filtered = dependencies['PSD_e_en_filtered']["data"][:,1]
        PSD_R_Coil_filtered = dependencies['PSD_R_Coil_filtered']["data"][:,1]
        PSD_R_cr_filtered = dependencies['PSD_R_cr_filtered']["data"][:,1]
        PSD_Total_filtered = dependencies['PSD_Total_filtered']["data"][:,1]
        frequency_vector = dependencies['frequency_vector']["data"]

        values = np.column_stack((frequency_vector, PSD_R_cr_filtered, PSD_R_Coil_filtered, PSD_e_en_filtered, PSD_e_in_filtered, PSD_Total_filtered))

        return {
            "data": values,
            "labels": ["Frequency", "PSD_R_cr_filtered", "PSD_R_Coil_filtered", "PSD_e_en_filtered", "PSD_e_in_filtered", "PSD_Total_filtered"],
            "units": ["Hz", "V/sqrt(Hz)", "V/sqrt(Hz)", "V/sqrt(Hz)", "V/sqrt(Hz)", "V/sqrt(Hz)"]
        }

    @staticmethod
    def get_dependencies():
        return ['PSD_e_in_filtered', 'PSD_e_en_filtered', 'PSD_R_Coil_filtered', 'PSD_R_cr_filtered', 'frequency_vector', "PSD_Total_filtered"]

class NEMI(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        PSD_Total = dependencies['PSD_Total']["data"][:,1]
        CLTF_Non_filtered = dependencies['CLTF_Non_filtered']["data"][:,1]
        frequency_vector = dependencies['frequency_vector']["data"]

        PSD_Total = 20*np.log10(PSD_Total)
        CLTF_Non_filtered = 20*np.log10(CLTF_Non_filtered)

        result = (PSD_Total - CLTF_Non_filtered)

        result = 10**(result/20)

        values = np.column_stack((frequency_vector, result))

        return {
            "data": values,
            "labels": ["Frequency", "NEMI"],
            "units": ["Hz", ""]
        }

    @staticmethod
    def get_dependencies():
        return ['PSD_Total', 'CLTF_Non_filtered', 'frequency_vector']


class NEMI_FIltered(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        PSD_Total_filtered = dependencies['PSD_Total_filtered']["data"][:,1]
        CLTF_Filtered = dependencies['CLTF_Filtered']["data"][:,1]
        frequency_vector = dependencies['frequency_vector']["data"]

        PSD_Total_filtered = 20*np.log10(PSD_Total_filtered)
        CLTF_Filtered = 20*np.log10(CLTF_Filtered)

        result = (PSD_Total_filtered - CLTF_Filtered)

        result = 10**(result/20)

        values = np.column_stack((frequency_vector, result))

        return {
            "data": values,
            "labels": ["Frequency", "NEMI"],
            "units": ["Hz", ""]
        }

    @staticmethod
    def get_dependencies():
        return ['PSD_Total_filtered', 'CLTF_Filtered', 'frequency_vector']
