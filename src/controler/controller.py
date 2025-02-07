"""
 src/controller/controller.py
 PLASMAG 2024 Software, LPP
"""
import importlib
import json

import numpy as np

from src.model.strategies.strategy_lib.Noise import PSD_R_cr, PSD_R_cr_filtered, PSD_R_Coil, PSD_R_Coil_filtered, \
    PSD_Flicker, PSD_e_en, PSD_e_en_filtered, PSD_e_in, PSD_e_in_filtered, PSD_Total, PSD_Total_filtered, \
    Display_all_PSD, NEMI, Display_all_PSD_filtered, NEMI_FIltered, NEMI_FIlteredv2, NEMI_FIlteredv3, PSD_R_cr_V2, \
    PSD_R_cr_filtered_V2, PSD_R_Coil_V2, PSD_R_Coil_filtered_V2, PSD_Flicker_V2, PSD_e_en_V2, PSD_e_en_filtered_V2, \
    PSD_e_in_V2, PSD_e_in_filtered_V2
from src.model.strategies.strategy_lib.CLTF import CLTF_Strategy_Filtered, \
    CLTF_Strategy_Non_Filtered_legacy, Display_CLTF_OLTF
from src.model.strategies.strategy_lib.OLTF import OLTF_Strategy_Non_Filtered, OLTF_Strategy_Filtered
from src.model.strategies.strategy_lib.TF_ASIC import TF_ASIC_Stage_1_Strategy_linear,  \
    TF_ASIC_Stage_2_Strategy_linear, TF_ASIC_Strategy_linear
from src.model.input_parameters import InputParameters
from src.model.engine import CalculationEngine
from src.model.strategies.strategy_lib.Nz import AnalyticalNzStrategy
from src.model.strategies.strategy_lib.capacitance import AnalyticalCapacitanceStrategy
from src.model.strategies.strategy_lib.frequency import FrequencyVectorStrategy
from src.model.strategies.strategy_lib.impedance import AnalyticalImpedanceStrategy
from src.model.strategies.strategy_lib.inductance import AnalyticalInductanceStrategy
from src.model.strategies.strategy_lib.lambda_strategy import AnalyticalLambdaStrategy
from src.model.strategies.strategy_lib.mu_app import AnalyticalMu_appStrategy
from src.model.strategies.strategy_lib.resistance import AnalyticalResistanceStrategy, AnalyticalResistanceStrategyv2
from src.model.strategies.strategy_lib.SPICE import SPICE_test, SPICE_op_Amp_gain, SPICE_op_Amp_transcient, \
    SPICE_impedance

STRATEGY_MAP = {
    "resistance": {
        "default": AnalyticalResistanceStrategy,
        "strategies": [AnalyticalResistanceStrategy, AnalyticalResistanceStrategyv2]
    },
    "frequency_vector": {
        "default": FrequencyVectorStrategy,
        "strategies": [FrequencyVectorStrategy]
    },
    "Nz": {
        "default": AnalyticalNzStrategy,
        "strategies": [AnalyticalNzStrategy]
    },
    "mu_app": {
        "default": AnalyticalMu_appStrategy,
        "strategies": [AnalyticalMu_appStrategy]
    },

     "lambda_param": {
          "default": AnalyticalLambdaStrategy,
          "strategies": [AnalyticalLambdaStrategy]
     },

    "inductance": {
        "default": AnalyticalInductanceStrategy,
        "strategies": [AnalyticalInductanceStrategy]
    },
    "capacitance": {
        "default": AnalyticalCapacitanceStrategy,
        "strategies": [AnalyticalCapacitanceStrategy]
    },
    "impedance": {
        "default": AnalyticalImpedanceStrategy,
        "strategies": [AnalyticalImpedanceStrategy]
    },
    "TF_ASIC_Stage_1": {
        "default": TF_ASIC_Stage_1_Strategy_linear,
        "strategies": [TF_ASIC_Stage_1_Strategy_linear]
    },
    "TF_ASIC_Stage_2": {
        "default": TF_ASIC_Stage_2_Strategy_linear,
        "strategies": [TF_ASIC_Stage_2_Strategy_linear]
    },
    "TF_ASIC_linear": {
        "default": TF_ASIC_Strategy_linear,
        "strategies": [TF_ASIC_Strategy_linear]
    },
    "OLTF_Non_filtered": {
        "default": OLTF_Strategy_Non_Filtered,
        "strategies": [OLTF_Strategy_Non_Filtered]
    },
    "OLTF_Filtered": {
        "default": OLTF_Strategy_Filtered,
        "strategies": [OLTF_Strategy_Filtered]
    },
    "CLTF_Non_filtered": {
        "default": CLTF_Strategy_Non_Filtered_legacy,
        "strategies": [CLTF_Strategy_Non_Filtered_legacy]
    },
    "CLTF_Filtered": {
        "default": CLTF_Strategy_Filtered,
        "strategies": [CLTF_Strategy_Filtered]
    },
    "Display_CLTF_OLTF": {
        "default": Display_CLTF_OLTF,
        "strategies": [Display_CLTF_OLTF]
    },
    "PSD_R_cr": {
        "default": PSD_R_cr,
        "strategies": [PSD_R_cr, PSD_R_cr_V2]
    },
    "PSD_R_cr_filtered": {
        "default": PSD_R_cr_filtered,
        "strategies": [PSD_R_cr_filtered,PSD_R_cr_filtered_V2]
    },
    "PSD_R_Coil": {
        "default": PSD_R_Coil,
        "strategies": [PSD_R_Coil, PSD_R_Coil_V2]
    },
    "PSD_R_Coil_filtered": {
        "default": PSD_R_Coil_filtered,
        "strategies": [PSD_R_Coil_filtered, PSD_R_Coil_filtered_V2]
    },
    "PSD_Flicker": {
        "default": PSD_Flicker,
        "strategies": [PSD_Flicker, PSD_Flicker_V2]
    },
    "PSD_e_en": {
        "default": PSD_e_en,
        "strategies": [PSD_e_en, PSD_e_en_V2]
    },
    "PSD_e_en_filtered": {
        "default": PSD_e_en_filtered,
        "strategies": [PSD_e_en_filtered, PSD_e_en_filtered_V2]
    },
    "PSD_e_in": {
        "default": PSD_e_in,
        "strategies": [PSD_e_in, PSD_e_in_V2]
    },
    "PSD_e_in_filtered": {
        "default": PSD_e_in_filtered,
        "strategies": [PSD_e_in_filtered, PSD_e_in_filtered_V2]
    },
    "PSD_Total": {
        "default": PSD_Total,
        "strategies": [PSD_Total]
    },
    "PSD_Total_filtered": {
        "default": PSD_Total_filtered,
        "strategies": [PSD_Total_filtered]
    },
    "Display_all_PSD": {
        "default": Display_all_PSD,
        "strategies": [Display_all_PSD]
    },
    "Display_all_PSD_filtered": {
        "default": Display_all_PSD_filtered,
        "strategies": [Display_all_PSD_filtered]
    },
    "NEMI": {
        "default": NEMI,
        "strategies": [NEMI]
    },
    "NEMI_FIltered": {
        "default": NEMI_FIltered,
        "strategies": [NEMI_FIltered,NEMI_FIlteredv2, NEMI_FIlteredv3]
    },
    # "SPICE_test": {
    #     "default": SPICE_test,
    #     "strategies": [SPICE_test]
    # },
    # "SPICE_op_Amp_gain" : {
    #     "default": SPICE_op_Amp_gain,
    #     "strategies": [SPICE_op_Amp_gain]
    # },
    # "SPICE_op_Amp_transcient": {
    #     "default": SPICE_op_Amp_transcient,
    #     "strategies": [SPICE_op_Amp_transcient]
    # },
    # "SPICE_impedance" : {
    #     "default": SPICE_impedance,
    #     "strategies": [SPICE_impedance]
    # }
}
class CalculationController:
    """
        The CalculationController class is responsible for managing the calculation engine and the input parameters
        of the engine. This controller is the main interface between the user interface and the calculation engine.
        It can be used to run the engine headless or to update the parameters and run the calculations.
    """
    def __init__(self, params_dict=None, backups_count=3):
        """
                Initializes the CalculationController with optional parameters. This controller
                sets up the calculation engine.

                Engine calculation nodes should be added here.

                Parameters:
                - params_dict (dict, optional): A dictionary of parameters to initialize the
                input parameters of the engine.
        """
        self.engine = CalculationEngine(backups_count=backups_count)
        self.is_data_ready = False
        self.params = None

        for node_name, info in STRATEGY_MAP.items():
            default_strategy = info["default"]()
            self.engine.add_or_update_node(node_name, default_strategy)

        if params_dict:
            self.update_parameters(params_dict)

    def delete_spice_nodes(self, spice_nodes : list):
        for node_name in spice_nodes:
            self.engine.delete_node(node_name)
            print(f"Deleted node {node_name}")
    def update_parameters(self, params_dict):
        """
               Updates the input parameters of the calculation engine using the provided dictionary. This method
               also triggers the update of the engine's parameters and marks the output data as ready for plot.

               Parameters:
               - params_dict (dict): A dictionary containing the new parameters to be updated in the engine.

               The dict should respect the following format:

                {
                    "param1": value1,
                    "param2": value2,
                    ...
                }

               Returns:
               - dict: The current results after updating the parameters, if any calculation was previously run.
           """
        self.params = params_dict
        new_parameters = InputParameters(self.params)
        self.engine.update_parameters(new_parameters)

        self.is_data_ready = True
        return self.get_current_results()

    def run_calculation(self):
        """
               Executes the calculations based on the current set of parameters and strategies defined in the engine.
               Marks the data as ready and returns the current results.

               Returns:
               - dict: The results of the calculations performed by the engine.
       """
        self.engine.run_calculations()
        self.is_data_ready = True
        return self.get_current_results()

    def get_current_results(self):
        """
                Retrieves the most recent results from the calculation engine output class if the data is marked as
                ready.

                Returns:
                - dict or None: The current results if available; otherwise,
                None if no calculations have been run or data is not ready.
        """
        if not self.is_data_ready:
            return None
        return self.engine.current_output_data.results

    def get_old_results(self):
        """
               Retrieves the previous set of results from the calculation engine.

               Returns:
               - dict: The results of the previous calculations performed by the engine.
           """
        return self.engine.old_output_data.results

    def save_current_results(self, index):
        """
               Saves the current results to the output data of the calculation engine.

               Parameters:
               - index (int): The index of the current results to be saved.
           """
        self.engine.save_calculation_results(index)

    def clear_calculation_results(self):
        """
               Clears the current results from the calculation engine.
           """
        self.engine.clear_calculation_results()

    def set_node_strategy(self, node_name, strategy_class, params_dict):
        strategy_instance = strategy_class()
        print(strategy_instance)
        self.engine.swap_strategy_for_node(node_name, strategy_instance, params_dict)

    def export_CLTF_NEMI(self, path):
        """
        IF the node is NEMI, and the node CLTF_filtered, plot both in the same graph and save it in the path
        :param path: Full path to save the graph
        :return: SUCCESS or ERROR
        """

        # Retrieve the results of the NEMI node if it exists
        data = self.get_current_results()
        if data is None:
            raise "Error: No data available"

        # Retrieve the results of the CLTF_Filtered node if it exists
        try:
            cltf_data = data.get("CLTF_Filtered", None)
            nemi_data = data.get("NEMI", None)

        except KeyError:
            raise "Error: Missing data for CLTF_Filtered or NEMI"

        try :
            # Plot the data
            import matplotlib.pyplot as plt
            freq_vector = cltf_data["data"][:,0]
            cltf_vector = 20*np.log(cltf_data["data"][:,1])
            nemi_vector = nemi_data["data"][:,1]

            fig, ax1 = plt.subplots()
            color = 'tab:red'
            ax1.set_xlabel('Frequency (Hz)')
            ax1.semilogx()
            ax1.semilogy()

            ax1.set_ylabel('NEMI', color=color)
            ax1.plot(freq_vector, nemi_vector, color=color)
            ax1.tick_params(axis='y', labelcolor=color)

            ax2 = ax1.twinx()
            ax2.semilogx()
            color = 'tab:blue'

            ax2.set_ylabel('CLTF (dB)', color=color)
            ax2.plot(freq_vector, cltf_vector, color=color)
            ax2.tick_params(axis='y', labelcolor=color)

            # add grid
            ax1.grid("both")
            ax2.grid("both")

            path = str(path)

            #if the path does not end with .png
            if not path.endswith(".png"):
                path += ".png"

            print("Saving plot to : " + path)

            plt.savefig(path)


            return "SUCCESS"
        except Exception as e:
            return "ERROR Plotting data : " + str(e)

