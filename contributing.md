
# How to add a new calculation strategy

1. Check all the existing calculation strategies in the `calculation_strategies` folder to see if your calculation strategy is already implemented.
2. Check all the existing parameters defined in `/data/default.json` to see if your calculation strategy requires any new parameters.
3. If your calculation strategy requires new parameters, add them to the `default.json` file. Check [Parameter](#How to add a new parameter) section for more details.
4. Check all the existing Nodes you can use. The list of existing nodes and their calculation strategy can be found in `src/controler/controller.py`.
```python
self.engine.add_or_update_node('frequency_vector', FrequencyVectorStrategy())
self.engine.add_or_update_node('resistance', AnalyticalResistanceStrategy())
self.engine.add_or_update_node('Nz', AnalyticalNzStrategy())
...
```
Make sure to do not recalculating the same node multiple times. 
5. If your calculation strategy is not implemented, create a new file in the `src/model/strategies/strategy_lib/` folder with the name of your calculation strategy.

Strategy files must be in the following format:
- They must inherit from the `CalculationStrategy` class.
- They must implement the `calculate` method.
- They must implement the `get_dependencies` method.


6. Add your just created strategy to a node in the controller. 
```python

self.engine.add_or_update_node('node_name', YourStrategy())

```
### Dependencies
The "Get_dependencies" method must return a list of the parameters or nodes that the calculation strategy requires to calculate the result.
Each parameter or node must be a string, and the string must match the name of the parameter in the `default.json` file or node name in the controller.

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

1. Check all the existing parameters defined in `/data/default.json` to see if your calculation strategy requires any new parameters.
2. If your calculation strategy requires new parameters, add them to the `default.json` file.

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

For example, you don't want to input a lenght in mm and write 0.001 m in the input field. You can define the input unit as mm and the target unit as m. The user will input 1 mm and the system will convert it to 0.001 m.

Units conversion is done using the `pint` library. You can find the list of supported units and more details [here](https://pint.readthedocs.io/en/stable/index.html).

Another example:
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

We use pylint to lint the code and ensure that it follows the PEP8 guidelines. You can run the linting with the following command:

```bash
 pylint --rcfile pylintrc src/folder/file.py
```

Replace `src/folder/file.py` with the path to the file you want to lint.
Check the return of the command to see if there are any errors or warnings in the code. Adapt and correct the code according to the pylint output.

You can read the [pylint documentation](https://pylint.pycqa.org/en/latest/) for more information on how to use pylint.


