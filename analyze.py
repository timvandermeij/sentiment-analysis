import sys
import re
import json

class Analyzer(object):
    def __init__(self, group):
        self.group = group
        self.display = (self.group == "id")

        # Load the positive and negative words
        self.words = {}
        self.colors = {1: '\033[1;32m', -1: '\033[1;31m', 0: '\033[1m', 'head': '\033[1;36m', 'end': '\033[0m'}
        with open("words/positive.txt") as file:
            for line in file:
                self.words[line.rstrip()] = 1
        with open("words/negative.txt") as file:
            for line in file:
                self.words[line.rstrip()] = -1

    def read_json(self, file, keep_fields=True):
        i = 0
        for jsonObject in file:
            data = json.loads(jsonObject)
            # Normalize newlines
            if "body" in data:
                data["body"] = data["body"].replace('\r\n', '\n')

            if type(keep_fields) == list:
                keep_fields = dict([(k,k) for k in keep_fields])
            elif type(keep_fields) != dict:
                k = {"message": "body"}
                if type(keep_fields) == str:
                    k[keep_fields] = keep_fields
                if self.group != "score":
                    k["group"] = self.group

                keep_fields = k

            fields = {}
            # Rename the fields and filter
            for new,old in keep_fields.iteritems():
                fields[new] = data[old]

            yield fields
            i = i + 1

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
                    disp += self.colors[self.words[w]] + w + self.colors['end'] + " "

        label = score / float(found) if found != 0 else 0.0
        return (label, disp)

    def output(self, group, message, label, disp):
        g = "{}\t".format(group) if self.group != "score" else ""

        text = ""
        if self.display:
            text = "\t{}{}".format(disp, message.replace('\n',' '))

        print("{}{:.2f}{}".format(g, label, text))

def main(argv):
    group = argv[0] if len(argv) > 0 else "id"
    analyzer = Analyzer(group)
    for data in analyzer.read_json(sys.stdin):
        (label, disp) = analyzer.analyze(data["message"])
        analyzer.output(data["group"], data["message"], label, disp)

if __name__ == "__main__":
    main(sys.argv[1:])
