import sys
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
    # Download the dataset if it does not exist yet
    if not os.path.isfile(DATASET_NAME + ".bson"):
        download(DATASET_URL, DATASET_NAME + ".tar.gz")
        extract(DATASET_NAME, "dump/github/" + DATASET_NAME + ".bson")
        os.remove(DATASET_NAME + ".tar.gz")

if __name__ == "__main__":
    main(sys.argv[1:])
