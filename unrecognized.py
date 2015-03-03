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
    unrecognized_negative = {}
    unrecognized_positive = {}
    for jsonObject in sys.stdin:
        data = json.loads(jsonObject)
        # normalize newlines
        message = data["body"].replace('\r\n','\n')
        score = 0
        found = 0
        parts = message.split()
        for w in parts:
            # Only keep alphanumeric and some punctuation characters
            w = re.sub(r'[^\-\'+\w]', '', w).lower()
            if w in words:
                score += words[w]
                found += 1

        if score == 0:
            continue;

        target = unrecognized_negative if score < 0 else unrecognized_positive
        for w in parts:
            # Only keep alphanumeric and some punctuation characters
            w = re.sub(r'[^\-\'+\w]', '', w).lower()
            if w not in words:
                if w in target:
                    target[w] += 1
                else:
                    target[w] = 1

    result = sorted(unrecognized_positive.items(), key=lambda x:x[1])
    for item in result:
        print(str(item[0]) + ": " + str(item[1]))

if __name__ == "__main__":
    main(sys.argv[1:])
