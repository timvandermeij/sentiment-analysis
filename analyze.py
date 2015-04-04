import sys
import re
from utils import Utilities

class Analyzer(object):
    def __init__(self, group):
        self.group = group
        self.display = (self.group == "id")

        # Load the positive and negative words
        self.words = {}
        with open("words/positive.txt") as file:
            for line in file:
                self.words[line.rstrip()] = 1
        with open("words/negative.txt") as file:
            for line in file:
                self.words[line.rstrip()] = -1

    def split(self, message):
        # Only keep alphanumeric and some punctuation characters
        # Keep emoticons together but beware of edge cases that should be split
        return filter(lambda x: x != '' and x is not None, re.split(r'"|(?:(?<=[a-z])[;\.])?\s+|(?:(?<=[a-z])[;\.])?$|(?!.[/(]\S)([^;\.\-\"\'+\w\s][^+\w\s]*(?:[-a-z]\b)?)|(?!.[/(]\S)((?:\b[a-z])?[^+\w\s]*[^;\.\-\"\'+\w\s])', message.lower()))

    def analyze(self, message):
        score = 0
        found = 0
        disp = ""

        i = 0
        parts = self.split(message)
        for w in parts:
            if w in self.words:
                score += self.words[w]
                found += 1
                if self.display:
                    i = message.lower().find(w, i)
                    d = Utilities.get_colored_text(self.words[w], message[i:i+len(w)])
                    message = message[:i] + d + message[i+len(w):]
                    i = i + len(d)

                    disp += d + " "

        label = score / float(found) if found != 0 else 0.0
        return (label, disp, message)

    def output(self, group, message, label, disp):
        g = "{}\t".format(group) if self.group != "score" else ""

        text = ""
        if self.display:
            text = "\t{}| {}".format(disp, message.replace('\n',' '))

        print("{}{:.2f}{}".format(g, label, text))

def main(argv):
    group = argv[0] if len(argv) > 0 else "id"
    analyzer = Analyzer(group)
    for data in Utilities.read_json(sys.stdin, group=group):
        (label, disp, message) = analyzer.analyze(data["message"])
        group = data["group"] if "group" in data else ""
        analyzer.output(group, message, label, disp)

if __name__ == "__main__":
    main(sys.argv[1:])
