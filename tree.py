import sys
import pickle
from sklearn import tree
from subprocess import check_call

def main(argv):
    model_file = argv[0] if len(argv) > 0 else "model"
    with open(model_file + ".pickle", 'r') as f:
        objects = pickle.load(f)
        model = objects[1][1]
        estimator = model.estimators_[0]
        tree.export_graphviz(estimator, out_file=model_file + '.dot')
        check_call(['dot', '-Tsvg', model_file + '.dot', '-o', model_file + '.svg'])

if __name__ == "__main__":
    main(sys.argv[1:])
