This repository contains all code necessary to perform sentiment analysis on a large dataset of Git commit comments
from GitHub (http://www.ghtorrent.org). The code is meant to be run on the Distributed ASCI Supercomputer 3 (DAS-3) at LIACS. It makes use of
Apache Hadoop's HDFS and MapReduce to perform the sentiment analysis. 

Prerequisites
=============

The version numbers mentioned below have been verified to work. Different versions might also work.

* Git 1.7.1 or 2.3.x
* Python 2.7.9 with libraries (see installation notes below for details)

Cloning the repository
======================

The first step is to clone the repository to obtain a local copy of the code. Open a terminal window and run the following commands.

    $ git clone https://github.com/timvandermeij/SDDM.git
    $ cd SDDM

Running the code
================

All code is written in Python. To run the simple sentiment analysis program, execute:

    $ python preprocess.py
    $ echo "Yay, sentiment analysis is working perfectly!" | python analyze.py

For the default group, running `preprocess.py` only needs to be done once. If all required data is available, `preprocess.py` will do nothing.

The output of the analysis program are lines containing scores between -1 and 1, where -1 indicates that the message is negative, 1 indicates that the
message is positive and 0 indicates that the message is neutral. The output can also contain grouping data or some visualization of the message.

Instead of using a single line as input, one can give a file to read as standard input as follows:

    $ python analyze.py < commit_comments.json
    $ python classify.py score < commit_comments.json

The latter `classify.py` script uses a (naive) classifier to predict the scores using a labeled dataset. Both programs work in a similar manner.

The output can be given to the `reducer.py` script, but only if it has been sorted on the first column of the output (the group or the score of the line).
This can be done using MapReduce as described later on. This generates a histogram of frequencies of the scores which can be passed to `plot.py` to
make a graph of the frequencies.

Groups
------

The code by default uses the `id` of a record as its group. This means that only the analyzer and classifier will do something useful. The reducer and plot scripts do not work nicely when the data is grouped this way. In order to group the classified targets with something else, pass another group, such as `score` or `language`, to all relevant scripts.

Note that for the `language` group, the preprocessor needs to retrieve more data, which can be done with `python preprocess.py repos language` and then again use `python preprocess.py commit_comments`. The first command can also be parallelized using MPI. This can be done on one machine using `mpirun -n <num_processes> python preprocess.py repos language`. The instructions for running this distributed on the DAS are given in the installation instructions there.

Running the code in MapReduce
-----------------------------

This section assumes that the installation notes below have already been followed and all dependencies and scripts are set up. The exact commands to call the MapReduce scripts, for various group parameters, are given in this section.

First of all, ensure that the data sets are on the HDFS:

    $ hdfs dfs -put commit_comments.json
    $ hdfs dfs -put commit_comments.labeled.json
    $ hdfs dfs -put words/positive.txt words/positive.txt
    $ hdfs dfs -put words/negative.txt words/negative.txt

Now, one can start a MapReduce job which classifies each record in the data set and then counts the frequency of each score as follows:

    $ pyhadoop commit_comments.json score classify.py reducer.py "score 100" score -D stream.num.map.output.key.fields=2 -files \"$HDFS_URL/words/positive.txt#words/positive.txt,$HDFS_URL/words/negative.txt#words/negative.txt\" -file commit_comments.labeled.json -file commit_comments.json -file analyze.py

For the naive analyzer, use `analyze.py` instead of `classify.py`, and the last `-file` argument can be omitted. To count frequencies of scores within a specific group, use the following:

    $ pyhadoop commit_comments.json score_lang classify.py reducer.py "lang 100" lang -D stream.num.map.output.key.fields=2 -files \"$HDFS_URL/words/positive.txt#words/positive.txt,$HDFS_URL/words/negative.txt#words/negative.txt\" -file commit_comments.labeled.json -file commit_comments.json -file analyze.py

This ensures that MapReduce knows which parts of the outputs are keys and which are values.

Installation notes for the DAS-3
================================

This section describes how to set up all dependencies for running the code on the Distributed ASCI Supercomputer 3 at LIACS. Along others, this gives instructions for Python 2.7 that can be run in virtualenv, Hadoop configuration, MPI, and libraries we depend on.

Python 2.7.9
------------

Compile `python` from source:

    $ wget https://www.python.org/ftp/python/2.7.9/Python-2.7.9.tgz
    $ tar xzvf Python-2.7.9.tgz
    $ cd Python-2.7.9
    $ ./configure --prefix=$HOME/.local
    $ make
    $ make install

Virtualenv
----------

Install `virtualenv` using `pip`:

    $ pip install --user virtualenv
    $ cd /scratch/scratch/{username} (we assume this directory from now on)
    $ ~/.local/bin/virtualenv -p $HOME/.local/bin/python2.7 python
    $ ~/.local/bin/virtualenv --relocatable python

We have now created a virtual environment called `python`. The goal is to distribute this over all the nodes using HDFS.

Shared libraries
----------------

Note that this is optional. The steps are roughly `wget http://{url}/{file}`, `tar xz {file}`, `cd {dir}/` `./configure --prefix=/scratch/scratch/{username}/opt`, `make` and `make install`.

* OpenMPI: http://www.open-mpi.org/software/ompi/v1.8/downloads/openmpi-1.8.4.tar.gz
* OpenBLAS: instead do the first part of http://stackoverflow.com/questions/11443302/compiling-numpy-with-openblas-integration/14391693#14391693
  with correct `PREFIX=...` and no `sudo` nor `ldconfig`.

Update ~/.bashrc
----------------

The final line for BLAS is optional.

    export SCRATCH="/scratch/scratch/{username}"
    PATH="$PATH:$HOME/.local/bin:/mounts/CentOS/6.6/root/usr/bin:$SCRATCH/python/bin:$SCRATCH/opt/bin"
    export LIBRARY_PATH="$HOME/.local/lib:$SCRATCH/opt/lib"
    export LD_LIBRARY_PATH="$HOME/.local/lib:$SCRATCH/opt/lib"
    export CPATH="$HOME/.local/include:$SCRATCH/opt/include"
    export PKG_CONFIG_PATH="$HOME/.local/lib/pkgconfig:$SCRATCH/opt/lib/pkgconfig"
    export BLAS="$HOME/.local/lib/libopenblas.a"

Then use `source ~/.bashrc` to reload the configuration. Note that you could do this earlier on, which might make some commands shorter and easier to use.

Python libraries
----------------

    $ source python/bin/activate

We now have a Python 2.7 virtual environment, but `pip` is still from Python 2.6. In order to fix this, run the following:

    (python)$ wget https://bootstrap.pypa.io/get-pip.py
    (python)$ python get-pip.py -U -I

This installs `pip` for Python 2.7, which is less likely to give troubles with installing or upgrading dependencies.

We use the following dependencies in this project:

    (python)$ pip install cython
    (python)$ pip install readline
    (python)$ pip install numpy
    (python)$ pip install scipy
    (python)$ pip install pandas
    (python)$ pip install scikit-learn==0.16b1
    (python)$ pip install numexpr
    (python)$ pip install matplotlib
    (python)$ pip install BeautifulSoup
    (python)$ pip install mpi4py

This is the simplest way to get all the dependencies, but you might want to use OpenBLAS. Then we need to install `numpy` from source instead, according to the following link:
http://stackoverflow.com/questions/11443302/compiling-numpy-with-openblas-integration/14391693#14391693

Note that installing `numpy` from source might mess up the latter `pip` installations since they depend on `numpy` and consider `numpy` installed this way to be incompatible, but that can be avoided by passing `--no-deps` to at least `scipy`, `pandas`, `scikit-learn` and `numexpr`.

HDFS
----

    $ tar xzvf python.tgz python/
    $ tar xzvf local.tgz $HOME/.local/*
    $ tar xzvf libs.tgz /usr/lib64/libg2c.so* /usr/lib/libgfortran.so*
    $ hdfs dfs -put python.tgz
    $ hdfs dfs -put local.tgz
    $ hdfs dfs -put libs.tgz

Update ~/.bashrc again
----------------------

    export HDFS_URL='hdfs://fs.das3.liacs.nl:8020/user/{username}'
    pyhadoop () {
        input=$1;shift;
        if [[ "x$input" = "x" ]]; then
            echo "Usage: pyhadoop <input> <output> <mapper> <reducer> [margs] [rargs] [...]"
            echo "Input and output are on HDFS, mapper and reducer are files in this directory."
            echo "Specify mapper and reducer arguments between quotes."
            echo "Rest of the parameters are used for the hadoop streaming command near start."
            return
        fi
        output=$1;shift;
        mapper=$1;shift;
        reducer=$1;shift;
        margs=$1;shift;
        rargs=$1;shift;
        echo "Arguments: input=$input output=$output mapper=\"$mapper $margs\" reducer=\"$reducer $rargs\" REST=\"$@\""
        hadoop jar /usr/lib/hadoop-mapreduce/hadoop-streaming.jar -archives "$HDFS_URL/python.tgz#python,$HDFS_URL/local.tgz#local,$HDFS_URL/libs.tgz#libs" $@ -input "$input" -output "$output" -cmdenv "LD_LIBRARY_PATH=./local/lib:./libs/usr/lib64" -cmdenv "PYTHONHOME=./python/python:./local" -cmdenv "PYTHONPATH=./python/python/lib/python2.7:./local/lib/python2.7:." -mapper "./python/python/bin/python $mapper $margs" -reducer "./python/python/bin/python $reducer $rargs" -file "$mapper" -file "$reducer"
    }

After sourcing `~/.bashrc` again, the function gives help by running `pyhadoop`. As can be seen, the function needs at least four arguments: the input file, the output directory, the Python mapper script and the Python reducer script. Then one can give arguments to the mapper and reducer, respectively. Put these between quotes if you want to give more than one argument per script.

The rest of the command is interpreted as extra arguments to `hadoop`, such as any additional archive files you might want to make available to the workers. These archives must be on HDFS and are then unpacked on the worker nodes. The part after the `#` specifies the directory name to unpack the archive in, but beware of directories within archives as well. So, for example, if you have an archive `data.tgz` containing a directory data with additional data files, then pass it like this:

    $ hdfs dfs -put data.tgz
    $ pyhadoop input.txt result mapper.py reducer.py "data/data 123" "data/data 42" -archives "$HDFS_URL/data.tgz#data"

If you have hardcoded paths, sometimes you can circumvent these directory problems by using e.g. `-files \"$HDFS_URL/words/positive.txt#words/positive.txt,$HDFS_URL/words/negative.txt#words/negative.txt\"`

MPI
---

To get the `preprocess.py` script running on distributed nodes, MPI must be able to connect to other nodes via SSH. Although SSH access is possible, one must ensure that there are no interactive authentication prompts when MPI tries to open an SSH connection. This is complicated further by the fact that MPI might open SSH connections on other nodes as well.

Let us first start with setting up an SSH key. Run `ssh-keygen -t rsa`. For the first question, keep the default file of `~/.ssh/id_rsa`. For the next two questions, enter and confirm a strong passphrase. Not entering one would make it easier to share the key, but is extremely unsafe and should not be done. After this, `cd $HOME/.ssh` and make the key authorized: `cp id_rsa.pub authorized_keys`. Ensure that these two files are world-readable for SSH and that `id_rsa` is only read/writable by the user with `ls -la`.

Once again, add the following to `~/.bashrc` to make running the SSH authentication and MPI easier:

    alias ssh-activate='eval $(ssh-agent);ssh-add ~/.ssh/id_rsa'
    pympi () {
            procs=$1;shift;
            if [[ "x$procs" = "x" ]]; then
                    echo "Usage: pympi <procs> <program> <progargs> [...]"
                    echo "Program is a file in this directory."
                    echo "For files on the scratch, use \\\$SCRATCH/path/to/file."
                    echo "Specify program arguments between quotes."
                    echo "Rest of the parameters are used for the mpi command."
                    echo "Example: pympi 8 test.py \"\" --hostfile hosts"
                    return
            fi
            prog=$1;shift;
            args=$1;shift;
            mpirun -np $procs $@ bash -c "source ~/.bashrc;source activate;python $prog $args"
    }

Now `source ~/.bashrc` and then run `ssh-activate` in order to set up an SSH agent with your key by entering your passphrase. We can already use the `pympi` function to run a program locally without problem, however we are not yet done setting up which hosts we can connect to. Use `./ssh-setup.sh /scratch/spark/conf/slaves` to set up a hosts file as well as check if all connections are OK. Follow the instructions there and rerun it in case something goes wrong. Note that `ssh-activate` must be run every session before using `pympi`, while setup only needs to be done once.

Once all is set up, run the preprocess script distributed as follows: `pympi 8 preprocess.py "repos language" --hostfile hosts`. Note that if your checkout is in `/scratch/scratch`, then instead use the filename `\$SCRATCH/SDDM/preprocess.py`, including the backslash.

Additional notes for installing Qt
----------------------------------

Note that installing Python from source on the DAS has the strange effect that among others, the default Tk GUI library in Python does not function. This is probably related to missing dependencies (development headers) or to configuration flags. Either way, it might be better to use something like GTK or Qt, although it is certainly not easy.

Also, this section is of limited use: one can display `matplotlib` files through X forwarding (make sure to use `ssh -X` on all connections between you and the DAS).

Installation will cost at least 4 hours. We assume you are in an `activate`d virtualenv shell.

- Download the Qt source from http://download.qt-project.org/official_releases/qt/5.4/5.4.1/single/qt-everywhere-opensource-src-5.4.1.tar.gz
- Extract with `tar xzf qt-everywhere-opensource-src-5.4.1.tar.gz` and `cd` 
  into that directory
- Compile as follows:

        $ ./configure -prefix $SCRATCH/opt -opensource -nomake tests -qt-xcb
        $ make
        $ make install

  Each step takes a long time. Answer `yes` to the license question during `./configure`, and check at the end whether the configuration makes sense. We probably did not need the entirety of Qt, but it is the easiest way, and the binary installation did not work.
- Download and install SIP:
  
        $ wget http://sourceforge.net/projects/pyqt/files/sip/sip-4.16.6/sip-4.16.6.tar.gz
        $ tar xzvf sip-4.16.6.tar.gz
        $ cd sip-4.16.6
        $ python configure.py
        $ make
        $ make install
- Download PyQt4 in the same fashion as SIP from http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.11.3/PyQt-x11-gpl-4.11.3.tar.gz and again use `configure.py`.
- This should be enough to display plots using `matplotlib`. Try out `python plot.py` with some frequency data (e.g., from a MapReduce run) to test.
- Requirements for IPython QtConsole:

        $ pip install pygments
        $ pip install pyzmq
        $ pip install ipython

Finding application logs
------------------------
After completing a job, you can find the logs with:

    $ hdfs dfs -ls /app-logs/{username}/logs/

The latest one is the most recent application job. Copy the whole application ID behind the slash, e.g. `application_1421846212827_0079`. Then you can read the logs with:
    
    $ yarn logs -applicationId application_1421846212827_0079 | less

Authors
=======

* Tim van der Meij (Leiden University, @timvandermeij)
* Leon Helwerda (Leiden University, @lhelwerd)

References
==========

* https://github.com/jeffreybreen/twitter-sentiment-analysis-tutorial-201107/tree/master/data/opinion-lexicon-English (positive and negative word lists)
