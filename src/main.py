from model import InputParameters
from model.engine import CalculationEngine
from model.strategies.strategy_lib.Nz import AnalyticalNzStrategy
from model.strategies.strategy_lib.inductance import AnalyticalInductanceStrategy
from model.strategies.strategy_lib.mu_app import AnalyticalMu_appStrategy
from model.strategies.strategy_lib.resistance import AnalyticalResistanceStrategy
from model.strategies.strategy_lib.lambda_strategy import AnalyticalLambdaStrategy

if __name__ == "__main__":
    # Ensure 'B' is included in the parameters for calculating 'Z'
    # Initialize the calculation engine with a set of parameters, including all necessary inputs for the calculations
    parameters_dict = {
        'mu_insulator' : 1,
        'len_coil' : 155*10**-3,
        'kapthon_thick' : 30*10**-6,
        'insulator_thick' : 10*10**-6,
        'diam_out_mandrel' : 3.2*10**-3,
        'diam_wire' : 90*10**-6,
        'capa_tuning' : 1,
        'capa_triwire' : 150,
        'len_core' : 20*10**-2,
        'diam_core' : 3.2*10**-3,
        'mu_r' : 100000,
        'nb_spire' : 12100,
        'ray_spire' : 5*10**-3,
        'rho_whire' : 1.6,
    }

    parameters = InputParameters(parameters_dict)

    # Initialize the calculation engine with a set of parameters, including all necessary inputs for the calculations
    calculation_engine = CalculationEngine()
    calculation_engine.update_parameters(parameters)

    # Add the calculation strategies to the engine
    calculation_engine.add_or_update_node('resistance', AnalyticalResistanceStrategy())
    calculation_engine.add_or_update_node('Nz', AnalyticalNzStrategy())
    calculation_engine.add_or_update_node('mu_app', AnalyticalMu_appStrategy())
    calculation_engine.add_or_update_node('lambda_param', AnalyticalLambdaStrategy())
    calculation_engine.add_or_update_node('inductance', AnalyticalInductanceStrategy())



    # Run the calculations
    calculation_engine.run_calculations()

    # Print the results
    print(calculation_engine.current_output_data.results)


