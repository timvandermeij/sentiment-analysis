import sys
import linecache
from analyze import Analyzer
from classify import Classifier
from utils import Utilities
from sklearn.ensemble import RandomForestRegressor

def main(argv):
    # Constants for the analyzer and the classifier
    dataset = 'commit_comments-dump.2015-01-29.json'
    group = 'id'
    model_file = 'model.pickle'
    
    # Create the analyzer
    analyzer = Analyzer(group)

    # Create the classifier
    algorithm_class = RandomForestRegressor
    algorithm_parameters = {
        'n_estimators': 100,
        'n_jobs': 2,
        'min_samples_split': 10
    }
    classifier = Classifier(group, model_file)
    classifier.create_model(train=True, class_name=algorithm_class, parameters=algorithm_parameters)

    # Compare analyzer output with classifier output and identify differences
    unrecognized_negative = {}
    unrecognized_positive = {}
    predictions = classifier.predict()
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

        message = data['message']
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
