import sys
import urllib2
from BeautifulSoup import BeautifulSoup
import os.path
import tarfile
import bson
import json
from glob import glob
import re
import shelve
from mpi4py import MPI
from array import array
import time

class Progress(object):
    def __init__(self, message, total_size):
        self.message = message
        self.total_size = total_size
        self.previous_percent = -1

    def show_progress(self, current_size):
        percent = int(current_size * 100. / self.total_size)
        if percent != self.previous_percent:
            self.print_progress('{:3d}%'.format(percent))
            self.previous_percent = percent

    def print_progress(self, text):
        status = '{} [{}]'.format(self.message, text)
        if MPI.COMM_WORLD.size > 1:
            status = '#{}. {}\n'.format(MPI.COMM_WORLD.rank, status)
        else:
            # Clear previous message and progress
            clear = chr(8) * (len(self.message) + 7)
            if self.previous_percent != -1:
                sys.stdout.write(clear)

        sys.stdout.write(status)
        sys.stdout.flush()

    def finish(self):
        self.print_progress("finished")
        sys.stdout.write('\n')

class ProgressFile(file, Progress):
    def __init__(self, *a, **kw):
        message = kw.pop('message', None)

        file.__init__(self, *a, **kw)

        if message is None:
            message = 'Reading file {}'.format(self.name)

        Progress.__init__(self, message, os.path.getsize(self.name))

    def read(self, size):
        self.show_progress(self.tell())
        return file.read(self, size)

    def close(self):
        if not self.closed:
            self.finish()
        file.close(self)

class Preprocessor(object):
    DOWNLOADS_URL = "http://ghtorrent.org/downloads/"
    BSON_FILE_DIR = "dump/github/"

    def __init__(self, process_id):
        self.dataset = ''
        self.bson_file = ''
        self.keep_fields = []
        self.process_id = str(process_id) if process_id != None else None

    def preprocess(self):
        self.get_bson()
        self.convert_bson()

    def get_bson(self):
        if not os.path.isfile(self.dataset + '.tar.gz'):
            self.download(self.dataset + '.tar.gz')
        if not os.path.isfile(self.bson_file + '.bson'):
            self.extract()

    def download(self, target):
        stream = urllib2.urlopen(self.DOWNLOADS_URL + self.dataset + '.tar.gz')
        file = open(target, 'wb')
        file_size = int(stream.info().getheaders('Content-Length')[0])
        downloaded_size = 0
        block_size = 8192
        message = 'Downloading "{}" dataset'.format(self.dataset)
        progress = Progress(message, file_size)

        while True:
            buffer = stream.read(block_size)
            if not buffer:
                break

            downloaded_size += len(buffer)
            file.write(buffer)
            progress.show_progress(downloaded_size)

        progress.finish()
        file.close()

    def extract(self):
        message = 'Untarring "{}" dataset'.format(self.dataset)
        file = ProgressFile(self.dataset + '.tar.gz', message=message)
        tar = tarfile.open(fileobj=file)
        if self.process_id != None:
            tar.extractall(self.process_id)
        else:
            tar.extractall()
        tar.close()
        file.close()

    def convert_bson(self):
        raise NotImplementedError("Cannot call convert_bson on the base class: a subclass must implement this method instead")

class Commit_Comments_Preprocessor(Preprocessor):
    def __init__(self, group):
        super(Commit_Comments_Preprocessor, self).__init__(None)
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

    def merge_shelves(self):
        files = sorted(glob('languages-*.shelf'))
        count = len(files)
        message = 'Merging partial shelves'
        progress = Progress(message, count)

        merged = shelve.open('languages.shelf')
        for index in range(count):
            progress.show_progress(index)
            shelf = shelve.open(files[index])
            merged.update(shelf)
            shelf.close()
            os.remove(files[index])
        merged.close()
        progress.finish()

    def convert_bson(self):
        output = open(self.dataset + '.json', 'wb')
        message = 'Converting BSON and removing unused fields'
        bson_file = ProgressFile(self.bson_file, 'rb', message=message)
        
        if os.path.isfile('languages-1.shelf'):
            # We have at least one partial shelve waiting to be merged.
            self.merge_shelves()
        
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

class Repos_Preprocessor(Preprocessor):
    def __init__(self, process_id, date):
        super(Repos_Preprocessor, self).__init__(process_id)
        self.dataset = 'repos-dump.' + date
        self.bson_file = self.process_id + '/' + self.BSON_FILE_DIR + 'repos.bson'

    def convert_bson(self):
        message = 'Converting BSON and removing unused fields'
        bson_file = ProgressFile(self.bson_file, 'rb', message=message)
        
        # Read every BSON object as an iterator to save memory.
        languages = shelve.open('languages-' + self.process_id + '.shelf', writeback=True)
        for raw_json in bson.decode_file_iter(bson_file):
            repository = raw_json['full_name'].encode('utf-8')
            language = raw_json['language'].encode('utf-8') if raw_json['language'] is not None else ''
            if repository not in languages:
                languages[repository] = language

        languages.close()
        bson_file.close()
        os.remove(self.bson_file)
        os.removedirs(self.process_id + '/' + self.BSON_FILE_DIR)

def get_downloads(prefix):
    dates = []
    html_page = urllib2.urlopen(Preprocessor.DOWNLOADS_URL)
    soup = BeautifulSoup(html_page)
    for link in soup.findAll('a'):
        href = link.get('href')
        if href.startswith(prefix):
            date = href[len(prefix)+1:-7]
            dates.append(date)

    return dates

def main(argv):
    task = argv[0] if len(argv) > 0 else "commit_comments"
    group = argv[1] if len(argv) > 1 else "id"

    # Buffers of MPI
    date = ""
    ready = array('c', '\0')

    if task == "repos":
        if group == "language" and not os.path.isfile('languages.shelf'):
            comm = MPI.COMM_WORLD
            num_processes = comm.size

            process_id = comm.rank
            if process_id == 0:
                # Fetch the repo dumps from the GHTorrent website and
                # process them in parallel if possible.
                dates = get_downloads('repos-dump')

                if num_processes == 1:
                    # Perform sequentially
                    for tag in range(len(dates)):
                        preprocessor = Repos_Preprocessor(tag, dates[tag])
                        preprocessor.preprocess()
                else:
                    # Automatically balance the jobs across the processes by 
                    # sending jobs to processes that tell us they are free.
                    # We run another cycle through all the other processes to 
                    # let them know they are done.
                    tag = 0
                    num_jobs = len(dates)
                    while tag < num_jobs + num_processes - 1:
                        # Wait for processes to be ready. We poll a receive of 
                        # a message from any process. In order to reduce CPU 
                        # usage of the idle master, we use our own sleep loop.
                        status = MPI.Status()
                        req = comm.Irecv(ready, source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG)
                        while not req.Test(status=status):
                            time.sleep(1)

                        # Finish the request
                        req.Wait()
                        if ready.tostring() == '\1':
                            process = status.Get_source()

                            if tag < num_jobs:
                                # A process is ready to receive, so send a job
                                print('MASTER: Process {} receives job {}'.format(process, tag))
                                comm.send(dates[tag], dest=process, tag=tag)
                            else:
                                # We are done sending jobs, so tell the process 
                                # that it is done
                                print('MASTER: Process {} is done'.format(process))
                                comm.send("", dest=process, tag=tag)

                            tag = tag + 1
            else:
                # Process repo dumps as jobs that we receive from the master.
                # Keep on running until the master lets us know we are done.
                while True:
                    # Let the master know that this process is ready
                    comm.Isend(array('c', '\1'), dest=0, tag=process_id)

                    # Execute only the preprocessor for this particular job
                    # if it received the signal to run.
                    status = MPI.Status()
                    date = comm.recv(source=0, tag=MPI.ANY_TAG, status=status)
                    tag = status.Get_tag()
                    if date == "":
                        print('PROCESS {}: Done'.format(process_id))
                        break

                    print('PROCESS {}: Received job {} with date {} for preprocessing'.format(process_id, tag, date))
                    preprocessor = Repos_Preprocessor(tag, date)
                    preprocessor.preprocess()
    elif task == "commit_comments":
        commit_comments = Commit_Comments_Preprocessor(group)
        commit_comments.preprocess()
    else:
        print("Unrecognized value for 'task': '{}'".format(task))
        print("Must be either 'repos' or 'commit_comments'")
        print("Usage: [mpiexec -n <num_processes>] python preprocess.py <task> [group]")

if __name__ == "__main__":
    main(sys.argv[1:])
