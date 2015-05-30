from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import *
from sklearn.linear_model import *
from sklearn.naive_bayes import *
from sklearn.neighbors import *
from sklearn.svm import *
import sys
import os
import itertools
import json
from collections import OrderedDict
from classify import Classifier
from utils import Utilities

def main(argv):
    folds = int(argv[0]) if len(argv) > 0 else 5
    filter = argv[1].lower() if len(argv) > 1 else ""

    # Fields to check whether the filter, if given, appears in.
    filter_fields = ['name', 'class_name', 'module']

    # Read the manifest containing algorithm descriptions.
    with open('algorithms.json', 'r') as manifest:
        algorithms = json.load(manifest)

    # Load previous results
    try:
        with open('experiment_results.json', 'r') as file:
            results = json.load(file)
    except:
        results = {}

    for algorithm in algorithms:
        # Skip running the algorithm if it is disabled or the filter name does 
        # not appear in any of the fields.
        if 'disabled' in algorithm and algorithm['disabled']:
            continue
        if filter and all([filter not in algorithm[k].lower() for k in filter_fields]):
            continue

        # Convert manifest entries to classifier class and parameters
        class_name = Utilities.get_class(algorithm['module'], algorithm['class_name'])
        dense = algorithm['dense'] if 'dense' in algorithm else False

        # Create all possible combinations of parameters.
        parameter_combinations = itertools.product(*algorithm['parameters'].values())

        single_parameters = [param for param,values in algorithm['parameters'].iteritems() if len(values) == 1]
        string_parameters = [param for param,values in algorithm['parameters'].iteritems() if isinstance(values[0],(str,unicode))]
        for combination in parameter_combinations:
            classifier = Classifier('id')

            # Turn the selected parameter combination back into a dictionary
            parameters = dict(zip(algorithm['parameters'].keys(), combination))

            # Create the model according to the parameters
            classifier.create_model(train=False, class_name=class_name, parameters=parameters, dense=dense)

            Utilities.print_algorithm(algorithm['name'], parameters)
            parameter_string = Utilities.get_parameter_string(parameters, single_parameters + string_parameters)

            # Run cross-validation and print results
            result = classifier.output_cross_validate(folds)
            print('')

            name = algorithm['name']
            for param in string_parameters:
                name += ", %s=%s" % (param,parameters[param])

            # Write the result measurements into the results dictionary.
            if name not in results:
                results[name] = OrderedDict()
            
            results[name].update({
                parameter_string: {
                    'average': result.mean(),
                    'standard_deviation': result.std()
                }
            })

            # Write intermediate results (back) into a pretty-printed JSON file
            with open('experiment_results.json', 'w') as file:
                json.dump(results, file, indent=4, separators=(',', ': '))

if __name__ == "__main__":
    main(sys.argv[1:])
