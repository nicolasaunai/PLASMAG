import json

import numpy as np

from controler.controller import CalculationController
from scipy.optimize import minimize

def determine_resonance_freq(freq_vector, impedance_vector):
    """
    Function to determine the resonance frequency of the impedance curve
    :param freq_vector: frequency vector
    :param impedance_vector: impedance vector
    :return: resonance frequency
    """
    # Find the index of the minimum impedance value
    max = impedance_vector.argmax()
    # Return the frequency at the index of the minimum impedance value
    return freq_vector[max]

def objective_function(x):
    params = parameters_dict.copy()
    params['len_coil'] = x[0]
    params['diam_wire'] = x[1]
    params['nb_spire'] = int(x[2])

    controller.update_parameters(params)
    results = controller.get_current_results()
    impedance = results['impedance']["data"]
    current_resonance_freq = determine_resonance_freq(impedance[:,0], impedance[:,1])

    target_resonance_freq = 1993
    return (current_resonance_freq - target_resonance_freq)**2

if __name__ == "__main__":
    # Ensure 'B' is included in the parameters for calculating 'Z'
    # Initialize the calculation engine with a set of parameters, including all necessary inputs for the calculations
    parameters_dict = {
        'f_start': 1,
        'f_stop': 1000000,
        'nb_points_per_decade': 100,
        # Add other parameters required by the strategies
        'mu_insulator': 1,
        'len_coil': 155 * 10 ** -3,
        'kapthon_thick': 30 * 10 ** -6,
        'insulator_thick': 10 * 10 ** -6,
        'diam_out_mandrel': 3.2 * 10 ** -3,
        'diam_wire': 90 * 10 ** -6,
        'capa_tuning': 1 * 10 ** -12,
        'capa_triwire': 150 * 10 ** -12,
        'len_core': 20 * 10 ** -2,
        'diam_core': 3.2 * 10 ** -3,
        'mu_r': 100000,
        'nb_spire': 10000,
        'ray_spire': 5 * 10 ** -3,
        'rho_whire': 1.6,
        'coeff_expansion': 1,
        'stage_1_cutting_freq': 20000,
        'stage_2_cutting_freq': 20000,
        'gain_1_linear': 1,
        'gain_2_linear': 1,
        'mutual_inductance': 0.1,
        'feedback_resistance': 1000,
        'temperature': 300,
        "spice_resistance_test": 1000,
        "Para_A": 1,
        "Para_B": 1,
        "e_en": 1,
        "e_in": 1,
        "Alpha": 1,
    }

    print(parameters_dict)

    controller = CalculationController()

    controller.update_parameters(parameters_dict)

    results = controller.get_current_results()
    impedance = results['impedance']["data"]

    resonnance_freq = determine_resonance_freq(impedance[:,0], impedance[:,1])


    # print(results)
    # # plot impedance vs frequency
    # import matplotlib.pyplot as plt
    #
    # #two subplots stacked vertically
    # fig, axs = plt.subplots(1, 1, figsize=(10, 10))
    # fig.suptitle('TF ASIC')
    # axs.plot(impedance[:,0], impedance[:,1], label='Impedance')
    #
    # #plot vertical line freq resonnance
    # axs.axvline(x=resonnance_freq, color='r', linestyle='--', label='Resonance frequency')
    #
    #
    # axs.set_xscale('log')
    # axs.set_yscale('log')
    # axs.grid("both")
    # axs.set_title('Linear scale')
    # axs.set_xlabel('Frequency [Hz]')
    # axs.set_ylabel('Gain linear')
    # axs.legend()
    #
    # plt.show()
    #
    # print("Resonance frequency: ", resonnance_freq)

    initial_guess = [
        parameters_dict['len_coil'],  # Initial length of coil
        parameters_dict['diam_wire'],  # Initial diameter of wire
        parameters_dict['nb_spire'],  # Initial number of spires
        parameters_dict['rho_whire'],
        parameters_dict['diam_core'],
        parameters_dict['len_core'],
        parameters_dict['mu_r'],
        parameters_dict['capa_tuning'],
        parameters_dict['capa_triwire'],
    ]

    # Bounds for each parameter
    bounds = [
        (1e-3, 200e-3),  # Bounds for len_coil
        (10e-6, 300e-6),  # Bounds for diam_wire
        (1000, 20000),  # Bounds for nb_spire
        (1,10), # Bounds for rho_whire
        (1e-3, 100e-3), # Bounds for diam_core
        (1e-2, 200e-2), # Bounds for len_core
        (1, 1000000), # Bounds for mu_r
        (1e-12, 1000e-12), # Bounds for capa_tuning
        (10e-12, 1000e-12), # Bounds for capa_triwire


    ]

    # Perform the optimization
    result = minimize(objective_function, initial_guess, bounds=bounds, method='Nelder-Mead')
    optimized_params = result.x

    print("Optimized length of coil: ", optimized_params[0])
    print("Optimized diameter of wire: ", optimized_params[1])
    print("Optimized number of spires: ", int(optimized_params[2]))
    print("Optimized resistance: ", optimized_params[3])
    print("Optimized diameter of core: ", optimized_params[4])
    print("Optimized length of core: ", optimized_params[5])
    print("Optimized mu_r: ", optimized_params[6])
    print("Optimized capa_tuning: ", optimized_params[7])
    print("Optimized capa_triwire: ", optimized_params[8])


    # Update the parameters with the optimized values to check the final resonance frequency
    parameters_dict['len_coil'] = optimized_params[0]
    parameters_dict['diam_wire'] = optimized_params[1]
    parameters_dict['nb_spire'] = int(optimized_params[2])
    controller.update_parameters(parameters_dict)
    results = controller.get_current_results()
    impedance = results['impedance']["data"]
    final_resonance_freq = determine_resonance_freq(impedance[:, 0], impedance[:, 1])
    print("Final resonance frequency: ", final_resonance_freq)








