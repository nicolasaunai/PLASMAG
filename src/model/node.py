from model.strategies import CalculationStrategy


class CalculationNode:
    """
        Represents a node in the calculation graph, capable of performing a calculation
        using a specified strategy and resolving dependencies dynamically.

        There are two types of nodes in the calculation graph:

        - Leaf nodes: These nodes directly use input parameters without further calculation.

        - Internal nodes: These nodes use a calculation strategy to perform a calculation based on dependencies and
        parameters.

        Attributes:
            name (str): Unique identifier for the node.
            engine (CalculationEngine): Reference to the engine that manages the calculation process.
            _strategy (CalculationStrategy, optional): The strategy used for calculation. May be None
                                                       for leaf nodes that use direct parameters.

        Methods:
            resolve_dependencies: Dynamically resolves (= get the value of) the dependencies required by the strategy.
            calculate: Performs the calculation based on the strategy and updates the results.
            set_strategy: Assigns a new calculation strategy to the node.
        """

    def __init__(self, name, engine, strategy: CalculationStrategy = None):
        """
               Initializes a CalculationNode with a name, reference to the calculation engine, and an optional strategy.

               Parameters:
                   name (str): The unique identifier for this node.
                   engine (CalculationEngine): The calculation engine this node is part of.
                   strategy (CalculationStrategy, optional): The strategy to use for calculations. Defaults to None.
       """
        self.name = name
        self.engine = engine
        self._strategy = strategy

    def resolve_dependencies(self) -> dict:
        """
        Dynamically resolves and calculates the dependencies required by this node's strategy.

        This method iterates over the dependencies required by the strategy and get their values. It doesn't
        calculate the value of the dependencies if they have already been calculated and stored in the
        CalculationResults class.


        Returns:
            dict: A dictionary where keys are dependency names and values are their calculated results.
        """
        dependencies = {}  # Store the resolved dependencies here

        # If the node has a strategy (it's not a leaf), resolve its dependencies
        if self._strategy:
            for dep_name in self._strategy.get_dependencies():
                # Get or create the dependency node and calculate its value
                dep_node = self.engine.get_or_create_node(dep_name)
                dependencies[dep_name] = dep_node.calculate()
        return dependencies

    def calculate(self) -> any:
        """
        Calculates the value for this node based on its strategy and resolved dependencies.
        If the node's value has already been calculated and stored, it returns that value
        instead of recalculating.

        Returns:
            The calculated value or the previously stored value if available.
        """

        # Check if the value has already been calculated and stored
        existing_value = self.engine.current_output_data.get_result(self.name)
        if existing_value is not None:
            return existing_value

        # Resolve dependencies required for the calculation
        dependencies = self.resolve_dependencies()

        # Perform the calculation using the strategy, if available; otherwise, use direct parameter
        calculated_value = self._strategy.calculate(dependencies, self.engine.current_parameters) \
            if self._strategy else self.engine.current_parameters.data.get(self.name, None)

        # Store the calculated value in OutputData
        self.engine.current_output_data.set_result(self.name, calculated_value)
        return calculated_value

    def set_strategy(self, strategy):
        """
        Assigns a new calculation strategy to this node and invalidates any previously calculated value,
        forcing a recalculation (to avoid corrupted results) with the new strategy on the next calculate call.

        Parameters:
            strategy (CalculationStrategy): The new strategy to use for calculations.
        """
        self._strategy = strategy

        # Invalidate the previously calculated value for this node to ensure recalculation
        self.engine.current_output_data.set_result(self.name, None)

