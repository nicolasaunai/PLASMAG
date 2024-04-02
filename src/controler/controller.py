"""
 src/controller/controller.py
 PLASMAG 2024 Software, LPP
"""

from src.model.strategies.strategy_lib.Noise import PSD_R_cr, PSD_R_cr_filtered, PSD_R_Coil, PSD_R_Coil_filtered, \
    PSD_Flicker, PSD_e_en, PSD_e_en_filtered, PSD_e_in, PSD_e_in_filtered, PSD_Total, PSD_Total_filtered, \
    Display_all_PSD, NEMI
from src.model.strategies.strategy_lib.CLTF import CLTF_Strategy_Filtered, \
    CLTF_Strategy_Non_Filtered_legacy
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
from src.model.strategies.strategy_lib.resistance import AnalyticalResistanceStrategy


class CalculationController:
    """
        The CalculationController class is responsible for managing the calculation engine and the input parameters
        of the engine. This controller is the main interface between the user interface and the calculation engine.
        It can be used to run the engine headless or to update the parameters and run the calculations.
    """
    def __init__(self, params_dict=None):
        """
                Initializes the CalculationController with optional parameters. This controller
                sets up the calculation engine.

                Engine calculation nodes should be added here.

                Parameters:
                - params_dict (dict, optional): A dictionary of parameters to initialize the
                input parameters of the engine.
        """
        self.engine = CalculationEngine()

        self.engine.add_or_update_node('frequency_vector', FrequencyVectorStrategy())
        self.engine.add_or_update_node('resistance', AnalyticalResistanceStrategy())
        self.engine.add_or_update_node('Nz', AnalyticalNzStrategy())
        self.engine.add_or_update_node('mu_app', AnalyticalMu_appStrategy())
        self.engine.add_or_update_node('lambda_param', AnalyticalLambdaStrategy())
        self.engine.add_or_update_node('inductance', AnalyticalInductanceStrategy())
        self.engine.add_or_update_node('capacitance', AnalyticalCapacitanceStrategy())

        self.engine.add_or_update_node('impedance', AnalyticalImpedanceStrategy())

        self.engine.add_or_update_node('TF_ASIC_Stage_1_linear', TF_ASIC_Stage_1_Strategy_linear())
        self.engine.add_or_update_node('TF_ASIC_Stage_2_linear', TF_ASIC_Stage_2_Strategy_linear())

        self.engine.add_or_update_node('TF_ASIC_linear', TF_ASIC_Strategy_linear())

        self.engine.add_or_update_node('OLTF_Non_filtered', OLTF_Strategy_Non_Filtered())
        self.engine.add_or_update_node('OLTF_Filtered', OLTF_Strategy_Filtered())

        self.engine.add_or_update_node('CLTF_Non_filtered', CLTF_Strategy_Non_Filtered_legacy())
        self.engine.add_or_update_node('CLTF_Filtered', CLTF_Strategy_Filtered())

        self.engine.add_or_update_node('PSD_R_cr', PSD_R_cr())
        self.engine.add_or_update_node('PSD_R_cr_filtered', PSD_R_cr_filtered())

        self.engine.add_or_update_node('PSD_R_Coil', PSD_R_Coil())
        self.engine.add_or_update_node('PSD_R_Coil_filtered', PSD_R_Coil_filtered())

        self.engine.add_or_update_node('PSD_Flicker', PSD_Flicker())

        self.engine.add_or_update_node('PSD_e_en', PSD_e_en())
        self.engine.add_or_update_node('PSD_e_en_filtered', PSD_e_en_filtered())

        self.engine.add_or_update_node('PSD_e_in', PSD_e_in())
        self.engine.add_or_update_node('PSD_e_in_filtered', PSD_e_in_filtered())

        self.engine.add_or_update_node('PSD_ASIC', PSD_ASIC())


        self.engine.add_or_update_node('PSD_Total', PSD_Total())
        self.engine.add_or_update_node('PSD_Total_filtered', PSD_Total_filtered())

        self.engine.add_or_update_node('Display_all_PSD', Display_all_PSD())

        self.engine.add_or_update_node('NEMI', NEMI())

        self.params = None
        if params_dict:
            self.update_parameters(params_dict)

        self.is_data_ready = False

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
