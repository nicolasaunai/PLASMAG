from src.model.strategies.strategy_lib.TF_ASIC import TF_ASIC_Stage_1_Strategy_linear, TF_ASIC_Stage_2_Strategy_linear, TF_ASIC_Strategy_linear
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

        'gain_1' : 0, # Gain of the first stage in  linear
        'stage_1_cutting_freq' : 100, # Cutting frequency of the first stage in Hz

        'gain_1_linear' : 1, # Gain of the first stage in dB
        'gain_2_linear' : 1.259, # Gain of the second stage in dB

        'gain_2' : 2, # Gain of the second stage in dB
        'stage_2_cutting_freq' : 20000, # Cutting frequency of the second stage in Hz

        'f_start' : 1,
        'f_stop' : 100000,
        'nb_points_per_decade' : 100,
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

    calculation_engine.add_or_update_node('TF_ASIC_Stage_1_linear', TF_ASIC_Stage_1_Strategy_linear())
    calculation_engine.add_or_update_node('TF_ASIC_Stage_2_linear', TF_ASIC_Stage_2_Strategy_linear())

    calculation_engine.add_or_update_node('TF_ASIC_linear', TF_ASIC_Strategy_linear())


    # Run the calculations
    calculation_engine.run_calculations()

    # Print the results
    print(calculation_engine.current_output_data.results)

    # plot impedance vs frequency
    import matplotlib.pyplot as plt
    ASIC_Stage_1_TF_linear = calculation_engine.current_output_data.results['TF_ASIC_Stage_1_linear']
    ASIC_Stage_2_TF_linear = calculation_engine.current_output_data.results['TF_ASIC_Stage_2_linear']
    ASIC_TF_linear = calculation_engine.current_output_data.results['TF_ASIC_linear']

    #two subplots stacked vertically
    fig, axs = plt.subplots(2, 1, figsize=(10, 10))
    fig.suptitle('TF ASIC')
    axs[0].plot(ASIC_Stage_1_TF_linear[:,0], ASIC_Stage_1_TF_linear[:,1], label='Stage 1')
    axs[0].plot(ASIC_Stage_2_TF_linear[:,0], ASIC_Stage_2_TF_linear[:,1], label='Stage 2')
    axs[0].plot(ASIC_TF_linear[:,0], ASIC_TF_linear[:,1], label='ASIC')


    axs[0].set_xscale('log')
    axs[0].set_yscale('log')
    axs[0].grid("both")
    axs[0].set_title('Linear scale')
    axs[0].set_xlabel('Frequency [Hz]')
    axs[0].set_ylabel('Gain linear')
    axs[0].legend()



    plt.show()








