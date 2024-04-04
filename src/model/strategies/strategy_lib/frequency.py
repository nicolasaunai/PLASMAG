import numpy as np

from src.model.input_parameters import InputParameters
from src.model.strategies import CalculationStrategy


class FrequencyVectorStrategy(CalculationStrategy):
    def calculate(self, dependencies: dict, parameters: InputParameters):
        f_start = parameters.data['f_start']
        f_stop = parameters.data['f_stop']
        nb_points_per_decade = parameters.data['nb_points_per_decade']
        frequency_vector = np.logspace(np.log10(f_start), np.log10(f_stop),
                                       int((np.log10(f_stop) - np.log10(f_start)) * nb_points_per_decade))
        return {
            "data": frequency_vector,
            "labels": ["Frequency"],
            "units": ["Hz"]
        }

    @staticmethod
    def get_dependencies():
        return ['f_start', 'f_stop', 'nb_points_per_decade']


