from model import InputParameters
from model.strategies import CalculationStrategy


class ZCalculationStrategy(CalculationStrategy):
    """
        Calculates a value 'Z' based on the result of the resistance calculation 'R'
        and a direct parameter 'B'. This strategy exemplifies how to use results from
        other calculations along with direct parameters.
        """

    def calculate(self, dependencies: dict, parameters: InputParameters):
        R = dependencies['R']
        B = parameters.data['B']
        return R * B

    @staticmethod
    def get_dependencies():
        return ['R', "B"]


class ZCalculationStrategy2(CalculationStrategy):
    """
        Calculates a value 'Z' based on the result of the resistance calculation 'R'
        and a calculated parameter 'C'

        """

    def calculate(self, dependencies: dict, parameters: InputParameters):
        R = dependencies['R']
        C = dependencies['C']
        return R * C

    @staticmethod
    def get_dependencies():
        return ['R', 'C']


class CCalculationStrategy(CalculationStrategy):
    """
        Calculates a value 'C' based on the result of the resistance calculation 'R'
        and a direct parameter 'B'. This strategy exemplifies how to use results from
        other calculations along with direct parameters.
        """

    def calculate(self, dependencies: dict, parameters: InputParameters):
        R = dependencies['R']
        B = parameters.data['B']
        return R * B

    @staticmethod
    def get_dependencies():
        return ['R']


class CyclicResistanceStrategy(CalculationStrategy):
    def calculate(self, dependencies, parameters):
        # This strategy is not used in the example, but it introduces a cyclic dependency
        return 0

    @staticmethod
    def get_dependencies():
        return ['Z']  # Introduces a cyclic dependency with Z
