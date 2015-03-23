import sys
import urllib2
import os.path
import tarfile
import bson
import json
import re
import gzip
import shelve

class Preprocessor(object):
    def __init__(self):
        self.name = ''
        self.url = ''
        self.keep_fields = []
        self.output = ''

    def preprocess(self):
        # No need to do anything when the output file already exists
        if os.path.isfile(self.output):
            return

        self.get_bson()
        self.convert_bson()

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

    def convert_bson(self):
        raise NotImplementedError("Cannot call convert_bson on the base class: a subclass must implement this method instead")

class Commit_Comments_Preprocessor(Preprocessor):
    def __init__(self, group):
        super(Commit_Comments_Preprocessor, self).__init__()
        self.name = 'commit_comments'
        self.url = 'http://ghtorrent.org/downloads/' + self.name + '-dump.2015-01-29.tar.gz'
        self.output = self.name + '.json'
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

    def convert_bson(self):
        output = open(self.name + '.json', 'wb')
        bson_file = open(self.name + '.bson', 'rb')
        
        # Read every BSON object as an iterator to save memory.
        languages = shelve.open('languages.shelf')
        for raw_json in bson.decode_file_iter(bson_file):
            if not self.is_latin(raw_json['body']):
                continue

            preprocessed_json = {}
            for item in self.keep_fields:
                preprocessed_json[item] = raw_json[item]
            repository = str(re.search(r"repos/([^/]+/[^/]+)(/|$)", raw_json['url']).group(1))
            preprocessed_json['language'] = ''
            if repository in languages:
                preprocessed_json['language'] = languages[repository]
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
        self.output = 'languages.shelf'

    def convert_bson(self):
        bson_file = open(self.name + '.bson', 'rb')
        
        # Read every BSON object as an iterator to save memory.
        languages = shelve.open(self.output)
        for raw_json in bson.decode_file_iter(bson_file):
            repository = raw_json['full_name'].encode('utf-8')
            language = raw_json['language'].encode('utf-8') if raw_json['language'] is not None else ''
            languages[repository] = language

        languages.close()
        bson_file.close()
        os.remove(self.name + '.bson')
        print('Converting BSON to shelf and removing unused fields [finished]')

def main(argv):
    group = argv[0] if len(argv) > 0 else "id"

    # First prepare the languages as the commit comments dataset depends on that.
    repos = Repos_Preprocessor()
    repos.preprocess()

    commit_comments = Commit_Comments_Preprocessor(group)
    commit_comments.preprocess()

if __name__ == "__main__":
    main(sys.argv[1:])
