from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
import numpy as np
import sys
import itertools
import linecache
import json
import os
import pickle
from analyze import Analyzer # for some train data labelling
from utils import Utilities

class Classifier(object):
    def __init__(self, group, n_estimators, model_file):
        self.dataset_name = "commit_comments-dump.2015-01-29"
        self.group = group
        self.model_file = model_file
        self.n_estimators = n_estimators
        self.train_ids = set()
        self.analyzer = Analyzer(group)

    def create_model(self):
        trained = False
        if self.model_file != "" and os.path.isfile(self.model_file):
            with open(self.model_file, 'rb') as f:
                model = pickle.load(f)
                trained = True
        else:
            model = RandomForestRegressor(n_estimators=self.n_estimators, n_jobs=-1)

        self.regressor = Pipeline([
            ('tfidf', TfidfVectorizer(input='content')),
            ('clf', model)
        ])

        if not trained:
            self.train()
            if self.model_file != "":
                with open(self.model_file, 'wb') as f:
                    pickle.dump(model, f)

    def train(self):
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

        # Train the regressor
        self.regressor.fit(train_data, train_labels)

    def split(self, data):
        if self.group != "score":
            self.test_group.append(data['group'])
        return data['message']

    def filter(self, data):
        return data['id'] not in self.train_ids

    def predict(self):
        self.test_group = []

        self.test_data = itertools.imap(self.split, itertools.ifilter(self.filter, Utilities.read_json(sys.stdin, 'id', self.group)))
        if self.analyzer.display:
            self.test_data = list(self.test_data)

        return self.regressor.predict(self.test_data)

    def output(self, predictions):
        for i in xrange(len(predictions)):
            prediction = predictions[i]
            message = ""
            group = self.test_group[i] if self.group != "score" else ""
            if self.analyzer.display:
                message = Utilities.get_colored_text(prediction, self.test_data[i])
            
            self.analyzer.output(group, message, prediction, "")

def main(argv):
    group = argv[0] if len(argv) > 0 else "id"
    n_estimators = int(argv[1]) if len(argv) > 1 else 1000
    model_file = argv[2] if len(argv) > 2 else ""
    
    classifier = Classifier(group, n_estimators, model_file)
    classifier.create_model()
    classifier.output(classifier.predict())

if __name__ == "__main__":
    main(sys.argv[1:])
