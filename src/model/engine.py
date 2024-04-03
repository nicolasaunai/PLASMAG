import json
import copy

from src.model.results import CalculationResults
from src.model.input_parameters import InputParameters
from src.model.node import CalculationNode


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

    def __init__(self, backups_count=3):
        """
               Initializes the calculation engine, setting up internal storage for parameters, nodes,
               and calculation results.
       """
        self.current_parameters = None
        self.old_parameters = None
        self.nodes = {}
        self.old_output_data = None
        self.current_output_data = CalculationResults()
        self.inverse_dependencies = {}
        self.build_inverse_dependencies()
        self.first_run = True

        self.saved_data_results = [CalculationResults() for _ in range(backups_count)]
        print(len(self.saved_data_results))
        print("Calculation Engine Initialized")

    def save_calculation_results(self, index):
        """
        Saves the current calculation results to a specific index in the saved_data_results list.
        """
        self.saved_data_results[index] = copy.deepcopy(self.current_output_data)
        print("Results saved to index: ", index)

    def clear_calculation_results(self):
        """
        Clears all data from the saved_data_results list at a specific index.
        """
        self.saved_data_results = [CalculationResults() for _ in range(5)]
        print("Results cleared")




    def build_inverse_dependencies(self):
        """
                Constructs a map of inverse dependencies for each node to efficiently update dependent nodes
                when parameters change. This map is used for identifying which nodes need recalculating when
                input parameters are updated.
        """
        self.inverse_dependencies = {}

        def add_inverse_dependency(node_name, dependency):
            """
                        Helper function to recursively build inverse dependencies.
            """
            if dependency not in self.inverse_dependencies:
                self.inverse_dependencies[dependency] = set()
            self.inverse_dependencies[dependency].add(node_name)
            if dependency in self.nodes:
                for sub_dependency in self.nodes[dependency].get_strategy().get_dependencies():
                    add_inverse_dependency(node_name, sub_dependency)

        for node_name, node in self.nodes.items():
            if node.get_strategy():
                for dependency in node.get_strategy().get_dependencies():
                    add_inverse_dependency(node_name, dependency)

    def export_inverse_dependencies_to_json(self, file_path):
        """
                Exports the current inverse dependencies map to a JSON file, useful for debugging
                or documentation purposes.

                Parameters:
                    file_path (str): The file path where the JSON data should be saved.
        """
        inverse_dependencies_json = {key: list(value) for key, value in self.inverse_dependencies.items()}

        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(inverse_dependencies_json, json_file, indent=4)

    def count_nodes(self):
        """
        Returns the number of nodes in the calculation graph.

        Returns:
            int: The number of calculation nodes in the graph.
        """
        return len(self.nodes)

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
            if not node or not node.get_strategy():
                # If the node does not exist or has no strategy (and thus no dependencies), return an empty dict
                return {}

            dependencies = {}
            for dep_name in node.get_strategy().get_dependencies():
                # Recursively build the tree for each dependency
                dependencies[dep_name] = build_tree(dep_name)
            return dependencies

        # Corrected approach to identify head nodes
        all_dependencies = set()
        for node in self.nodes.values():
            if node.get_strategy():
                all_dependencies.update(node.get_strategy().get_dependencies())

        head_nodes = [node_name for node_name in self.nodes if node_name not in all_dependencies]

        # Build the dependency tree starting from each head node
        dependency_tree = {}
        for head_node in head_nodes:
            dependency_tree[head_node] = build_tree(head_node)

        # Save the tree to a file in JSON format if a path is specified
        if path:
            with open(path, 'w', encoding='utf-8') as json_file:
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
                stack.remove(node_name)

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

        # self.update_parameters(self.current_parameters)

        # Check for cycles in the graph after adding or updating a node
        self.check_for_cycles()
        self.build_inverse_dependencies()

    def get_affected_nodes(self, changed_params):
        """
        Identifies nodes affected by the changed parameters.

        Parameters:
            changed_params (dict): A dictionary of changed parameters.

        Returns:
            Set[str]: A set of node names that are affected by the changed parameters.
        """
        # Initialize an empty set to collect affected node names
        affected_nodes = set()

        # Loop through each changed parameter to find affected nodes
        for changed_param in changed_params.keys():
            if changed_param in self.inverse_dependencies:
                # If the changed parameter has inverse dependencies, add all nodes
                # that are dependent on this parameter to the affected nodes set
                affected_nodes.update(self.inverse_dependencies[changed_param])

        return affected_nodes

    def update_parameters(self, new_parameters: InputParameters):
        """
        Updates the parameters used for calculations and archives the current results.

        Parameters:
            new_parameters (InputParameters): The new set of parameters for subsequent calculations.
        """
        if self.first_run:
            self.first_run = False
            self.current_parameters = new_parameters
            self.run_calculations()

        changed_params = {}

        if self.current_parameters is not None:
            for param, new_value in new_parameters.data.items():
                old_value = self.current_parameters.data.get(param, None)
                if new_value != old_value:
                    changed_params[param] = {'old': old_value, 'new': new_value}

        self.old_parameters = self.current_parameters
        self.current_parameters = new_parameters

        if self.current_output_data.results:
            self.old_output_data = copy.deepcopy(self.current_output_data)

        if changed_params:
            affected_nodes = self.get_affected_nodes(changed_params)

            for node_name in affected_nodes:
                self.nodes[node_name].mark_for_recalculation()
            self.run_calculations(affected_nodes)

    def run_calculations(self, node_names=None):
        """
        Executes the calculations for all nodes in the calculation graph.

        Iterates over each node, performing calculations based on their strategies
        and the current set of parameters. Results are stored in `current_output_data`.

        THIS METHOD shouldn't be called directly, it should be called by update_parameters method
        """
        if node_names is None:
            node_names = list(self.nodes.keys())
        for name in node_names:
            self.nodes[name].calculate()

    def __repr__(self):
        """
        Returns a string representation of the calculation engine calculation nodes
        """
        return f"CalculationEngine({self.nodes})"
