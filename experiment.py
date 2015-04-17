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
    algorithms = [
        {
            'name': 'Ada Boost classifier',
            'class_name': AdaBoostClassifier,
            'parameters': {
                'n_estimators': 100,
                'learning_rate': 0.5
            },
            'enabled': True
        },
        {
            'name': 'Extra trees classifier',
            'class_name': ExtraTreesClassifier,
            'parameters': {
                'n_estimators': 100,
                'n_jobs': 2
            },
            'enabled': True
        },
        {
            'name': 'Random forest classifier',
            'class_name': RandomForestClassifier,
            'parameters': {
                'n_estimators': 100,
                'n_jobs': 2
            },
            'enabled': True
        },
        {
            'name': 'Passsive aggressive classifier',
            'class_name': PassiveAggressiveClassifier,
            'parameters': {
                'C': 0.2,
                'n_jobs': 2
            },
            'enabled': True
        },
        {
            'name': 'SGD classifier',
            'class_name': SGDClassifier,
            'parameters': {
                'alpha': 0.001,
                'n_iter': 10
            },
            'enabled': True
        },
        {
            'name': 'Bernoulli naive Bayes classifier',
            'class_name': BernoulliNB,
            'parameters': {
                'alpha': 0.001
            },
            'enabled': True
        },
        {
            'name': 'K neighbors classifier',
            'class_name': KNeighborsClassifier,
            'parameters': {},
            'enabled': True
        },
        {
            'name': 'Linear SVC',
            'class_name': LinearSVC,
            'parameters': {
                'C': 0.8
            },
            'enabled': True
        },
        {
            'name': 'Nu SVC',
            'class_name': NuSVC,
            'parameters': {
                'nu': 0.8
            },
            'enabled': True
        }
    ]

    for algorithm in algorithms:
        if not algorithm['enabled']:
            continue

        classifier = Classifier('id')
        classifier.create_model(train=False, class_name=algorithm['class_name'], parameters=algorithm['parameters'])

        print(Utilities.get_colored_text(0, '::: {} :::'.format(algorithm['name'])))
        print('Performing cross-validation on {} folds'.format(folds))
        results = classifier.cross_validate(folds)
        print('Folds: {}'.format(results))
        print('Average: {}'.format(results.mean()))
        print('Standard deviation: {}'.format(results.std()))
        print('')

if __name__ == "__main__":
    main(sys.argv[1:])
