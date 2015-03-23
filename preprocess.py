import sys
import urllib2
import os.path
import tarfile
import bson
import json
import re
import gzip

class Preprocessor(object):
    def __init__(self):
        self.name = ''
        self.url = ''
        self.keep_fields = []

    def preprocess(self):
        # No need to do anything when the JSON file already exists
        if os.path.isfile(self.name + '.json'):
            return

        self.get_bson()
        self.bson_to_json()

    def get_bson(self):
        if not os.path.isfile(self.name + '.tar.gz'):
            self.download(self.name + '.tar.gz')
        if not os.path.isfile(self.name + '.bson'):
            self.extract('dump/github/' + self.name + '.bson')

    def download(self, target):
        stream = urllib2.urlopen(self.url)
        file = open(target, 'wb')
        file_size = int(stream.info().getheaders('Content-Length')[0])
        downloaded_size = 0
        block_size = 8192
        
        while True:
            buffer = stream.read(block_size)
            if not buffer:
                break

            downloaded_size += len(buffer)
            file.write(buffer)
            status = 'Downloading "' + self.name + '" dataset [%3.0f%%]' % (downloaded_size * 100. / file_size)
            status += chr(8) * (len(status) + 1)
            print(status),

        print('Downloading "' + self.name + '" dataset [finished]')
        file.close()

    def extract(self, file):
        tar = tarfile.open(self.name + '.tar.gz')
        member = tar.getmember(file)
        member.name = os.path.basename(member.name)
        tar.extract(member)
        tar.close()
        print('Untarring "' + self.name + '" dataset [finished]')

    def bson_to_json(self):
        raise NotImplementedError("Cannot call bson_to_json on the base class: a subclass must implement this method instead")

class Commit_Comments_Preprocessor(Preprocessor):
    def __init__(self, group):
        super(Commit_Comments_Preprocessor, self).__init__()
        self.name = 'commit_comments'
        self.url = 'http://ghtorrent.org/downloads/' + self.name + '-dump.2015-01-29.tar.gz'
        self.group = group
        self.keep_fields = ['id', 'body']
        if group not in self.keep_fields:
            self.keep_fields.append(group)

    def is_latin(self, string):
        try:
            string.encode('ascii')
        except UnicodeEncodeError:
            return False
        
        return True

    def bson_to_json(self):
        output = open(self.name + '.json', 'wb')
        bson_file = open(self.name + '.bson', 'rb')
        
        # Read every BSON object as an iterator to save memory.
        for raw_json in bson.decode_file_iter(bson_file):
            if not self.is_latin(raw_json['body']):
                continue

            preprocessed_json = {}
            for item in self.keep_fields:
                preprocessed_json[item] = raw_json[item]
            json.dump(preprocessed_json, output)
            output.write('\n')

        output.close()
        bson_file.close()
        os.remove(self.name + '.bson')
        print('Converting BSON to JSON and removing unused fields [finished]')

class Repos_Preprocessor(Preprocessor):
    def __init__(self):
        super(Repos_Preprocessor, self).__init__()
        self.name = 'repos'
        self.url = 'http://ghtorrent.org/downloads/' + self.name + '-dump.2015-01-29.tar.gz'
        self.keep_fields = ['full_name', 'language']

    def bson_to_json(self):
        output = open(self.name + '.json', 'wb')
        bson_file = open(self.name + '.bson', 'rb')
        
        # Read every BSON object as an iterator to save memory.
        for raw_json in bson.decode_file_iter(bson_file):
            preprocessed_json = {}
            for item in self.keep_fields:
                preprocessed_json[item] = raw_json[item]
            json.dump(preprocessed_json, output)
            output.write('\n')

        output.close()
        bson_file.close()
        os.remove(self.name + '.bson')
        print('Converting BSON to JSON and removing unused fields [finished]')

def main(argv):
    group = argv[0] if len(argv) > 0 else "id"

    commit_comments = Commit_Comments_Preprocessor(group)
    commit_comments.preprocess()

    repos = Repos_Preprocessor()
    repos.preprocess()

if __name__ == "__main__":
    main(sys.argv[1:])
