"""
 src/engine/input_parameters.py
 PLASMAG 2024 Software, LPP
"""


class InputParameters:
    """
    This class serves as a container for all the parameters needed by
    the calculation engine. It provides a structured way to access
    input data for various calculations.

    Attributes:
        data (dict): A dictionary containing key-value pairs of parameters.
                     Keys are parameter names (str) and values are their
                     corresponding values. These parameters are used throughout
                     the calculation process to provide necessary input values
                     for different calculation strategies and nodes.

    Note:
        The `data` dictionary should contain all the necessary parameters
        required by the calculation strategies employed in the calculation
        engine. Missing parameters may result in calculation errors or
        incomplete results.
    """

    def __init__(self, data: dict):
        """
        Initializes the InputParameters object with the provided data.
        :param data:
        """
        self.data = data
