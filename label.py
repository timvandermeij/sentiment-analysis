import sys
import os
import linecache
import json
from collections import OrderedDict
from analyze import Analyzer

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
            opt = '[{}]'.format(analyzer.get_colored_text(v, k))
            options.append(v.replace(k, opt) if k in v else "{} {}".format(opt, v))
        choices = ', '.join(options)

        while self.labeled_num_lines < self.original_num_lines:
            line = self.labeled_num_lines + 1
            
            # linecache provides random access to lines in (large) text files
            raw_json = linecache.getline(self.dataset + '.json', line)
            json_object = json.loads(raw_json)
            message = json_object['body']
            (label, disp, message) = analyzer.analyze(message)
            
            print(analyzer.get_colored_text('head', '--- Labeling message {} (ID: {}) ---'.format(line, json_object['id'])))
            print(message + '\n')
            print('Guess: {}'.format(analyzer.get_colored_text(label)))
            choice = '?'
            while choice != '' and choice not in self.labels:
                choice = raw_input('Label (Enter to confirm, or {}): '.format(choices))
                if choice == 'q':
                    return

            text = self.labels[choice] if choice is not '' else analyzer.score_to_label(label)
            print('You entered: {}\n'.format(analyzer.get_colored_text(text, text)))

            self.write(json_object, text)
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
