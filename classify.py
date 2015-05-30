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
import argparse
from collections import OrderedDict
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
            prediction = predictions[i]
            message = ""
            if self.display:
                message = "\t" + Utilities.get_colored_text(prediction, self.test_data[i]).replace('\n', ' ')
    
            g = "{}\t".format(self.test_group[i]) if self.group != "score" else ""
            print("{}{:.2f}{}".format(g, prediction, message))

class Algorithms(object):
    def __init__(self):
        self.parameters = OrderedDict()
        self.algorithms = OrderedDict()

    def add_algorithm(self, algorithm):
        self.algorithms[algorithm['class_name']] = {
            "module": algorithm['module'],
            "dense": algorithm['dense'] if 'dense' in algorithm else False,
            "parameters": algorithm['parameters'].keys()
        }

        for parameter, values in algorithm['parameters'].iteritems():
            if parameter in self.parameters:
                self.parameters[parameter]["classes"].append(algorithm['class_name'])
                self.parameters[parameter]["values"].extend(values)
            else:
                self.parameters[parameter] = {
                    "classes": [algorithm['class_name']],
                    "values": values,
                }

    def read_manifest(self):
        # Read the manifest containing algorithm descriptions for extra 
        # options. Store some algorithm data (module, dense, parameter names) 
        # as well as parameter data (classes they belong to, example values).
        with open('algorithms.json', 'r') as manifest:
            algorithms = json.load(manifest)
            for algorithm in algorithms:
                if 'disabled' in algorithm and algorithm['disabled']:
                    continue
                
                self.add_algorithm(algorithm)

                # There actually aren't any regressors in the algorithms.json, 
                # but we allow them by searching for a regressor with a similar 
                # name and assume all parameters are the same.
                if 'Classifier' in algorithm['class_name']:
                    algorithm['class_name'] = algorithm['class_name'].replace('Classifier','' if 'Ridge' in algorithm['class_name'] else 'Regressor')
                    algorithm['module'] = algorithm['module'].replace('classification','regression')
                    self.add_algorithm(algorithm)

        return self.parameters, self.algorithms

def main(argv):
    if len(argv) > 0 and not argv[0].startswith('-'):
        # Backward compatible arguments
        argv.insert(0,'--group')
        if len(argv) > 2:
            argv.insert(2,'--cv-folds' if argv[2].isdigit() else '--model')
        if len(argv) > 4:
            argv.insert(4,'--path')

    parser = argparse.ArgumentParser(description='Train a model, cross-validate or predict commit message scores')
    parser.add_argument('-g','--group', default='id', help="Group name to group on. May be one of the groups in the data set, such as 'id' or 'score'.")
    parser.add_argument('-m','--model', dest='model_file', default='', help='Model file to read a trained model from or save the model to after training.')
    parser.add_argument('-f','--cv-folds', dest='cv_folds', type=int, nargs='?', default=0, const=5, metavar='FOLDS', help='Perform cross-validation with number of folds to use.')
    parser.add_argument('-t','--only-train', dest='only_train', action='store_true', default=False, help='Stop after training the model. Ignored by --cv-folds.')
    parser.add_argument('-p','--path', default='', help='Path to read input files from.')

    # Additional algorithm parameters
    algos = Algorithms()
    parameters, algorithms = algos.read_manifest()

    parser.add_argument('--algorithm', default='RandomForestClassifier', choices=algorithms.keys(), help='Model algorithm to use for training and predictions')
    for parameter, options in parameters.iteritems():
        kw = {
            "dest": parameter,
            "help": 'Only for {} {}'.format(', '.join(options["classes"]), 'algorithm' if len(options["classes"]) == 1 else 'algorithms')
        }

        if len(options["values"]) > 0:
            kw["default"] = options["values"][0]

            if isinstance(options["values"][0],(int,float)):
                kw["type"] = type(options["values"][0])
            elif isinstance(options["values"][0],(str,unicode)):
                # Remove duplicates
                kw["choices"] = [k for k,v in itertools.groupby(options["values"])]
            elif isinstance(options["values"][0],list):
                kw["nargs"] = len(options["values"][0])
                kw["type"] = type(options["values"][0][0])

        parser.add_argument('--{}'.format(parameter.replace('_','-')), **kw)

    # Parse the arguments now that all arguments are known
    args = parser.parse_args(argv)

    # Convert chosen algorithm to classifier class and parameters
    algorithm = algorithms[args.algorithm]
    algorithm_class = Utilities.get_class(algorithm['module'], args.algorithm)

    algorithm_parameters = {}
    for parameter in algorithm['parameters']:
        algorithm_parameters[parameter] = args.__dict__[parameter]

    classifier = Classifier(args.group, args.model_file)
    classifier.create_model(train=not args.cv_folds, class_name=algorithm_class, parameters=algorithm_parameters, dense=algorithm['dense'])
    if args.cv_folds > 0:
        classifier.output_cross_validate(args.cv_folds)
    elif not args.only_train:
        if args.path != "" or sys.stdin.isatty():
            path = args.path
            if path != "" and path[-1] != "/":
                path = path + "/"

            glob_pattern = 'commit_comments-dump.[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].json'
            files = glob(path + '[0-9]*/' + glob_pattern) + glob(path + glob_pattern)
            for name in files:
                with open(name, 'rb') as file:
                    try:
                        classifier.output(classifier.predict(file))
                    except ValueError as e:
                        raise(ValueError("File '{}' is incorrect: {}".format(name, e)))
        else:
            classifier.output(classifier.predict(sys.stdin))

if __name__ == "__main__":
    main(sys.argv[1:])
