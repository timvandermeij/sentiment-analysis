from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
import numpy as np
import sys
import itertools
import linecache
import json
from analyze import Analyzer # for some train data labelling

class Classifier(object):
    def __init__(self, group, train_size):
        self.dataset_name = "commit_comments"
        self.group = group
        self.train_size = train_size
        self.train_ids = set()
        self.analyzer = Analyzer(group)

    def train(self):
        # Collect the training data
        train_data = []
        train_labels = []
        with open(self.dataset_name + ".labeled.json", 'r') as f:
            i = 0
            for data in self.analyzer.read_json(f, ['id','label']):
                i = i + 1
                score = 0.0
                if data["label"] == "positive":
                    score = 1.0
                elif data["label"] == "negative":
                    score = -1.0
                elif data["label"] != "neutral":
                    continue

                line = linecache.getline(self.dataset_name + '.json', i)
                json_object = json.loads(line)
                if json_object['id'] != data['id']:
                    raise(ValueError('ID in label dataset does not match with dataset on line {}: {} vs {}'.format(i, data['id'], json_object['id'])))

                message = json_object['body'].replace('\r\n', '\n')
                self.train_ids.add(data['id'])
                train_data.append(message)
                train_labels.append(score)

                if len(train_data) >= self.train_size:
                    break

        # Train the regressor
        self.regressor = Pipeline([
            ('tfidf', TfidfVectorizer(input='content')),
            ('clf', RandomForestRegressor())
        ])
        self.regressor.fit(train_data, train_labels)

    def split(self, data):
        if self.analyzer.group != "score":
            self.test_group.append(data['group'])
        return data['message']

    def filter(self, data):
        return data['id'] not in self.train_ids

    def predict(self):
        self.test_group = []

        self.test_data = itertools.imap(self.split, itertools.ifilter(self.filter, self.analyzer.read_json(sys.stdin, 'id')))
        if self.analyzer.display:
            self.test_data = list(self.test_data)

        return self.regressor.predict(self.test_data)

    def output(self, predictions):
        for i in xrange(len(predictions)):
            prediction = predictions[i]
            message = ""
            group = self.test_group[i] if self.analyzer.group != "score" else ""
            if self.analyzer.display:
                # Take the color for this group of predictions
                c = cmp(prediction, 0)
                message = self.analyzer.colors[c] + self.test_data[i] + self.analyzer.colors['end']
            
            self.analyzer.output(group, message, prediction, "")

def main(argv):
    group = argv[0] if len(argv) > 0 else "id"
    train_size = int(argv[1]) if len(argv) > 1 else 1000
    
    classifier = Classifier(group, train_size)
    classifier.train()
    classifier.output(classifier.predict())

if __name__ == "__main__":
    main(sys.argv[1:])
