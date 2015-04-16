from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import *
from sklearn.linear_model import *
from sklearn.naive_bayes import *
from sklearn.neighbors import *
import sys
import os
from classify import Classifier
from utils import Utilities

class Experiment_Classifier(Classifier):
    def __init__(self):
        Classifier.__init__(self, 'id', 100)

    def create_model(self, class_name):
        models = [
            ('tfidf', TfidfVectorizer(input='content', tokenizer=Utilities.split)),
            ('clf', class_name())
        ]
        self.regressor = Pipeline(models)
        self.train()

def main(argv):
    folds = int(argv[0]) if len(argv) > 0 else ""
    algorithms = {
        'Ada Boost classifier': AdaBoostClassifier,
        'Extra trees classifier': ExtraTreesClassifier,
        'Random forest classifier': RandomForestClassifier,
        'Passsive aggressive classifier': PassiveAggressiveClassifier,
        'SGD classifier': SGDClassifier,
        'Bernoulli naive Bayes classifier': BernoulliNB,
        'K neighbors classifier': KNeighborsClassifier
    }

    for algorithm, class_name in algorithms.iteritems():
        classifier = Experiment_Classifier()
        classifier.create_model(class_name)

        print(Utilities.get_colored_text(0, '::: {} :::'.format(algorithm)))
        print('Performing cross-validation on {} folds'.format(folds))
        results = classifier.cross_validate(folds)
        print('Folds: {}'.format(results))
        print('Average: {}'.format(results.mean()))
        print('Standard deviation: {}'.format(results.std()))
        print('')

if __name__ == "__main__":
    main(sys.argv[1:])
