import sys
import re
import json

def main(argv):
    # Load the positive and negative words
    words = {}
    with open("words/positive.txt") as file:
        for line in file:
            words[line.rstrip()] = 1

    with open("words/negative.txt") as file:
        for line in file:
            words[line.rstrip()] = -1

    # Perform the sentiment analysis
    for jsonObject in sys.stdin:
        data = json.loads(jsonObject)
        message = data["body"]
        score = 0
        found = 0
        for w in message.split():
            # Only keep alphanumeric and some punctuation characters
            w = re.sub(r'[^\-\'+\w]', '', w).lower()
            if w in words:
                score += words[w]
                found += 1

        print("{}\t{:.2f}".format(data["id"], score / float(found) if found != 0 else 0.0))

if __name__ == "__main__":
    main(sys.argv[1:])
