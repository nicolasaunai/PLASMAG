import json

from model import CalculationResults, InputParameters, CalculationNode


class CalculationEngine:
    """
    Orchestrates the calculation process across multiple nodes within a calculation graph.

    Manages the lifecycle of calculation nodes, their strategies, and the input/output data flow.
    It allows for dynamic updates to calculation strategies and input parameters, facilitating
    flexible and adaptable calculation processes.

    Attributes:
        current_parameters (InputParameters): The current set of parameters for calculations.
        old_parameters (InputParameters, optional): The previous set of parameters, stored for reference.
        nodes (dict): A dictionary of calculation nodes, keyed by their unique names.
        old_output_data (CalculationResults, optional): The previous set of calculation results.
        current_output_data (CalculationResults): The current set of calculation results being populated.

    Methods:
        get_or_create_node: Retrieves an existing calculation node or creates a new one if not present.
        add_or_update_node: Adds a new calculation node or updates an existing node's strategy.
        update_parameters: Updates the calculation parameters and archives the current results.
        run_calculations: Executes the calculations across all nodes in the graph.
    """

    def __init__(self):
        """
        Initializes the calculation engine.
        """
        self.current_parameters = None
        self.old_parameters = None
        self.nodes = {}
        self.old_output_data = None
        self.current_output_data = CalculationResults()

    def get_or_create_node(self, node_name: str) -> CalculationNode:
        """
        Retrieves an existing node by its name or creates a new one if it doesn't exist.

        Parameters:
            node_name (str): The name of the node to retrieve or create.

        Returns:
            CalculationNode: The retrieved or newly created calculation node.
        """
        if node_name not in self.nodes:
            self.nodes[node_name] = CalculationNode(node_name, self)
        return self.nodes[node_name]

    def build_dependency_tree(self, path=None):
        """
        Builds a nested dictionary representing the dependency tree of the calculation graph.
        Each key in the dictionary is a node name, and its value is a dictionary of its dependencies.
        Optionally saves the tree to a JSON file if a path is specified.

        Parameters:
            path (str, optional): The file path where to save the dependency tree in JSON format.
                                  If not specified, the tree is not saved to a file.
                                  MUST BE A FULL PATH

        Returns:
            dict: A nested dictionary representing the dependency tree of the entire calculation graph.
        """

        # Helper function to recursively build the dependency tree
        def build_tree(node_name):
            node = self.nodes.get(node_name)
            if not node or not node._strategy:
                # If the node does not exist or has no strategy (and thus no dependencies), return an empty dict
                return {}

            dependencies = {}
            for dep_name in node._strategy.get_dependencies():
                # Recursively build the tree for each dependency
                dependencies[dep_name] = build_tree(dep_name)
            return dependencies

        # Corrected approach to identify head nodes
        all_dependencies = set()
        for node in self.nodes.values():
            if node._strategy:
                all_dependencies.update(node._strategy.get_dependencies())

        head_nodes = [node_name for node_name in self.nodes if node_name not in all_dependencies]

        # Build the dependency tree starting from each head node
        dependency_tree = {}
        for head_node in head_nodes:
            dependency_tree[head_node] = build_tree(head_node)

        # Save the tree to a file in JSON format if a path is specified
        if path:
            with open(path, 'w') as json_file:
                json.dump(dependency_tree, json_file, indent=4)

        return dependency_tree

    def check_for_cycles(self):
        """
        Performs a cycle detection in the graph of calculation nodes to prevent infinite recursion or deadlock
        This method implements a depth-first search (DFS) algorithm
        to traverse the graph and detect cycles.

        A cycle in the graph is detected if a node is encountered that is already in the current path (stack)
        from the root of the DFS. If such a cycle is detected, an exception is raised to indicate the error.

        Raises:
            Exception: If a cyclic dependency is detected among the calculation nodes.

       How it works:
            1. Utilizes `visited` and `stack` sets to track nodes already explored and the path being traversed during
            depth-first search (DFS), respectively.
            2. Employs a recursive `visit` function to perform DFS from any given node, identifying and visiting all its
             dependencies.
            3. Marks nodes as visited by adding them to `visited` and `stack` upon exploration. This helps in tracking
            the DFS path and detecting cycles.
            4. Recursively explores all dependencies for each node. Dependencies are defined by the node's strategy,
            reflecting the calculation dependencies.
            5. Removes a node from `stack` once all its dependencies are explored (when it reaches the leaves),
            signifying the completion of its DFS branch.
            6. Detects cycles when a node appears in `stack` more than once during its visit, indicating a path looped
            back on itself, and raises an exception.
            7. Iterates over all nodes in the graph, ensuring every node is visited, which accommodates for any
            disconnected components within the graph.

        Note:
            This method should be called every times the graph is modified (nodes added or updated).
            Detecting cycles beforehand prevents runtime errors due to infinite recursion or deadlock situations.
            WARNING : DSF algorithm may take a long time to execute if the graph is very large. It should only be used
            when updating the graph.
        """
        visited = set()
        stack = set()

        def visit(node_name):
            if node_name in stack:
                raise Exception(f"Cyclic dependency detected involving {node_name}")
            if node_name not in visited:
                stack.add(node_name)
                visited.add(node_name)
                node = self.nodes.get(node_name)
                if node and node._strategy:
                    for dep_name in node._strategy.get_dependencies():
                        visit(dep_name)
                stack.remove(node_name)  # Utilisez node_name ici au lieu de node

        for node_name in self.nodes:
            if node_name not in visited:
                visit(node_name)

    def add_or_update_node(self, node_name: str, strategy=None):
        """
        Adds a new calculation node or updates the strategy of an existing node.

        Parameters:
            node_name (str): The name of the node to add or update.
            strategy (CalculationStrategy, optional): The calculation strategy to assign to the node.
        """
        node = self.get_or_create_node(node_name)
        node.set_strategy(strategy)

        # Switching calculation strategy requires re-calculating the node's value, it's equivalent to a change in the
        # parameters set

        self.update_parameters(self.current_parameters)

        # Check for cycles in the graph after adding or updating a node
        self.check_for_cycles()

    def update_parameters(self, new_parameters: InputParameters):
        """
        Updates the parameters used for calculations and archives the current results.

        Parameters:
            new_parameters (InputParameters): The new set of parameters for subsequent calculations.
        """
        self.old_parameters = self.current_parameters
        self.current_parameters = new_parameters

        if self.current_output_data.results:
            self.old_output_data = self.current_output_data
        self.current_output_data = CalculationResults()

    def run_calculations(self):
        """
        Executes the calculations for all nodes in the calculation graph.

        Iterates over each node, performing calculations based on their strategies
        and the current set of parameters. Results are stored in `current_output_data`.
        """
        # Use a list of node names to prevent modification during iteration errors
        node_names = list(self.nodes.keys())
        for name in node_names:
            self.nodes[name].calculate()

    def __repr__(self):
        return f"CalculationEngine({self.nodes})"

