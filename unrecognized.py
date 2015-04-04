import sys
import re
import json
import linecache
from analyze import Analyzer
from classify import Classifier
from utils import Utilities

def main(argv):
    dataset = 'commit_comments-dump.2015-01-29.json'
    group = "id"
    model_file = 'model.pickle'
    analyzer = Analyzer(group)
    classifier = Classifier(group, 10, model_file)
    classifier.create_model()

    # Perform the sentiment analysis
    unrecognized_negative = {}
    unrecognized_positive = {}
    predictions = classifier.predict()
    print('Done predictions')
    line = 0 # Dataset line
    i = 0 # Prediction ID (+1)
    file = open(dataset, 'rb')
    for data in Utilities.read_json(file, 'id', group):
        line = line + 1
        if line % 1000 == 0:
            print(line)
        if not classifier.filter(data):
            continue
        i = i + 1

        message = data["message"]
        score = analyzer.analyze(message)[0]

        if score == 0:
            continue

        diff = predictions[i-1] - score
        if abs(diff) < 1.0:
            continue

        target = unrecognized_negative if diff < 0 else unrecognized_positive
        target[line] = diff

    result = sorted(unrecognized_positive.items(), key=lambda x: x[1])
    for item in result:
        print("{}: {}: {}".format(item[0], item[1], linecache.getline(dataset, item[0])[:-1]))

if __name__ == "__main__":
    main(sys.argv[1:])
