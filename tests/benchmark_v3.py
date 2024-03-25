import time

import numpy as np
import timeit

import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from model.strategies.strategy_lib.CLTF import CLTF_Strategy_Non_Filtered, CLTF_Strategy_Filtered, \
    CLTF_Strategy_Non_Filtered_legacy
from model.strategies.strategy_lib.OLTF import OLTF_Strategy_Non_Filtered, OLTF_Strategy_Filtered
from model.strategies.strategy_lib.TF_ASIC import TF_ASIC_Stage_1_Strategy_linear, TF_ASIC_Stage_2_Strategy_linear, \
    TF_ASIC_Strategy_linear
from src.model.input_parameters import InputParameters
from model.engine import CalculationEngine
from model.strategies.strategy_lib.Nz import AnalyticalNzStrategy
from model.strategies.strategy_lib.capacitance import AnalyticalCapacitanceStrategy
from model.strategies.strategy_lib.frequency import FrequencyVectorStrategy
from model.strategies.strategy_lib.impedance import AnalyticalImpedanceStrategy
from model.strategies.strategy_lib.inductance import AnalyticalInductanceStrategy
from model.strategies.strategy_lib.lambda_strategy import AnalyticalLambdaStrategy
from model.strategies.strategy_lib.mu_app import AnalyticalMu_appStrategy
from model.strategies.strategy_lib.resistance import AnalyticalResistanceStrategy



def run_benchmark_with_increasing_nodes(f_start, f_stop, nb_points_per_decade):
    total_benchmarks = len(frequencies_ranges) * len(points_per_decade_list)
    benchmarks_completed = 0

    parameters_dict = {
        'f_start': f_start,
        'f_stop': f_stop,
        'nb_points_per_decade': nb_points_per_decade,
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
        'nb_spire': 12100,
        'ray_spire': 5 * 10 ** -3,
        'rho_whire': 1.6,
        'coeff_expansion': 1,
        'stage_1_cutting_freq': 20000,
        'stage_2_cutting_freq': 20000,
        'gain_1_linear': 1,
        'gain_2_linear': 1,
        'mutual_inductance': 0.1,
        'feedback_resistance': 1000,
    }
    node_strategies = [
        #nodes that returns scalar values
        ('frequency_vector', FrequencyVectorStrategy()),
        ('resistance', AnalyticalResistanceStrategy()),
        ('Nz', AnalyticalNzStrategy()),
        ('mu_app', AnalyticalMu_appStrategy()),
        ('lambda_param', AnalyticalLambdaStrategy()),
        ('inductance', AnalyticalInductanceStrategy()),
        ('capacitance', AnalyticalCapacitanceStrategy()),
        # nodes that return vector values
        ('impedance', AnalyticalImpedanceStrategy()),
        ('TF_ASIC_Stage_1_linear', TF_ASIC_Stage_1_Strategy_linear()),
        ('TF_ASIC_Stage_2_linear', TF_ASIC_Stage_2_Strategy_linear()),
        ('TF_ASIC_linear', TF_ASIC_Strategy_linear()),
        ('OLTF_Non_filtered', OLTF_Strategy_Non_Filtered()),
        ('OLTF_Filtered', OLTF_Strategy_Filtered()),
        ('CLTF_Non_filtered', CLTF_Strategy_Non_Filtered()),
        ('CLTF_Filtered', CLTF_Strategy_Filtered()),
        ('CLTF_Non_Filtered_legacy', CLTF_Strategy_Non_Filtered_legacy())
    ]

    benchmark_results = []

    scalar_nodes = [
        'frequency_vector', 'resistance', 'Nz', 'mu_app',
        'lambda_param', 'inductance', 'capacitance'
    ]
    vector_nodes = [
        'impedance', 'TF_ASIC_Stage_1_linear', 'TF_ASIC_Stage_2_linear',
        'TF_ASIC_linear', 'OLTF_Non_filtered', 'OLTF_Filtered',
        'CLTF_Non_filtered', 'CLTF_Filtered', 'CLTF_Non_Filtered_legacy'
    ]

    for i in range(1, len(node_strategies) + 1):
        current_strategies = node_strategies[:i]

        num_scalar = len([node for node in current_strategies if node[0] in scalar_nodes])
        num_vector = len([node for node in current_strategies if node[0] in vector_nodes])

        # Éviter la division par zéro
        scalar_to_vector_ratio = num_scalar / max(num_vector, 1)

        calculation_engine = CalculationEngine()
        calculation_engine.update_parameters(InputParameters(parameters_dict))

        for strategy_name, strategy in current_strategies:
            calculation_engine.add_or_update_node(strategy_name, strategy)

        start_time = time.time()
        calculation_engine.run_calculations()
        time_taken = time.time() - start_time

        benchmark_results.append({
            'number_of_nodes': i,
            'time_taken': time_taken,
            'scalar_to_vector_ratio': scalar_to_vector_ratio
        })

    benchmarks_completed += 1
    print(f"Completed {benchmarks_completed}/{total_benchmarks} benchmarks")



    return benchmark_results


# Define benchmark parameters
#frequencies_ranges = [(1, 1000), (1, 10000), (10, 100000), (100, 1000000), (1000, 10000000),
                      #                      (10000, 100000000), (100000, 1000000000)]

#points_per_decade = [10, 20, 50, 100, 200, 500, 700, 800, 1000, 1200, 1500, 2000, 2500, 3000,
 #                    5000, 7000, 10000, 100000]

# Calculer les limites de chaque plage sur une échelle logarithmique
log_start = np.log10(1)  # Log de la fréquence de départ (1 Hz)
log_stop = np.log10(1000000)  # Log de la fréquence de fin (1 GHz)

# Générer 10 points log-spaced entre log_start et log_stop
log_points = np.logspace(log_start, log_stop, num=6, base=10)

# Créer les plages de fréquences en utilisant ces points
# Chaque plage commence là où la précédente s'est arrêtée, et se termine au point actuel
frequencies_ranges = [(int(log_points[i]), int(log_points[i+1])) for i in range(len(log_points)-1)]

points_per_decade_list = [20, 80,  320,  1280,  5120]

all_benchmark_results = []

for f_range in frequencies_ranges:
    for nb_points in points_per_decade_list:
        f_start, f_stop = f_range
        benchmark_results = run_benchmark_with_increasing_nodes(f_start, f_stop, nb_points)
        for result in benchmark_results:
            result['f_start'] = f_start
            result['f_stop'] = f_stop
            result['nb_points_per_decade'] = nb_points
        all_benchmark_results.extend(benchmark_results)

# Convertir en DataFrame pour une manipulation facile
df = pd.DataFrame(all_benchmark_results)


# Définir les dimensions de la grille
rows = len(frequencies_ranges)
cols = len(points_per_decade_list)

fig, axs = plt.subplots(rows, cols, figsize=(20, 10), sharex=True, sharey=True)
fig.suptitle('Execution Time vs Number of Nodes for Various Configurations', fontsize=16)

for i, f_range in enumerate(frequencies_ranges):
    for j, nb_points in enumerate(points_per_decade_list):
        ax = axs[i, j] if rows > 1 and cols > 1 else axs[max(i, j)]
        subset = df[(df['f_start'] == f_range[0]) & (df['f_stop'] == f_range[1]) & (df['nb_points_per_decade'] == nb_points)]
        ax.plot(subset['number_of_nodes'], subset['time_taken'], marker='o', linestyle='-', color='blue')
        ax.set_title(f"Freq: {f_range[0]}-{f_range[1]} Hz, Points/Dec: {nb_points}")
        ax.grid(True)

# Ajustements pour une meilleure lisibilité
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.show()

#### HEATMAP

# Supposant que all_benchmark_results est une liste de dictionnaires
# où chaque dictionnaire contient les résultats d'un benchmark
#### df = pd.DataFrame(all_benchmark_results)

# Numéroter chaque configuration
#### d#### f['config_id'] = df.index + 1
#### heatmap_data = df.pivot(index='config_id', columns='number_of_nodes', values='time_taken')

#### heatmap_data_log = np.log(heatmap_data.replace(0, np.nan))  # Remplacer les 0 par NaN pour éviter des erreurs avec le log

#### plt.figure(figsize=(12, 8))
#### sns.heatmap(heatmap_data_log, cmap="viridis")
#### plt.title('Log-Scale Heatmap of Execution Time')
#### plt.ylabel('Configuration ID')
#### plt.xlabel('Number of Nodes')
#### plt.show()
