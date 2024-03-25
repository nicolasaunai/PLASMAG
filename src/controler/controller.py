from src.model.strategies.strategy_lib.CLTF import CLTF_Strategy_Non_Filtered, CLTF_Strategy_Filtered, \
    CLTF_Strategy_Non_Filtered_legacy
from src.model.strategies.strategy_lib.OLTF import OLTF_Strategy_Non_Filtered, OLTF_Strategy_Filtered
from src.model.strategies.strategy_lib.TF_ASIC import TF_ASIC_Stage_1_Strategy_linear, TF_ASIC_Stage_2_Strategy_linear, TF_ASIC_Strategy_linear
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
    def __init__(self, params_dict=None):

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

        self.engine.add_or_update_node('CLTF_Non_filtered', CLTF_Strategy_Non_Filtered())
        self.engine.add_or_update_node('CLTF_Filtered', CLTF_Strategy_Filtered())


        self.engine.add_or_update_node('CLTF_Non_Filtered_legacy', CLTF_Strategy_Non_Filtered_legacy())


        self.params = None
        if params_dict:
            self.update_parameters(params_dict)

        self.is_data_ready = False

    def update_parameters(self, params_dict):
        self.params = params_dict
        new_parameters = InputParameters(self.params)
        self.engine.update_parameters(new_parameters)

    def run_calculation(self):
        self.engine.run_calculations()
        self.is_data_ready = True
        return self.get_current_results()

    def get_current_results(self):

        if not self.is_data_ready:
            return None
        else:
            return self.engine.current_output_data.results

    def get_old_results(self):
        return self.engine.old_output_data.results
