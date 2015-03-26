import sys
import urllib2
from BeautifulSoup import BeautifulSoup
import os.path
import tarfile
import bson
import json
import re
import shelve

class Progress(object):
    def __init__(self, message, total_size):
        self.message = message
        self.total_size = total_size
        self.previous_percent = -1

    def show_progress(self, current_size):
        percent = int(current_size * 100. / self.total_size)
        if percent != self.previous_percent:
            status = self.message + ' [%3d%%]' % percent
            clear = chr(8) * len(status)
            if self.previous_percent != -1:
                sys.stdout.write(clear)

            sys.stdout.write(status)
            sys.stdout.flush()
            self.previous_percent = percent
            if percent == 100:
                sys.stdout.write(clear)

class ProgressFile(file, Progress):
    def __init__(self, *a, **kw):
        message = kw.pop('message', None)

        file.__init__(self, *a, **kw)

        if message is None:
            message = 'Reading file ' + self.name

        Progress.__init__(self, message, os.path.getsize(self.name))

    def read(self, size):
        self.show_progress(self.tell())
        return file.read(self, size)

class Preprocessor(object):
    DOWNLOADS_URL = "http://ghtorrent.org/downloads/"
    BSON_FILE_DIR = "dump/github/"

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
        stream = urllib2.urlopen(self.DOWNLOADS_URL + self.dataset + '.tar.gz')
        file = open(target, 'wb')
        file_size = int(stream.info().getheaders('Content-Length')[0])
        downloaded_size = 0
        block_size = 8192
        message = 'Downloading "' + self.dataset + '" dataset'
        progress = Progress(message, file_size)

        while True:
            buffer = stream.read(block_size)
            if not buffer:
                break

            downloaded_size += len(buffer)
            file.write(buffer)
            progress.show_progress(downloaded_size)

        print(message + ' [finished]')
        file.close()

    def extract(self, file):
        message = 'Untarring "' + self.dataset + '" dataset'
        tar = tarfile.open(fileobj=ProgressFile(self.dataset + '.tar.gz', message=message))
        tar.extractall()
        tar.close()
        print(message + ' [finished]')

    def convert_bson(self):
        raise NotImplementedError("Cannot call convert_bson on the base class: a subclass must implement this method instead")

class Commit_Comments_Preprocessor(Preprocessor):
    def __init__(self, group):
        super(Commit_Comments_Preprocessor, self).__init__()
        self.dataset = 'commit_comments-dump.2015-01-29'
        self.bson_file = self.BSON_FILE_DIR + 'commit_comments.bson'
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
        message = 'Converting BSON and removing unused fields'
        bson_file = ProgressFile(self.bson_file, 'rb', message=message)
        
        if os.path.isfile('languages.shelf'):
            languages = shelve.open('languages.shelf', writeback=True)
        else:
            languages = {}
        
        # Read every BSON object as an iterator to save memory.
        for raw_json in bson.decode_file_iter(bson_file):
            if not self.is_latin(raw_json['body']):
                continue

            preprocessed_json = {}
            repository = str(re.search(r"repos/([^/]+/[^/]+)(/|$)", raw_json['url']).group(1))
            raw_json['language'] = ''
            if repository in languages:
                raw_json['language'] = languages[repository]
            for item in self.keep_fields:
                preprocessed_json[item] = raw_json[item]
           
            json.dump(preprocessed_json, output)
            output.write('\n')

        output.close()
        bson_file.close()
        os.remove(self.bson_file)
        os.removedirs(self.BSON_FILE_DIR)
        print(message + ' [finished]')

class Repos_Preprocessor(Preprocessor):
    def __init__(self, date):
        super(Repos_Preprocessor, self).__init__()
        self.dataset = 'repos-dump.' + date
        self.bson_file = self.BSON_FILE_DIR + 'repos.bson'

    def convert_bson(self):
        message = 'Converting BSON and removing unused fields'
        bson_file = ProgressFile(self.bson_file, 'rb', message=message)
        
        # Read every BSON object as an iterator to save memory.
        languages = shelve.open('languages.shelf', writeback=True)
        for raw_json in bson.decode_file_iter(bson_file):
            repository = raw_json['full_name'].encode('utf-8')
            language = raw_json['language'].encode('utf-8') if raw_json['language'] is not None else ''
            if repository not in languages:
                languages[repository] = language

        languages.close()
        bson_file.close()
        os.remove(self.bson_file)
        os.removedirs(self.BSON_FILE_DIR)
        print(message + ' [finished]')

def main(argv):
    group = argv[0] if len(argv) > 0 else "id"

    if group == "language" and not os.path.isfile('languages.shelf'):
        # First prepare the languages as the commit comments dataset depends on 
        # that. Fetch all the repo dumps.
        preprocessors = []
        html_page = urllib2.urlopen(Preprocessor.DOWNLOADS_URL)
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
