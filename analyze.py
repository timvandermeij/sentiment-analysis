import sys
import re

def main(argv):
    # Message to perform sentiment analysis on
    message = argv[0] if len(argv) > 0 else ""

    if message == "":
        print("Usage: python analyze.py [message]")
        sys.exit(1)

    # Load the positive and negative words
    words = {}
    with open("words/positive.txt") as file:
        for line in file:
            line = line.replace("\r\n", "").lower()
            words[line] = 1

    with open("words/negative.txt") as file:
        for line in file:
            line = line.replace("\r\n", "").lower()
            words[line] = -1

    # Perform the sentiment analysis
    score = 0
    found = 0
    for w in message.split():
        w = re.sub(r'\W+', '', w).lower() # Only keep alphanumeric characters
        if w in words:
            score += words[w]
            found += 1

    print(round(score / float(found), 2))

if __name__ == "__main__":
    main(sys.argv[1:])
