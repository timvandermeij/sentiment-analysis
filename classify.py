from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
import numpy as np
import sys
import itertools
from analyze import Analyzer # for some train data labelling

class Classifier(object):
    def __init__(self, group, train_size):
        self.group = group
        self.train_size = train_size
        self.analyzer = Analyzer(group)

    def train(self):
        # Collect the training data
        train_data = []
        train_labels = []
        for message, _ in self.analyzer.read_json(sys.stdin):
            label = self.analyzer.analyze(message)[0]
            train_data.append(message)
            train_labels.append(label)

            if len(train_data) >= self.train_size:
                break

        # Train the regressor
        self.regressor = Pipeline([
            ('tfidf', TfidfVectorizer(input='content')),
            ('clf', RandomForestRegressor())
        ])
        self.regressor.fit(train_data, train_labels)

    def predict(self):
        self.test_group = []
        def track(x):
            if self.analyzer.group != "score":
                self.test_group.append(x[1])
            return x[0]

        self.test_data = itertools.imap(track, self.analyzer.read_json(sys.stdin))
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
