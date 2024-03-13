import unittest
from model import InputParameters
from model.engine import CalculationEngine
from model.strategies.test_strategy.resistance_strategy import ResistanceCalculationStrategy, \
    OtherResistanceCalculationStrategy
from model.strategies.test_strategy.random_strategy_tests import ZCalculationStrategy, CyclicResistanceStrategy, \
    ZCalculationStrategy2, CCalculationStrategy

class TestCalculationEngine(unittest.TestCase):
    def test_calculations(self):
        parameters_dict = InputParameters({'N': 12000, 'Rs': 4, 'rho': 1.6, 'A': 10, 'B': 10})
        calculation_engine = CalculationEngine()
        calculation_engine.update_parameters(parameters_dict)
        calculation_engine.add_or_update_node('R', ResistanceCalculationStrategy())
        calculation_engine.add_or_update_node('Z', ZCalculationStrategy())
        calculation_engine.run_calculations()
        self.assertIsNotNone(calculation_engine.current_output_data.results)

        calculation_engine.add_or_update_node('R', OtherResistanceCalculationStrategy())
        calculation_engine.run_calculations()
        self.assertIsNotNone(calculation_engine.current_output_data.results)

        calculation_engine.update_parameters(InputParameters({'N': 12000, 'Rs': 2, 'rho': 1.6, 'A': 10, 'B': 5}))
        calculation_engine.run_calculations()
        self.assertIsNotNone(calculation_engine.current_output_data.results)

        calculation_engine.add_or_update_node('C', CCalculationStrategy())
        calculation_engine.add_or_update_node('Z', ZCalculationStrategy2())
        calculation_engine.run_calculations()
        self.assertIsNotNone(calculation_engine.current_output_data.results)

    def test_dependency_tree(self):
        parameters_dict = InputParameters({'N': 12000, 'Rs': 4, 'rho': 1.6, 'A': 10, 'B': 10})
        calculation_engine = CalculationEngine()
        calculation_engine.update_parameters(parameters_dict)
        calculation_engine.add_or_update_node('R', ResistanceCalculationStrategy())
        calculation_engine.add_or_update_node('Z', ZCalculationStrategy())
        calculation_engine.run_calculations()
        dict_tree = calculation_engine.build_dependency_tree()
        self.assertIsNotNone(dict_tree)

    def test_save_dependency_tree(self):
        parameters_dict = InputParameters({'N': 12000, 'Rs': 4, 'rho': 1.6, 'A': 10, 'B': 10})
        calculation_engine = CalculationEngine()
        calculation_engine.update_parameters(parameters_dict)
        calculation_engine.add_or_update_node('R', ResistanceCalculationStrategy())
        calculation_engine.add_or_update_node('Z', ZCalculationStrategy())
        calculation_engine.run_calculations()
        self.assertRaises(TypeError, calculation_engine.build_dependency_tree, '/home/ronceray/Documents/PLASMAG/PLASMAG/Dep_tree.json')

    def test_engine_with_cyclic_strategy(self):
        parameters_dict = InputParameters({'N': 12000, 'Rs': 4, 'rho': 1.6, 'A': 10, 'B': 5})
        calculation_engine = CalculationEngine()
        calculation_engine.update_parameters(parameters_dict)
        calculation_engine.add_or_update_node('R', ResistanceCalculationStrategy())
        calculation_engine.add_or_update_node('Z', ZCalculationStrategy())
        self.assertRaises(Exception, calculation_engine.run_calculations)

        calculation_engine.add_or_update_node('R', CyclicResistanceStrategy())
        calculation_engine.run_calculations()
        self.assertIsNotNone(calculation_engine.current_output_data.results)

if __name__ == '__main__':
    unittest.main()
