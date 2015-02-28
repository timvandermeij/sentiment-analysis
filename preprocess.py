import sys
import urllib2
import os.path
import tarfile
import bson
import json

DATASET_NAME = "commit_comments"
DATASET_URL = "http://ghtorrent.org/downloads/" + DATASET_NAME + "-dump.2015-01-29.tar.gz"
DATASET_KEEP_FIELDS = ["id", "body"]

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
        status = "Downloading dataset [%3.0f%%]" % (downloadedSize * 100. / fileSize)
        status += chr(8) * (len(status) + 1)
        print(status),

    print("Downloading dataset [finished]")
    file.close()

def extract(tarball, file):
    tar = tarfile.open(tarball + ".tar.gz")
    member = tar.getmember(file)
    member.name = os.path.basename(member.name)
    tar.extract(member)
    tar.close()
    print("Untarring dataset [finished]")

def isLatinAlphabet(string):
    try:
        string.encode('ascii')
    except UnicodeEncodeError:
        return False
    
    return True

def bson2json(file):
    output = open(file + ".json", "wb")
    bsonFile = open(file + ".bson", "rb")
    # Read every BSON object as an iterator to save memory.
    for rawJson in bson.decode_file_iter(bsonFile):
        # TODO: Perhaps just strip non-Latin and only ignore if nothing is left
        if not isLatinAlphabet(rawJson["body"]):
            continue

        preprocessedJson = {}
        for item in DATASET_KEEP_FIELDS:
            preprocessedJson[item] = rawJson[item]
        json.dump(preprocessedJson, output)
        output.write("\n")

    output.close()
    bsonFile.close()
    print("Converting BSON to JSON and removing unused fields [finished]")

def main(argv):
    if not os.path.isfile(DATASET_NAME + ".tar.gz"):
        download(DATASET_URL, DATASET_NAME + ".tar.gz")
    if not os.path.isfile(DATASET_NAME + ".bson"):
        extract(DATASET_NAME, "dump/github/" + DATASET_NAME + ".bson")

    bson2json(DATASET_NAME)
    os.remove(DATASET_NAME + ".bson")

if __name__ == "__main__":
    main(sys.argv[1:])
