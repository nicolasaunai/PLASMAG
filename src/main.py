from model import InputParameters
from model.engine import CalculationEngine
from model.strategies.resistance.resistance_strategy import ResistanceCalculationStrategy, \
    OtherResistanceCalculationStrategy
from model.strategies.test_strategy.random_strategy_tests import ZCalculationStrategy, CyclicResistanceStrategy, \
    ZCalculationStrategy2, CCalculationStrategy

if __name__ == "__main__":
    # Ensure 'B' is included in the parameters for calculating 'Z'
    # Initialize the calculation engine with a set of parameters, including all necessary inputs for the calculations
    parameters_dict = InputParameters({'N': 12000, 'Rs': 4, 'rho': 1.6, 'A': 10, 'B': 10})

    calculation_engine = CalculationEngine()
    calculation_engine.update_parameters(parameters_dict)

    # Adding nodes 'R' and 'Z' to the engine with their respective calculation strategies
    # 'R' calculates resistance based on input parameters
    # 'Z' calculates a value based on the result of 'R' and the direct parameter 'B'
    calculation_engine.add_or_update_node('R', ResistanceCalculationStrategy())
    calculation_engine.add_or_update_node('Z', ZCalculationStrategy())

    # Perform the calculations across all nodes
    calculation_engine.run_calculations()
    print(calculation_engine.current_output_data.results)

    print("Adding a new node 'R' with a different strategy")

    # Change the strategy for calculating 'R' to a different one and recalculate This demonstrates the engine's
    # flexibility in updating strategies for calculations and dynamically adjusting the results
    calculation_engine.add_or_update_node('R', OtherResistanceCalculationStrategy())
    calculation_engine.run_calculations()
    print(calculation_engine.current_output_data.results)

    # Update the parameters for the calculations and rerun them
    # Shows how the engine can adapt to new input parameters without needing to reconfigure the entire calculation setup
    calculation_engine.update_parameters(InputParameters({'N': 12000, 'Rs': 2, 'rho': 1.6, 'A': 10, 'B': 5}))
    calculation_engine.run_calculations()
    print(calculation_engine.current_output_data.results)

    # Adding new nodes 'C' and changing the strategy for calculating 'Z' to use the result of 'C'
    # Illustrates the engine's capability to expand with additional calculations and dependencies dynamically
    # Assume `CCalculationStrategy` and `ZCalculationStrategy2` are defined elsewhere
    calculation_engine.add_or_update_node('C', CCalculationStrategy())
    calculation_engine.add_or_update_node('Z', ZCalculationStrategy2())
    calculation_engine.run_calculations()
    print(calculation_engine.current_output_data.results)

    # Display the graph of calculation nodes
    dict_tree = calculation_engine.build_dependency_tree()

    # print and indent the dictionary
    # print(json.dumps(dict_tree, indent=4))

    # Try to save to a file MUST BE A FULL PATH
    calculation_engine.build_dependency_tree('/home/ronceray/Documents/PLASMAG/PLASMAG/Dep_tree.json')

    parameters_2 = InputParameters({'N': 12000, 'Rs': 4, 'rho': 1.6, 'A': 10, 'B': 5})
    engine2 = CalculationEngine()
    engine2.update_parameters(parameters_2)

    engine2.add_or_update_node('R', ResistanceCalculationStrategy())
    engine2.add_or_update_node('Z', ZCalculationStrategy())

    try:
        engine2.run_calculations()
        print("Pas de cycles détectés. Résultats:", engine2.current_output_data.results)
    except Exception as e:
        print(f"Erreur: {e}")

    try:
        engine2.add_or_update_node('R', CyclicResistanceStrategy())
        engine2.run_calculations()
        print("Calculs exécutés avec succès.")
    except Exception as e:
        print(f"Erreur: {e}")
