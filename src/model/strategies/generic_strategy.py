"""
src/model/strategies/generic_strategy.py
PLASMAG 2024 Software, LPP
"""
from abc import ABC, abstractmethod


class CalculationStrategy(ABC):
    """
    Abstract base class for defining calculation strategies within the calculation engine.

    A calculation strategy encapsulates a specific method of computation that
    can be applied to a set of input parameters and dependencies. Implementations
    of this class are expected to provide the logic for performing a calculation
    and specifying its dependencies.

    This class is designed to be subclassed with concrete strategies implementing
    the actual calculation logic tailored to specific computational needs.

    Methods:
        calculate: Performs the calculation based on given dependencies and parameters.
        get_dependencies: Returns a list of names of other calculations this strategy depends on.

    Example:
        Subclass this `CalculationStrategy` to implement a custom calculation method.
        >> class MyCalculationStrategy(CalculationStrategy):
        >>     @staticmethod
        >>    def get_dependencies():
        >>         return ['dependency1', 'dependency2']
        >>
        >>     def calculate(self, dependencies, parameters):
        >>         # Custom calculation logic here
        >>         result = dependencies['dependency1'] * parameters.data['param1']
        >>         return result

    Note:
        - `calculate` method must be overridden in subclasses to provide specific calculation logic.
        - `get_dependencies` method should return a list of the names of all other calculations
          that the current strategy's calculation depends on.
          This is used by the calculation
          engine to ensure all dependencies are calculated before attempting to calculate this one.
          The list of dependencies should match the keys used to store the results in the `CalculationResults`.
          The full list of dependencies should be provided even if some of them are not used in the calculation.
          To know all existing dependencies, they are all listed in the CalculationResults readme file.
    """

    @abstractmethod
    def calculate(self, dependencies: dict, parameters):
        """
        Abstract method to perform the calculation using provided dependencies and parameters.

        Parameters:
            dependencies (dict): A dictionary where keys are the names of the dependencies
                                  (as defined by get_dependencies) and values are the results
                                  of those dependencies' calculations.
            parameters (InputParameters): A reference to the input parameters object/class containing the data

        Returns:
            The result of the calculation. The type and shape of the result depends on the specific
            calculation being performed.
        """
        return NotImplemented

    @staticmethod
    def get_dependencies() -> list[str]:
        """
        Returns a list of names of other calculations that this strategy depends on.

        This method should be overridden in subclasses to specify the exact dependencies
        required for the calculation strategy.

        Returns:
            list[str]: A list of dependency names.
        """
        return []
