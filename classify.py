from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
import numpy as np
import json
import sys

def read_json(file):
    i = 0
    for jsonObject in file:
        data = json.loads(jsonObject)
        message = data["body"].replace('\r\n', '\n')
        yield message
        i = i + 1
        if i % 1000 == 0:
            print(i)
            return

def main(argv):
    cv = CountVectorizer(input='content')
    train_counts = cv.fit_transform(read_json(sys.stdin))
    #print(train_counts)
    tt = TfidfTransformer()
    tfidf = tt.fit_transform(train_counts)
    #print(tfidf)

if __name__ == "__main__":
    main(sys.argv[1:])
