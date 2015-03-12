import sys
import os
import linecache
import json
from analyze import Analyzer

class Labeler:
    def __init__(self, dataset):
        self.dataset = dataset
        self.labels = {'p': 'positive', 'n': 'negative', 't': 'neutral', 'u': 'unknown'}
        
        if not os.path.isfile(dataset + '.json'):
            print('Dataset file "' + dataset + '" not found')
            sys.exit(1)

        self.original_num_lines = sum(1 for line in open(dataset + '.json'))
        self.labeled_num_lines = 0
        if os.path.isfile(dataset + '.labeled.json'):
            self.labeled_num_lines = sum(1 for line in open(dataset + '.labeled.json'))

    def interpret(self, score):
        if score < 0:
            return 'negative'
        elif score == 0:
            return 'neutral'

        return 'positive'

    def start(self):
        analyzer = Analyzer('id')
        while self.labeled_num_lines < self.original_num_lines:
            line = self.labeled_num_lines + 1
            print('--- Labeling message ' + str(line) + ' ---')
            
            # linecache provides random access to lines in (large) text files
            raw_json = linecache.getline(self.dataset + '.json', line)
            json_object = json.loads(raw_json)
            message = json_object['body']
            label = analyzer.analyze(message)[0]
            
            print(message + '\n')
            print('Guess: ' + self.interpret(label))
            choice = raw_input('Label (Enter to confirm, otherwise "p", "n", "t" or "u"): ')
            print('\n')

            self.write(json_object, self.labels[choice] if choice is not '' else self.interpret(label))
            self.labeled_num_lines += 1

    def write(self, json_object, label):
        del json_object['body']
        json_object['label'] = label
        output = open(self.dataset + '.labeled.json', 'a')
        output.write(json.dumps(json_object) + '\n')
        output.close()

def main(argv):
    dataset = argv[0] if len(argv) > 0 else 'commit_comments'
    labeler = Labeler(dataset)
    labeler.start()

if __name__ == "__main__":
    main(sys.argv[1:])
