import sys
import urllib2
import os.path
import tarfile
import bson
import json
import re
import gzip
import shelve

# TODO: do not untar completely, but use directly when untarring
# TODO: cleanup name, url, file and output parameters
# TODO: cleanup main function (pass in an array of dates)
# TODO: what to do with remaining repositories without a language?
# TODO: what to do with 'null' language?
class Preprocessor(object):
    def __init__(self):
        self.name = ''
        self.url = ''
        self.file = ''
        self.keep_fields = []
        self.output = ''

    def preprocess(self):
        self.get_bson()
        self.convert_bson()

    def get_bson(self):
        if not os.path.isfile(self.name + '.tar.gz'):
            self.download(self.name + '.tar.gz')
        if not os.path.isfile(self.file + '.bson'):
            self.extract('dump/github/' + self.file + '.bson')

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
        tar.extractall()
        tar.close()
        print('Untarring "' + self.name + '" dataset [finished]')

    def convert_bson(self):
        raise NotImplementedError("Cannot call convert_bson on the base class: a subclass must implement this method instead")

class Commit_Comments_Preprocessor(Preprocessor):
    def __init__(self, group):
        super(Commit_Comments_Preprocessor, self).__init__()
        self.name = 'commit_comments'
        self.url = 'http://ghtorrent.org/downloads/' + self.name + '-dump.2015-01-29.tar.gz'
        self.file = 'dump/github/commit_comments.bson'
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
        output = open(self.output, 'wb')
        bson_file = open(self.file, 'rb')
        
        # Read every BSON object as an iterator to save memory.
        languages = shelve.open('languages.shelf')
        failed = 0
        total = 0
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
        os.remove(self.file)
        print('Converting BSON to JSON and removing unused fields [finished]')

class Repos_Preprocessor(Preprocessor):
    def __init__(self, date):
        super(Repos_Preprocessor, self).__init__()
        self.name = 'repos-dump.' + date
        self.file = 'dump/github/repos.bson'
        self.url = 'http://ghtorrent.org/downloads/' + self.name + '.tar.gz'
        self.output = 'languages.shelf'

    def convert_bson(self):
        bson_file = open(self.file, 'rb')
        
        # Read every BSON object as an iterator to save memory.
        languages = shelve.open(self.output)
        for raw_json in bson.decode_file_iter(bson_file):
            repository = raw_json['full_name'].encode('utf-8')
            language = raw_json['language'].encode('utf-8') if raw_json['language'] is not None else ''
            languages[repository] = language

        languages.close()
        bson_file.close()
        os.remove(self.file)
        print('Converting BSON to shelf and removing unused fields [finished]')

def main(argv):
    group = argv[0] if len(argv) > 0 else "id"

    # First prepare the languages as the commit comments dataset depends on that.
    if not os.path.isfile('repos-dump.2015-01-29.tar.gz'):
        repos = Repos_Preprocessor('2015-01-29')
        repos.preprocess()
    if not os.path.isfile('repos-dump.2014-11-29.tar.gz'):
        repos = Repos_Preprocessor('2014-11-29')
        repos.preprocess()
    if not os.path.isfile('repos-dump.2014-09-29.tar.gz'):
        repos = Repos_Preprocessor('2014-09-29')
        repos.preprocess()
    if not os.path.isfile('repos-dump.2014-07-29.tar.gz'):
        repos = Repos_Preprocessor('2014-07-29')
        repos.preprocess()
    if not os.path.isfile('repos-dump.2014-05-29.tar.gz'):
        repos = Repos_Preprocessor('2014-05-29')
        repos.preprocess()
    if not os.path.isfile('repos-dump.2014-03-29.tar.gz'):
        repos = Repos_Preprocessor('2014-03-29')
        repos.preprocess()
    if not os.path.isfile('repos-dump.2014-01-29.tar.gz'):
        repos = Repos_Preprocessor('2014-01-29')
        repos.preprocess()
    if not os.path.isfile('repos-dump.2013-11-29.tar.gz'):
        repos = Repos_Preprocessor('2013-11-29')
        repos.preprocess()
    if not os.path.isfile('repos-dump.2013-09-29.tar.gz'):
        repos = Repos_Preprocessor('2013-09-29')
        repos.preprocess()
    if not os.path.isfile('repos-dump.2013-07-29.tar.gz'):
        repos = Repos_Preprocessor('2013-07-29')
        repos.preprocess()
    if not os.path.isfile('repos-dump.2013-05-29.tar.gz'):
        repos = Repos_Preprocessor('2013-05-29')
        repos.preprocess()
    if not os.path.isfile('repos-dump.2013-03-29.tar.gz'):
        repos = Repos_Preprocessor('2013-03-29')
        repos.preprocess()
    if not os.path.isfile('repos-dump.2013-01-29.tar.gz'):
        repos = Repos_Preprocessor('2013-01-29')
        repos.preprocess()
    if not os.path.isfile('repos-dump.2012-11-29.tar.gz'):
        repos = Repos_Preprocessor('2012-11-29')
        repos.preprocess()
    if not os.path.isfile('repos-dump.2012-09-29.tar.gz'):
        repos = Repos_Preprocessor('2012-09-29')
        repos.preprocess()
    if not os.path.isfile('repos-dump.2012-07-30.tar.gz'):
        repos = Repos_Preprocessor('2012-07-30')
        repos.preprocess()

    commit_comments = Commit_Comments_Preprocessor(group)
    commit_comments.preprocess()

if __name__ == "__main__":
    main(sys.argv[1:])
