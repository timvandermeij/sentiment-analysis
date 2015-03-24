import sys
import os
import linecache
import json
from collections import OrderedDict
from analyze import Analyzer
from utils import Utilities

class Labeler:
    def __init__(self, dataset):
        self.dataset = dataset
        self.labels = OrderedDict([
            ('p', 'positive'),
            ('n', 'negative'),
            ('t', 'neutral'),
            ('u', 'unknown')
        ])
        
        if not os.path.isfile(dataset + '.json'):
            print('Dataset file "' + dataset + '" not found')
            sys.exit(1)

        self.original_num_lines = sum(1 for line in open(dataset + '.json'))
        self.labeled_num_lines = 0
        if os.path.isfile(dataset + '.labeled.json'):
            self.labeled_num_lines = sum(1 for line in open(dataset + '.labeled.json'))

    def start(self):
        analyzer = Analyzer('id')
        options = []
        for k, v in self.labels.items():
            opt = '[{}]'.format(Utilities.get_colored_text(v, k))
            options.append(v.replace(k, opt) if k in v else "{} {}".format(opt, v))
        choices = ', '.join(options)

        while self.labeled_num_lines < self.original_num_lines:
            line = self.labeled_num_lines + 1
            
            # linecache provides random access to lines in (large) text files
            raw_json = linecache.getline(self.dataset + '.json', line)
            json_object = json.loads(raw_json)
            message = json_object['body']
            (label, disp, message) = analyzer.analyze(message)
            
            print(Utilities.get_colored_text('head', '--- Labeling message {} (ID: {}) ---'.format(line, json_object['id'])))
            print(message + '\n')
            print('Guess: {}'.format(Utilities.get_colored_text(label)))
            choice = '?'
            while choice != '' and choice not in self.labels:
                choice = raw_input('Label (Enter to confirm, or {}): '.format(choices))
                if choice == 'q':
                    return

            text = self.labels[choice] if choice is not '' else Utilities.score_to_label(label)
            print('You entered: {}\n'.format(Utilities.get_colored_text(text, text)))

            json_object['label'] = text
            Utilities.write_json(self.dataset + '.labeled.json', json_object, ["id", "label"])
            self.labeled_num_lines += 1

def main(argv):
    dataset = argv[0] if len(argv) > 0 else 'commit_comments-dump.2015-01-29'
    labeler = Labeler(dataset)
    labeler.start()

if __name__ == "__main__":
    main(sys.argv[1:])
