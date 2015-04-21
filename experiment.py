from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import *
from sklearn.linear_model import *
from sklearn.naive_bayes import *
from sklearn.neighbors import *
from sklearn.svm import *
import sys
import os
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
                'n_estimators': 100,
                'learning_rate': 0.5
            }
        },
        {
            'name': 'Extra trees classifier',
            'class_name': ExtraTreesClassifier,
            'parameters': {
                'n_estimators': 100,
                'n_jobs': 2
            }
        },
        {
            'name': 'Random forest classifier',
            'class_name': RandomForestClassifier,
            'parameters': {
                'n_estimators': 100,
                'n_jobs': 2
            }
        },
        {
            'name': 'Passsive aggressive classifier',
            'class_name': PassiveAggressiveClassifier,
            'parameters': {
                'C': 0.2,
                'n_jobs': 2
            }
        },
        {
            'name': 'SGD classifier',
            'class_name': SGDClassifier,
            'parameters': {
                'alpha': 0.001,
                'n_iter': 10
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
                'alpha': 0.8
            },
            'dense': True
        },
        {
            'name': 'Bernoulli naive Bayes classifier',
            'class_name': BernoulliNB,
            'parameters': {
                'alpha': 0.01
            }
        },
        {
            'name': 'K neighbors classifier',
            'class_name': KNeighborsClassifier,
            'parameters': {
                'n_neighbors': 25,
                'weights': 'distance'
            }
        },
        {
            'name': 'Linear SVC',
            'class_name': LinearSVC,
            'parameters': {
                'C': 0.8
            }
        },
        {
            'name': 'Nu SVC',
            'class_name': NuSVC,
            'parameters': {
                'nu': 0.8
            }
        }
    ]

    for algorithm in algorithms:
        if 'disabled' in algorithm and algorithm['disabled']:
            continue
        if filter and filter not in algorithm['name'].lower() and filter not in algorithm['class_name'].__name__.lower():
            continue

        dense = algorithm['dense'] if 'dense' in algorithm else False
        classifier = Classifier('id')
        classifier.create_model(train=False, class_name=algorithm['class_name'], parameters=algorithm['parameters'], dense=dense)

        print(Utilities.get_colored_text(0, '::: {} :::'.format(algorithm['name'])))
        classifier.output_cross_validate(folds)
        print('')

if __name__ == "__main__":
    main(sys.argv[1:])
