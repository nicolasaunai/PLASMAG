from src.model.input_parameters import InputParameters
from model.engine import CalculationEngine
from model.strategies.strategy_lib.Nz import AnalyticalNzStrategy
from model.strategies.strategy_lib.capacitance import AnalyticalCapacitanceStrategy
from model.strategies.strategy_lib.frequency import FrequencyVectorStrategy
from model.strategies.strategy_lib.impedance import AnalyticalImpedanceStrategy
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
        'capa_tuning' : 1*10**-12,
        'capa_triwire' : 150*10**-12,
        'len_core' : 20*10**-2,
        'diam_core' : 3.2*10**-3,
        'mu_r' : 100000,
        'nb_spire' : 12100,
        'ray_spire' : 5*10**-3,
        'rho_whire' : 1.6,
        'coeff_expansion' : 1,

        'f_start' : 1,
        'f_stop' : 100000,
        'nb_points_per_decade' : 2,
    }

    print(parameters_dict)

    parameters = InputParameters(parameters_dict)

    # Initialize the calculation engine with a set of parameters, including all necessary inputs for the calculations
    calculation_engine = CalculationEngine()
    calculation_engine.update_parameters(parameters)

    # Add the calculation strategies to the engine

    calculation_engine.add_or_update_node('frequency_vector', FrequencyVectorStrategy())
    calculation_engine.add_or_update_node('resistance', AnalyticalResistanceStrategy())
    calculation_engine.add_or_update_node('Nz', AnalyticalNzStrategy())
    calculation_engine.add_or_update_node('mu_app', AnalyticalMu_appStrategy())
    calculation_engine.add_or_update_node('lambda_param', AnalyticalLambdaStrategy())
    calculation_engine.add_or_update_node('inductance', AnalyticalInductanceStrategy())
    calculation_engine.add_or_update_node('capacitance', AnalyticalCapacitanceStrategy())

    calculation_engine.add_or_update_node('impedance', AnalyticalImpedanceStrategy())

    # Run the calculations
    calculation_engine.run_calculations()

    # Print the results
    print(calculation_engine.current_output_data.results)

    # plot impedance vs frequency
    import matplotlib.pyplot as plt
    impedance_freq_tensor = calculation_engine.current_output_data.results['impedance']

    plt.plot(impedance_freq_tensor[:,0], impedance_freq_tensor[:,1])
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Impedance (Ohm)')
    #show detailed grid
    plt.grid(which='both')
    plt.show()





