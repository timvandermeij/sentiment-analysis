from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
import numpy as np
import json
import sys
import time
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
        #('clf', KNeighborsRegressor())
    ])
    regressor.fit(train_data, train_labels)

    for message, group in analyzer.read_json(sys.stdin):
        # Call predict for every message which might be slow in practice but 
        # avoids memory hog due to not being able to use iterators if done in 
        # one batch.
        prediction = regressor.predict([message])[0]
        if analyzer.display:
            # Take the color for this group of predictions
            c = cmp(prediction, 0)
            message = analyzer.colors[c] + message + analyzer.END_COLOR

        analyzer.output(group, message, prediction, "")


if __name__ == "__main__":
    main(sys.argv[1:])
