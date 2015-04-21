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
from classify import Classifier
from utils import Utilities

def main(argv):
    folds = int(argv[0]) if len(argv) > 0 else 5
    filter = argv[1].lower() if len(argv) > 1 else ""
    algorithms = [
        {
            'name': 'Ada Boost classifier',
            'class_name': AdaBoostClassifier,
            'parameters': {
                'n_estimators': [10, 50, 100, 250, 500],
                'learning_rate': [0.1, 0.2, 0.3, 0.4, 0.5]
            }
        },
        {
            'name': 'Extra trees classifier',
            'class_name': ExtraTreesClassifier,
            'parameters': {
                'n_estimators': [10, 50, 100, 250, 500],
                'n_jobs': [2]
            }
        },
        {
            'name': 'Random forest classifier',
            'class_name': RandomForestClassifier,
            'parameters': {
                'n_estimators': [10, 50, 100, 250, 500],
                'n_jobs': [2]
            }
        },
        {
            'name': 'Passsive aggressive classifier',
            'class_name': PassiveAggressiveClassifier,
            'parameters': {
                'C': [0.1, 0.2, 0.3, 0.4, 0.5],
                'n_jobs': [2]
            }
        },
        {
            'name': 'SGD classifier',
            'class_name': SGDClassifier,
            'parameters': {
                'alpha': [0.0001, 0.001, 0.005, 0.01, 0.2],
                'n_iter': [2, 4, 6, 8, 10, 15, 20]
            }
        },
        {
            'name': 'Gaussian naive Bayes classifier',
            'class_name': GaussianNB,
            'parameters': {},
            'dense': True
        },
        {
            'name': 'Multinomial naive Bayes classifier',
            'class_name': MultinomialNB,
            'parameters': {
                'alpha': [0.2, 0.4, 0.5, 0.7, 0.8]
            },
            'dense': True
        },
        {
            'name': 'Bernoulli naive Bayes classifier',
            'class_name': BernoulliNB,
            'parameters': {
                'alpha': [0.0001, 0.001, 0.005, 0.01, 0.2]
            }
        },
        {
            'name': 'K neighbors classifier',
            'class_name': KNeighborsClassifier,
            'parameters': {
                'n_neighbors': [5, 10, 15, 20, 25, 30, 50],
                'weights': ['uniform', 'distance']
            }
        },
        {
            'name': 'Linear SVC',
            'class_name': LinearSVC,
            'parameters': {
                'C': [0.1, 0.2, 0.3, 0.4, 0.5]
            }
        },
        {
            'name': 'Nu SVC',
            'class_name': NuSVC,
            'parameters': {
                'nu': [0.1, 0.2, 0.3, 0.4, 0.5]
            }
        }
    ]

    for algorithm in algorithms:
        if 'disabled' in algorithm and algorithm['disabled']:
            continue
        if filter and filter not in algorithm['name'].lower() and filter not in algorithm['class_name'].__name__.lower():
            continue

        dense = algorithm['dense'] if 'dense' in algorithm else False
        parameter_combinations = itertools.product(*algorithm['parameters'].values())
        for combination in parameter_combinations:
            classifier = Classifier('id')
            class_name = algorithm['class_name']
            parameters = dict(zip(algorithm['parameters'].keys(), combination))
            classifier.create_model(train=False, class_name=class_name, parameters=parameters, dense=dense)

            parameter_string = ', '.join("%s=%r" % (key,val) for (key,val) in parameters.iteritems())
            print(Utilities.get_colored_text(0, '::: {} ({}) :::'.format(algorithm['name'], parameter_string)))
            classifier.output_cross_validate(folds)
            print('')

if __name__ == "__main__":
    main(sys.argv[1:])
