import sys
import urllib2
from BeautifulSoup import BeautifulSoup
import os.path
import tarfile
import bson
import json
import re
import shelve

# TODO: change labeler with new dataset names
# TODO: what to do with remaining repositories without a language?
# TODO: what to do with 'null' language?
class Preprocessor(object):
    def __init__(self):
        self.dataset = ''
        self.bson_file = ''
        self.keep_fields = []

    def preprocess(self):
        self.get_bson()
        self.convert_bson()

    def get_bson(self):
        if not os.path.isfile(self.dataset + '.tar.gz'):
            self.download(self.dataset + '.tar.gz')
        if not os.path.isfile(self.bson_file + '.bson'):
            self.extract(self.bson_file + '.bson')

    def download(self, target):
        stream = urllib2.urlopen('http://ghtorrent.org/downloads/' + self.dataset + '.tar.gz')
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
            status = 'Downloading "' + self.dataset + '" dataset [%3.0f%%]' % (downloaded_size * 100. / file_size)
            status += chr(8) * (len(status) + 1)
            print(status),

        print('Downloading "' + self.dataset + '" dataset [finished]')
        file.close()

    def extract(self, file):
        tar = tarfile.open(self.dataset + '.tar.gz')
        tar.extractall()
        tar.close()
        print('Untarring "' + self.dataset + '" dataset [finished]')

    def convert_bson(self):
        raise NotImplementedError("Cannot call convert_bson on the base class: a subclass must implement this method instead")

class Commit_Comments_Preprocessor(Preprocessor):
    def __init__(self, group):
        super(Commit_Comments_Preprocessor, self).__init__()
        self.dataset = 'commit_comments-dump.2015-01-29'
        self.bson_file = 'dump/github/commit_comments.bson'
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
        output = open(self.dataset + '.json', 'wb')
        bson_file = open(self.bson_file, 'rb')
        
        if os.path.isfile('languages.shelf'):
            languages = shelve.open('languages.shelf')
        else:
            languages = {}
        failed = 0
        total = 0
        # Read every BSON object as an iterator to save memory.
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
            else:
                failed += 1
            total += 1
            json.dump(preprocessed_json, output)
            output.write('\n')

        print(str(failed) + ' failed from ' + str(total) + ' in total')
        output.close()
        bson_file.close()
        os.remove(self.bson_file)
        os.removedirs('dump/github')
        print('Converting BSON to JSON and removing unused fields [finished]')

class Repos_Preprocessor(Preprocessor):
    def __init__(self, date):
        super(Repos_Preprocessor, self).__init__()
        self.dataset = 'repos-dump.' + date
        self.bson_file = 'dump/github/repos.bson'

    def convert_bson(self):
        bson_file = open(self.bson_file, 'rb')
        
        # Read every BSON object as an iterator to save memory.
        languages = shelve.open('languages.shelf')
        for raw_json in bson.decode_file_iter(bson_file):
            repository = raw_json['full_name'].encode('utf-8')
            language = raw_json['language'].encode('utf-8') if raw_json['language'] is not None else ''
            if repository not in languages:
                languages[repository] = language

        languages.close()
        bson_file.close()
        os.remove(self.bson_file)
        os.removedirs('dump/github')
        print('Converting BSON to shelf and removing unused fields [finished]')

def main(argv):
    group = argv[0] if len(argv) > 0 else "id"

    if group == "language":
        # First prepare the languages as the commit comments dataset depends on 
        # that.
        # Fetch all the repos dumps.
        preprocessors = []
        downloads_page = "http://ghtorrent.org/downloads/"
        html_page = urllib2.urlopen(downloads_page)
        soup = BeautifulSoup(html_page)
        for link in soup.findAll('a'):
            href = link.get('href')
            if href.startswith('repos-dump'):
                date = href[11:-7]
                preprocessors[:0] = [Repos_Preprocessor(date)]

        for preprocessor in preprocessors:
            preprocessor.preprocess()

    commit_comments = Commit_Comments_Preprocessor(group)
    commit_comments.preprocess()

if __name__ == "__main__":
    main(sys.argv[1:])
