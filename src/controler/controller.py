from model import InputParameters
from model.engine import CalculationEngine
from model.strategies.strategy_lib.Nz import AnalyticalNzStrategy
from model.strategies.strategy_lib.capacitance import AnalyticalCapacitanceStrategy
from model.strategies.strategy_lib.frequency import FrequencyVectorStrategy
from model.strategies.strategy_lib.impedance import AnalyticalImpedanceStrategy
from model.strategies.strategy_lib.inductance import AnalyticalInductanceStrategy
from model.strategies.strategy_lib.lambda_strategy import AnalyticalLambdaStrategy
from model.strategies.strategy_lib.mu_app import AnalyticalMu_appStrategy
from model.strategies.strategy_lib.resistance import AnalyticalResistanceStrategy


class CalculationController:
    def __init__(self, params_dict = None):

        self.engine = CalculationEngine()

        self.engine.add_or_update_node('frequency_vector', FrequencyVectorStrategy())
        self.engine.add_or_update_node('resistance', AnalyticalResistanceStrategy())
        self.engine.add_or_update_node('Nz', AnalyticalNzStrategy())
        self.engine.add_or_update_node('mu_app', AnalyticalMu_appStrategy())
        self.engine.add_or_update_node('lambda_param', AnalyticalLambdaStrategy())
        self.engine.add_or_update_node('inductance', AnalyticalInductanceStrategy())
        self.engine.add_or_update_node('capacitance', AnalyticalCapacitanceStrategy())

        self.engine.add_or_update_node('impedance', AnalyticalImpedanceStrategy())

        self.params = None
        if params_dict:
            self.update_parameters(params_dict)

    def update_parameters(self, params_dict):
        self.params = params_dict
        new_parameters = InputParameters(self.params)
        self.engine.update_parameters(new_parameters)
    def run_calculation(self):
        self.engine.run_calculations()
        impedance_results = self.engine.current_output_data.get_result('impedance')
        if impedance_results is not None:
            impedance = impedance_results[:, 1]
            frequencies = impedance_results[:, 0]
            return impedance, frequencies
        return None, None
