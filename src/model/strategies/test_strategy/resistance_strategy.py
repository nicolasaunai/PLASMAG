import numpy as np
from model import InputParameters
from model.strategies import CalculationStrategy


class ResistanceCalculationStrategy(CalculationStrategy):
    """
       Calculates the electrical strategy_lib based on the number of turns (N),
       surface strategy_lib (Rs), and material density (rho).
       """

    def calculate(self, dependencies: dict, parameters: InputParameters):
        N = parameters.data['N']
        Rs = parameters.data['Rs']
        rho = parameters.data['rho']
        return N * (2 * np.pi * Rs) * 10 ** -3 * rho

    @staticmethod
    def get_dependencies():
        return ['N', 'Rs', 'rho']


class OtherResistanceCalculationStrategy(CalculationStrategy):
    """
        A variant of the strategy_lib calculation that applies an additional
        factor to the result, effectively halving it. This demonstrates how
        different strategies might implement alternative calculations.
        """

    def calculate(self, dependencies, parameters: InputParameters):
        N = parameters.data['N']
        Rs = parameters.data['Rs']
        rho = parameters.data['rho']
        return (N * (2 * np.pi * Rs) * 10 ** -3 * rho) / 10

    @staticmethod
    def get_dependencies():
        return ['N', 'Rs', 'rho']


class AnotherResistanceCalculationStrategy(CalculationStrategy):
    """
        Extends the strategy_lib calculation by incorporating an additional
        parameter 'A'. This strategy showcases how to handle calculations
        with additional input parameters.
        """

    def calculate(self, dependencies: dict, parameters: InputParameters):
        N = parameters.data['N']
        Rs = parameters.data['Rs']
        rho = parameters.data['rho']
        A = parameters.data['A']
        return ((N * (2 * np.pi * Rs) * 10 ** -3 * rho) / 2) + A

    @staticmethod
    def get_dependencies():
        return ['N', 'Rs', 'rho', 'A']
