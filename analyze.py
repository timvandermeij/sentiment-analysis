import sys
import re
import json

class Analyzer(object):
    END_COLOR = '\033[0m'

    def __init__(self, group):
        self.group = group
        self.display = self.group == "id"
        # Load the positive and negative words
        self.words = {}
        self.colors = {1: '\033[92m', -1: '\033[91m', 0: ''}
        with open("words/positive.txt") as file:
            for line in file:
                self.words[line.rstrip()] = 1

        with open("words/negative.txt") as file:
            for line in file:
                self.words[line.rstrip()] = -1

    def read_json(self, file, max=None):
        i = 0
        for jsonObject in file:
            data = json.loads(jsonObject)
            # Normalize newlines
            message = data["body"].replace('\r\n', '\n')
            del data["body"]
            group = str(data[self.group]) if self.group != "score" else ""
            yield message, group
            i = i + 1
            if max is not None and i >= max:
                break

    def analyze(self, message):
        score = 0
        found = 0
        disp = ""
        # Only keep alphanumeric and some punctuation characters
        # Keep emoticons together but beware of edge cases that should be split
        parts = filter(lambda x: x != '' and x is not None, re.split(r'"|(?:(?<=[a-z])[;\.])?\s+|(?:(?<=[a-z])[;\.])?$|(?!.[/(]\S)([^;\.\-\"\'+\w\s][^+\w\s]*(?:[-a-z]\b)?)|(?!.[/(]\S)((?:\b[a-z])?[^+\w\s]*[^;\.\-\"\'+\w\s])', message.lower()))
        for w in parts:
            if w in self.words:
                score += self.words[w]
                found += 1
                if self.display:
                    disp += self.colors[self.words[w]] + w + self.END_COLOR + " "

        label = score / float(found) if found != 0 else 0.0
        return (label, score, found, disp)

    def output(self, group, message, label, disp):
        g = group + "\t" if self.group != "score" else ""

        text = ""
        if self.display:
            text = "\t{}{}".format(disp, message.replace('\n',' '))

        print("{}{:.2f}{}".format(g, label, text))

def main(argv):
    group = argv[0] if len(argv) > 0 else "id"

    # Perform the sentiment analysis
    analyzer = Analyzer(group)
    for message, data in analyzer.read_json(sys.stdin):
        (label, score, found, disp) = analyzer.analyze(message)

        analyzer.output(data, message, label, disp)

if __name__ == "__main__":
    main(sys.argv[1:])
