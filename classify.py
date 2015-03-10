from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
import numpy as np
import json
import sys
import time
from analyze import Analyzer # for some train data labelling

class FilterIterator:
    def __init__(self, I, do_output=False):
        self.current = 0
        self.input = I
        self.do_output = do_output
        self.output = []

    def __iter__(self):
        return self
    
    def next(self):
        (message, data) = self.input.next()
        self.current = self.current + 1
        #if self.current > 3000:
        #    print(message,data)
        #    raise(StopIteration)
        if self.do_output:
            self.output.append(data)

        return message

def main(argv):
    group = argv[0] if len(argv) > 0 else "id"
    train_size = int(argv[1]) if len(argv) > 1 else 1000

    train_data = []
    train_labels = []
    analyzer = Analyzer(group)
    for message, _ in analyzer.read_json(sys.stdin):
        label = analyzer.analyze(message)[0]
        train_data.append(message)
        train_labels.append(label)

        if len(train_data) >= train_size:
            break

    regressor = Pipeline([
        ('tfidf', TfidfVectorizer(input='content')),
        #('clf', RandomForestRegressor())
        ('clf', KNeighborsRegressor())
    ])
    regressor.fit(train_data, train_labels)

    test = analyzer.read_json(sys.stdin)#, 2000)
    it = FilterIterator(test, do_output=analyzer.group != "score")
    predicted = regressor.predict(it)

    test_set = it.output
    print(len(predicted), len(test_set))
    return
    #print(test_set)

    for i in range(len(predicted)):
        message = ""
        if analyzer.display:
            # Take the color for this group of predictions
            c = cmp(predicted[i], 0)
            message = analyzer.colors[c] + test_set[i]["body"].replace('\r\n', '\n') + analyzer.END_COLOR

        analyzer.output(test_set[i], message, predicted[i], "")


if __name__ == "__main__":
    main(sys.argv[1:])
