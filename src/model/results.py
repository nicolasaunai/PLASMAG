"""
 src/engine/results.py
 PLASMAG 2024 Software, LPP
"""
class CalculationResults:
    """
    This class acts as a centralized repository for storing the outcomes of various
    calculations. It allows for the retrieval and updating of calculation results,
    facilitating the communication of outcomes between different parts of the calculation
    process.

    Attributes:
        results (dict): A dictionary to store the results of calculations. The keys
                        are the names (str) of the calculation results, and the values
                        are the outcomes of those calculations.

    Methods:
        set_result: Stores or updates a calculation result in the repository.
        get_result: Retrieves a calculation result by its name.

    Note:
        If a result for the given key does not exist, `get_result` returns None.
        This behavior allows checking the existence of results without raising exceptions.
    """

    def __init__(self):
        self.results = {}

    def set_result(self, key: str, value: any):
        """
        Stores or updates the result of a calculation.

        Parameters:
            key (str): The name of the calculation result to store or update.
            value: The outcome of the calculation to be stored.
        """
        self.results[key] = value

    def get_result(self, key: str) -> any:
        """
        Retrieves the result of a calculation by its name.

        Parameters:
            key (str): The name of the calculation result to retrieve.

        Returns:
            The outcome of the calculation associated with the given key, or None if
            no result is found for the specified key.
        """
        return self.results.get(key, None)
