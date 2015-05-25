from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.base import TransformerMixin
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn import cross_validation
import numpy as np
import sys
import itertools
import linecache
import json
import os
import pickle
from glob import glob
from utils import Utilities

# Make it possible to use classifiers and regressors that want dense matrices 
# as input with our TF.IDF vecotrizer transformer in the pipeline.
# Source: 
# http://zacstewart.com/2014/08/05/pipelines-of-featureunions-of-pipelines.html
class DenseTransformer(TransformerMixin):
    def transform(self, X, y=None, **fit_params):
        return X.todense()

    def fit_transform(self, X, y=None, **fit_params):
        self.fit(X, y, **fit_params)
        return self.transform(X)

    def fit(self, X, y=None, **fit_params):
        return self

class Classifier(object):
    def __init__(self, group, model_file=""):
        self.dataset_name = "commit_comments-dump.2015-01-29"
        self.group = group
        self.display = (self.group == "id")
        self.model_file = model_file
        self.train_ids = set()

    def create_model(self, train=True, class_name=DummyRegressor, parameters={}, dense=False):
        trained = False
        if self.model_file != "" and os.path.isfile(self.model_file):
            with open(self.model_file, 'rb') as f:
                objects = pickle.load(f)
                models = objects[0:-1]
                models[0][1].tokenizer = Utilities.split
                self.train_ids = objects[-1][1]
                trained = True
        else:
            models = []
            models.append(('tfidf', TfidfVectorizer(input='content', tokenizer=Utilities.split)))
            if dense:
                models.append(('to_dense', DenseTransformer()))
            models.append(('clf', class_name(**parameters)))

        self.regressor = Pipeline(models)

        if not trained and train:
            self.train()
            if self.model_file != "":
                with open(self.model_file, 'wb') as f:
                    models[0][1].tokenizer = None
                    models.append(('train_ids', self.train_ids))
                    pickle.dump(models, f)
                    print("Wrote trained model to output file {}".format(self.model_file))

    def get_train_data(self):
        # Collect the training data
        train_data = []
        train_labels = []
        with open(self.dataset_name + ".labeled.json", 'r') as f:
            i = 0
            for data in Utilities.read_json(f, ['id','label'], self.group):
                i = i + 1
                score = Utilities.label_to_score(data["label"])
                if score is None: # unknown
                    continue

                line = linecache.getline(self.dataset_name + '.json', i)
                json_object = json.loads(line)
                if json_object['id'] != data['id']:
                    raise(ValueError('ID in label dataset does not match with dataset on line {}: {} vs {}'.format(i, data['id'], json_object['id'])))

                message = json_object['body'].replace('\r\n', '\n')
                self.train_ids.add(data['id'])
                train_data.append(message)
                train_labels.append(score)
        
        return (train_data, train_labels)

    def train(self):
        (train_data, train_labels) = self.get_train_data()
        # Train the regressor
        self.regressor.fit(train_data, train_labels)

    def cross_validate(self, folds=5):
        (train_data, train_labels) = self.get_train_data()
        # Crossvalidate the regressor on the labeled data
        return cross_validation.cross_val_score(self.regressor, train_data, train_labels, cv=folds)

    def output_cross_validate(self, folds=5):
        print('Performing cross-validation on {} folds'.format(folds))
        results = self.cross_validate(folds)
        print('Folds: {}'.format(results))
        print('Average: {}'.format(results.mean()))
        print('Standard deviation: {}'.format(results.std()))
        return results

    def split(self, data):
        if self.group != "score":
            self.test_group.append(data['group'])
        return data['message']

    def filter(self, data):
        return data['id'] not in self.train_ids

    def predict(self, file):
        self.test_group = []

        self.test_data = itertools.imap(self.split, itertools.ifilter(self.filter, Utilities.read_json(file, 'id', self.group)))
        if self.display:
            self.test_data = list(self.test_data)

        return self.regressor.predict(self.test_data)

    def output(self, predictions):
        for i in xrange(len(predictions)):
            group = self.test_group[i] if self.group != "score" else ""
            prediction = predictions[i]
            message = ""
            if self.display:
                message = "\t" + Utilities.get_colored_text(prediction, self.test_data[i]).replace('\n', ' ')
    
            g = "{}\t".format(group) if group != "" else ""
            print("{}{:.2f}{}".format(g, prediction, message))

def main(argv):
    group = argv[0] if len(argv) > 0 else "id"
    model_file = argv[1] if len(argv) > 1 else ""
    cv_folds = 0
    if model_file.isdigit():
        cv_folds = int(model_file) if model_file != '0' else 5
        model_file = ""

    algorithm_class = RandomForestRegressor
    algorithm_parameters = {
        'n_estimators': 100,
        'n_jobs': 2,
        'min_samples_split': 10
    }
    classifier = Classifier(group, model_file)
    classifier.create_model(train=not cv_folds, class_name=algorithm_class, parameters=algorithm_parameters)
    if cv_folds > 0:
        classifier.output_cross_validate(cv_folds)
    else:
        if sys.stdin.isatty():
            glob_pattern = 'commit_comments-dump.[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].json'
            files = glob('[0-9]*/' + glob_pattern) + glob(glob_pattern)
            if not files:
                print("No commit comments JSON files found, cannot classify.")
            else:
                for name in files:
                    with open(name, 'rb') as file:
                        classifier.output(classifier.predict(file))
        else:
            classifier.output(classifier.predict(sys.stdin))

if __name__ == "__main__":
    main(sys.argv[1:])
