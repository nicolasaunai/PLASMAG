# Table of Contents

- [How to add a new calculation strategy](#How-to-add-a-new-calculation-strategy)
  - [Preliminary Checks](#Preliminary-Checks)
  - [Adding New Parameters](#Adding-New-Parameters)
  - [Strategy Implementation](#Strategy-Implementation)
  - [Method Specifications](#Method-Specifications)
    - [Dependencies](#Dependencies)
    - [Calculate method](#Calculate-method)
- [How to add a new parameter](#How-to-add-a-new-parameter)
     - [Unit Conversion](#Unit-Conversion)
- [Linting](#Linting)
- [Git Guidelines](#Git-Guidelines)
  - [Branching Strategy](#Branching-Strategy)
  - [Commit Message Format](#Commit-Message-Format)
    - [Types](#Types)
  - [Best Practices for Pull Requests](#Best-Practices-for-Pull-Requests)
- [SPICE](#SPICE)

# How to add a new calculation strategy

## Preliminary Checks

1. Review Existing Strategies: Inspect all the calculation strategies in the calculation_strategies folder to ensure your strategy hasn't already been implemented.
2. Review Parameters: Examine the parameters defined in `/data/default.json`. Determine if new parameters are needed for your strategy.

## Adding New Parameters
3. Parameter Addition: If your strategy introduces new parameters, add them to the ``default.json`` file. Refer to the Adding a New Parameter section for detailed guidance.4. Check all the existing Nodes you can use. The list of existing nodes and their calculation strategy can be found in `src/controler/controller.py`.

## Strategy Implementation
4. Utilize Existing Nodes: Explore the list of nodes in ``src/controller/controller.py``to understand the available calculation strategies. Avoid recalculating nodes.
```python
self.engine.add_or_update_node('frequency_vector', FrequencyVectorStrategy())
self.engine.add_or_update_node('resistance', AnalyticalResistanceStrategy())
self.engine.add_or_update_node('Nz', AnalyticalNzStrategy())
...
```
DO NOT recalculate the same node with a different strategy. Instead, apply your new strategy to an existing node.


5. If your calculation strategy is not implemented, create a new file in the `src/model/strategies/strategy_lib/` folder with the name of your calculation strategy.

This file should:
- Inherit from the `CalculationStrategy` class.
- Implement the `calculate` method.
- Implement the `get_dependencies` method.


6. Node Association: Incorporate your newly created strategy into the controller by assigning it to a node.
```python

self.engine.add_or_update_node('node_name', YourStrategy())

```

## Method Specifications

### Dependencies
- The get_dependencies method must return a list of required parameters or nodes as strings, matching their names in the default.json file or controller.
### Calculate method
The `calculate` method must return the result of the calculation. The method takes two arguments:
- `dependencies`: A dictionary containing the values of all the nodes available in the engine. The keys are the names of the nodes, and the values are the results of the calculation.
- `parameters`: An instance of the `InputParameters` class containing the values of the parameters entered by the user.

This method must return the result of the calculation. 
The result can be on of the following:
- A single value (int, float, etc.)
- A Tensor (2D array) containing the result of the calculation for each frequency value. The first column must be the frequency values or (the x_axis for the plot), and the following columns must be the result of the calculation.

ALL OUTPUTS MUST BE IN SI UNITS in linear scale (no dB, no log scale).


### Examples : 
```python
class AnalyticalResistanceStrategy(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        N = parameters.data['nb_spire']
        Rs = parameters.data['ray_spire']
        rho = parameters.data['rho_whire']
        return N * (2 * np.pi * Rs) * rho

    @staticmethod
    def get_dependencies():
        return ['nb_spire', 'ray_spire', 'rho_whire']
```

```python
class AnalyticalImpedanceStrategy(CalculationStrategy):

    def calculate(self, dependencies: dict, parameters: InputParameters):
        R = dependencies['resistance']
        L = dependencies['inductance']
        C = dependencies['capacitance']

        frequency_vector = dependencies['frequency_vector']


        vectorized_impedance = np.vectorize(self.calculate_impedance)
        impedance_values = vectorized_impedance(R, L, C, frequency_vector)
        frequency_impedance_tensor = np.column_stack((frequency_vector, impedance_values))
        return frequency_impedance_tensor
    
    def calculate_impedance(self, R, L, C, f):
        impedance_num = (R ** 2) + (L * 2 * np.pi * f) ** 2
        impedance_den = (1 - L * C * (2 * np.pi * f) ** 2) ** 2 + (R * C * (2 * np.pi * f)) ** 2
        return np.sqrt(impedance_num / impedance_den)

    @staticmethod
    def get_dependencies():
        return ['resistance', 'inductance', 'capacitance', 'frequency_vector']

```

# How to add a new parameter

1. **Existing Parameters:** Verify if the new parameter exists within /data/default.json.
2. **Addition:** Introduce new parameters to `default.json` as needed, adhering to the specified format:
The file must be in the following format:

```json
{ "section_name": 
  {
      "param_name": {
            "default": XX,
            "min": XX,
            "max": XX,
            "description": "Short description, used for the user interface",
            "input_unit": "",
            "target_unit": ""
        }
  }
}

```

Note that the `section_name` is the name of the section in the user interface. The `param_name` is the name of the parameter in the user interface.
Each section can have multiple parameters.

These are the fields that must be filled in if your parameter is a number that require unit conversion:

```json
"input_unit": "",
"target_unit": ""
```
### Unit Conversion


For example, you don't want to input a lenght in mm and write 0.001 m in the input field. You can define the input unit as mm and the target unit as m. The user will input 1 mm and the system will convert it to 0.001 m.

Utilize the ``pint`` library for unit conversion. Input and target units should be defined for parameters requiring conversion.
For comprehensive unit support and details, visit Pint's documentation.

Example:
```json
"capa_triwire": {
            "default": 150,
            "min": 10,
            "max": 1000,
            "description": "Triwire capacitance in picofarads",
            "input_unit": "picofarad",
            "target_unit": "farad"
        }
```

# Linting

We use pylint to ensure compliance with PEP8 guidelines. Lint your code with:
```bash
 pylint --rcfile pylintrc src/folder/file.py
```

Replace `src/folder/file.py` with the path to the file you want to lint.
Check the return of the command to see if there are any errors or warnings in the code. Adapt and correct the code according to the pylint output.

You can read the [pylint documentation](https://pylint.pycqa.org/en/latest/) for more information on how to use pylint.

# Git Guidelines

To maintain the repository's integrity and streamline development processes, we adhere to a GitFlow-inspired workflow and specific naming conventions for branches and commit messages. Below is a comprehensive guide on how to contribute code to this project effectively.

## Branching Strategy

We use a branching strategy that categorizes work based on the nature of changes, ensuring that our repository remains organized and manageable. When starting work on a new feature, bug fix, or other tasks, you must create a new branch following these conventions:

- **Feature Branches**: `engine/branch-name`, `UI/branch-name`, `controller/branch-name`
- **Refactoring**: `refactor/branch-name`

**Important**: Direct commits to the `dev` branch are prohibited. Always create a new branch for your work, branching off from the latest `dev` branch.

## Commit Message Format

Commit messages should be clear, concise, and follow a formal structure to simplify the repository's history. Use the following format:

```
TYPE[TAG] - DESCRIPTION

[optional body]

[optional footer(s)]
```


**Tags**: Include `#issue_id` if your work addresses a specific open issue.

### Types

- `FEAT`: Introduces a new feature.
- `FIX`: Fixes a bug.
- `CHORE`: Changes that don't affect the source or test files, like updating dependencies.
- `REFACTOR`: Code changes that neither fix a bug nor add a feature.
- `DOC`: Documentation updates.
- `QUAL`: General code quality improvements.
- `TEST`: Adds or updates tests.
- `PERF`: Performance improvements.
- `REVERT`: Reverts a previous commit.

For more detailed examples and best practices on commit messages, refer to [this article](https://www.freecodecamp.org/news/how-to-write-better-git-commit-messages/).

## Best Practices for Pull Requests

- **Scope**: Keep your pull requests small and focused on a single feature or bug fix to facilitate the review process.
- **Adherence to Standards**: Ensure your contributions follow the project's coding standards and guidelines.
- **Stay Updated**: Regularly update your fork to keep it in sync with the main project. This helps in minimizing merge conflicts.
- **Linting**: Run the linter on your code before submitting a pull request to ensure compliance with PEP8 guidelines.
- **Documentation**: Update the documentation if your changes affect the project's functionality or require additional information.

By following these guidelines, you contribute to the efficiency and clarity of the project, making it easier for others to review your contributions and maintain the project's health.

# SPICE

Simulation Program with Integrated Circuit Emphasis (SPICE) is a general-purpose analog electronic circuit simulator. It is a powerful tool for simulating and analyzing circuits, providing valuable insights into circuit behavior and performance. SPICE is widely used in the electronics industry for designing and testing circuits, making it an essential tool for electrical engineers and circuit designers.

In PLASMAG, we integrate spice simulations to allow the user to create their own models and have more accurate results.

## How to add a new SPICE model

### 1. Prepare the JSON Configuration for the SPICE Module

Each SPICE module is defined in a JSON file, which outlines the circuit characteristics along with associated parameters and calculation strategies. Here are the steps to prepare this file:

1. **Module Key Creation:** 
Add a new key in the JSON file (e.g., **spice_new_model**) that will act as a unique identifier for the new module.

2. **Defining Module Attributes:**
    -  **name:** The name of the module, such as "New OP AMP Model".
    - **description:** A detailed description of the module, used for the user interface.
    - **image:** The filename of the image representing the circuit (must be pre-added to the relevant images directory).

3. **Parameters:**
    Define all necessary parameters for the module. Each parameter should include:
   - **default, min, max:** Default, minimum, and maximum values.
   - **description:** A description of the parameter for the user interface.
   - **input_unit and target_unit:** Input and conversion units, if applicable.

4. **Strategies:**
    - Add references to specific calculation strategies used by this module in the `src/model/strategies/strategy_lib/` directory.
    - Each strategy must have a **name** and a **file** pointing to the Python script implementing the strategy.

#### Example JSON Section for a New SPICE Module

```json
"spice_new_model" : {
    "name" : "New OP AMP Model",
    "description" : "An advanced test circuit for the spice simulator",
    "image" : "new_op_amp_model.png",
    "parameters" : {
        "R1": {
            "default": 500,
            "min": 10,
            "max": 10000,
            "description": "Spice test resistance",
            "input_unit": "ohm",
            "target_unit": "ohm"
        }
    },
    "strategies" : {
        "SPICE_impedance" : {
            "name" : "SPICE Impedance",
            "file" : "src/model/strategies/strategy_lib/SPICE.py"
        }
    }
}

```

### 2. Implement Calculation Strategies

For each strategy listed in the JSON configuration:

- Create a Python class in the specified file within `src/model/strategies/strategy_lib/`.
- Each class should inherit from the **CalculationStrategy** class and implement necessary methods such as **calculate** and **get_dependencies**.
- The calculate method should handle the specific SPICE simulation logic based on input parameters and dependencies defined in the module.


### 3. Test and Validate

Once the new module is configured and the strategies are implemented:

- Test the module extensively to ensure that it works as expected with the SPICE simulator. You can try the script outside of PLASMAG
in the `if __name__ == "__main__"`, with mock data.
- Validate that all parameters and calculations produce accurate and reliable results.

### 4. Update User Documentation and Interface

-  Add any necessary documentation to help users understand how to use the new SPICE module.

### 5. Commit Changes

Follow the project's Git guidelines to commit and push the new module to the repository:

- Create a feature branch, e.g., feature/spice_new_model.
- Commit your changes with a clear message describing the addition of the new SPICE module.
- Open a pull request for review.

### 5. MISC

- Make sure to return the results in SI units for consistency. X-axis values should be in Hz, or seconds for time-domain simulations.
- If the X-axis is in the time domain, make sure to return the time vector as the first column of the tensor, with the following label : "Time"
- If you are returning the Gain and the Phase, make sure to return a linear Gain, and the phase in radians. The first column should be the frequency values, the second column the gain, and the third column the phase, with the following labels : "Frequency", "Gain", "Phase"
