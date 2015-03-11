from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
import numpy as np
import json
import sys
import itertools
from analyze import Analyzer # for some train data labelling

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
        ('clf', RandomForestRegressor())
    ])
    regressor.fit(train_data, train_labels)

    test_group = []
    def track(x):
        if analyzer.group != "score":
            test_group.append(x[1])
        return(x[0])

    test_data = itertools.imap(track, analyzer.read_json(sys.stdin))
    if analyzer.display:
        test_data = list(test_data)

    predictions = regressor.predict(test_data)

    for i in xrange(len(predictions)):
        # Call predict for every message which might be slow in practice but 
        # avoids memory hog due to not being able to use iterators if done in 
        # one batch.
        prediction = predictions[i]
        message = ""
        group = test_group[i] if analyzer.group != "score" else ""
        if analyzer.display:
            # Take the color for this group of predictions
            c = cmp(prediction, 0)
            message = analyzer.colors[c] + test_data[i] + analyzer.colors['end']

        analyzer.output(group, message, prediction, "")

if __name__ == "__main__":
    main(sys.argv[1:])
