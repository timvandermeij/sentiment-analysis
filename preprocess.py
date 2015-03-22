import sys
import urllib2
import os.path
import tarfile
import bson
import json
import re
import gzip
import tokenize
import shelve

class Preprocessor(object):
    def __init__(self, group):
        self.group = group
        self.languages = {}
        self.keep_fields = ['id', 'body']
        if group not in self.keep_fields:
            self.keep_fields.append(group)

    def get_repo(self, url):
        return str(re.search(r"repos/([^/]+/[^/]+)(/|$)", url).group(1))

    def get_mysql_dataset(self, url, name, store_file):
        if os.path.isfile(store_file):
            self.languages = shelve.open(store_file)
            print('Opened existing language store.')
        else:
            if not os.path.isfile(name):
                self.download(url, name)

            self.languages = shelve.open(store_file)
            self.get_project_langs(name)

    def get_project_langs(self, mysql_file):
        done = False
        l = 0
        state = 0
        with gzip.open(mysql_file, 'rb') as f:
            for token in tokenize.generate_tokens(f.readline):
                if state == 0 and token[1] != "INSERT":
                    if l > 0:
                        print('Done processing relevant MySQL lines.')
                        break

                    print('Skipping irrelevant line')
                    state = -1
                if state == 3:
                    if token[1] == "projects":
                        l = l + 1
                        if l % 10 == 0:
                            print('Processing line {}'.format(l))
                    else:
                        print('Skipping irrelevant line')
                        state = -1

                if token[1] == '\n':
                    state = 0
                    continue
                if state == -1:
                    continue

                if state >= 9 and (state - 9) % 22 == 0:
                    url = token[1][1:-1]
                    project = self.get_repo(url)
                elif state >= 17 and (state - 17) % 22 == 0:
                    language = token[1][1:-1]
                    self.languages[project] = str(language)

                state = state + 1
    
    def get_bson_dataset(self, url, name):
        if not os.path.isfile(name + '.tar.gz'):
            self.download(url, name + '.tar.gz')
        if not os.path.isfile(name + '.bson'):
            self.extract(name, 'dump/github/' + name + '.bson')

    def download(self, url, target):
        stream = urllib2.urlopen(url)
        file = open(target, 'wb')
        file_size = int(stream.info().getheaders('Content-Length')[0])
        downloaded_size = 0
        block_size = 8192
        
        print('Downloading to {}'.format(target))
        while True:
            buffer = stream.read(block_size)
            if not buffer:
                break

            downloaded_size += len(buffer)
            file.write(buffer)
            status = 'Downloading dataset [%3.0f%%]' % (downloaded_size * 100. / file_size)
            status += chr(8) * (len(status) + 1)
            print(status),

        print('Downloading dataset [finished]')
        file.close()

    def extract(self, tarball, file):
        tar = tarfile.open(tarball + '.tar.gz')
        member = tar.getmember(file)
        member.name = os.path.basename(member.name)
        tar.extract(member)
        tar.close()
        print('Untarring dataset [finished]')

    def is_latin(self, string):
        try:
            string.encode('ascii')
        except UnicodeEncodeError:
            return False
        
        return True

    def bson_to_json(self, file):
        output = open(file + '.json', 'wb')
        bson_file = open(file + '.bson', 'rb')
        
        # Read every BSON object as an iterator to save memory.
        for raw_json in bson.decode_file_iter(bson_file):
            if not self.is_latin(raw_json['body']):
                continue

            raw_json['repo'] = self.get_repo(raw_json['url'])
            if raw_json['repo'] in self.languages:
                raw_json['lang'] = self.languages[raw_json['repo']]
            else:
                raw_json['lang'] = ''

            preprocessed_json = {}
            for item in self.keep_fields:
                preprocessed_json[item] = raw_json[item]
            json.dump(preprocessed_json, output)
            output.write('\n')

        output.close()
        bson_file.close()
        print('Converting BSON to JSON and removing unused fields [finished]')

def main(argv):
    group = argv[0] if len(argv) > 0 else "id"
    mysql_file = argv[1] if len(argv) > 1 else "projects.sql.gz"

    dataset_name = 'commit_comments'
    dataset_url = 'http://ghtorrent.org/downloads/' + dataset_name + '-dump.2015-01-29.tar.gz'
    mysql_url = 'http://ghtorrent.org/downloads/mysql-2015-01-04.sql.gz'
    store_file = 'languages.shelf'

    preprocessor = Preprocessor(group)
    preprocessor.get_bson_dataset(dataset_url, dataset_name)

    if group == 'lang':
        preprocessor.get_mysql_dataset(mysql_url, mysql_file, store_file)

    preprocessor.bson_to_json(dataset_name)
    os.remove(dataset_name + '.bson')

if __name__ == "__main__":
    main(sys.argv[1:])
