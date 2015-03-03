import sys
import os
import json
import struct

DATASET_NAME = "commit_comments"

def create(file):
    output = open(file + ".labels", "wb")

    content = ""
    with open(file + ".json") as input:
        for line in input:
            data = json.loads(line);
            content += "{}\t{}\n".format(data["id"], "")

    output.write(content)
    output.close()
    print("Creating labels file [finished]")

def main(argv):
    if not os.path.isfile(DATASET_NAME + ".labels"):
        create(DATASET_NAME)

if __name__ == "__main__":
    main(sys.argv[1:])
