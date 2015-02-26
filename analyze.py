import sys
import re
import urllib2
import os.path
import tarfile

DATASET_NAME = "commit_comments"
DATASET_URL = "http://ghtorrent.org/downloads/" + DATASET_NAME + "-dump.2015-01-29.tar.gz"

def download(url, target):
    stream = urllib2.urlopen(url)
    file = open(target, 'wb')
    fileSize = int(stream.info().getheaders("Content-Length")[0])
    downloadedSize = 0
    blockSize = 8192
    
    while True:
        buffer = stream.read(blockSize)
        if not buffer:
            break

        downloadedSize += len(buffer)
        file.write(buffer)
        status = "-> Downloading commit messages dataset (%3.2f%%)" % (downloadedSize * 100. / fileSize)
        status += chr(8) * (len(status) + 1)
        print(status),

    print("-> Downloading commit messages dataset (finished)")
    file.close()

def extract(tarball, file):
    tar = tarfile.open(tarball + ".tar.gz")
    member = tar.getmember(file)
    member.name = os.path.basename(member.name)
    tar.extract(member)
    tar.close()
    print(" -> Untarring commit messages dataset (finished)")
 
def main(argv):
    # Message to perform sentiment analysis on
    message = argv[0] if len(argv) > 0 else ""

    if message == "":
        print("Usage: python analyze.py [message]")
        sys.exit(1)

    # Download the dataset if it does not exist yet
    if not os.path.isfile(DATASET_NAME + ".bson"):
        download(DATASET_URL, DATASET_NAME + ".tar.gz")
        extract(DATASET_NAME, "dump/github/" + DATASET_NAME + ".bson")
        os.remove(DATASET_NAME + ".tar.gz")

    # Load the positive and negative words
    words = {}
    with open("words/positive.txt") as file:
        for line in file:
            words[line.rstrip()] = 1

    with open("words/negative.txt") as file:
        for line in file:
            words[line.rstrip()] = -1

    # Perform the sentiment analysis
    score = 0
    found = 0
    for w in message.split():
        w = re.sub(r'\W+', '', w).lower() # Only keep alphanumeric characters
        if w in words:
            score += words[w]
            found += 1

    if found == 0:
        print(0)
    else:
        print(round(score / float(found), 2))

if __name__ == "__main__":
    main(sys.argv[1:])
