import sys
import re
import json

class Analyzer(object):
    END_COLOR = '\033[0m'

    def __init__(self):
        # Load the positive and negative words
        self.words = {}
        self.colors = {1: '\033[92m', -1: '\033[91m'}
        with open("words/positive.txt") as file:
            for line in file:
                self.words[line.rstrip()] = 1

        with open("words/negative.txt") as file:
            for line in file:
                self.words[line.rstrip()] = -1

    def analyze(self, message, display=False):
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
                if display:
                    disp += self.colors[self.words[w]] + w + self.END_COLOR + " "

        return (score, found, disp)

def main(argv):
    group = argv[0] if len(argv) > 0 else "id"
    display = group == "id"

    # Perform the sentiment analysis
    for jsonObject in sys.stdin:
        data = json.loads(jsonObject)
        # normalize newlines
        message = data["body"].replace('\r\n','\n')

        (score, found, disp) = analyze(message, display)

        print("{}{:.2f}{}".format(str(data[group]) + "\t" if group != "score" else "", score / float(found) if found != 0 else 0.0, "\t{}{}".format(disp, message.replace('\n',' ')) if display else ""))

if __name__ == "__main__":
    main(sys.argv[1:])
