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
    $ echo '{"body":"Yay, sentiment analysis is working perfectly!"}' | python analyze.py score

For the default group of `id` and the group `score`, running `preprocess.py` only needs to be done once. If all required data is available, `preprocess.py` will do nothing.

The output of the analysis program are lines containing scores between -1 and 1, where -1 indicates that the message is negative, 1 indicates that the
message is positive and 0 indicates that the message is neutral. The output can also contain grouping data or some visualization of the message.

Instead of using a single line as input, one can give a file to read as standard input as follows:

    $ python analyze.py < commit_comments.json
    $ python classify.py score < commit_comments.json

The latter `classify.py` script uses a classifier to predict the scores using a labeled dataset. Both programs work in a similar manner. This script requires the `2015-01-29` commit comments dump in order to cross-reference the labels with the messages. The classification itself can be run on any dump, and the script will filter any already labeled messages before prediction.

The output can be given to the `reducer.py` script, but only if it has been sorted on the first column of the output (the group or the score of the line).
This can be done using MapReduce as described later on, or by passing the output through `sort`. The `reducer.py` script generates a histogram of frequencies of the scores which can be passed to `plot.py` to
make a graph of the frequencies.

Groups
------

The code by default uses the `id` of a record as its group. This means that only the analyzer and classifier will do something useful. The reducer and plot scripts do not work nicely when the data is grouped this way. In order to group the classified targets with something else, pass another group, such as `score` or `language`, to all relevant scripts.

Note that for the `language` group, the preprocessor needs to retrieve more data, which can be done with `python preprocess.py repos language` and then again use `python preprocess.py commit_comments language`. These commands can also be distributed using MPI, in order to retrieve and process multiple dump files in parallel processes. Note that it is only necessary to parallelize the second command if one wants to receive all the commit comments dumps, whereas working with the `2015-01-29` dataset is usually enough.
The MPI parallelization can be done on one machine using `mpirun -n <num_processes> python preprocess.py repos language`. The instructions for running the preprocessor on distributed worker nodes are given in the installation instructions for the DAS-3, where the command is `pympi <num_processes> preprocess.py "repos language" --hostfile hosts --map-by node`.

Running the code in MapReduce
-----------------------------

This section assumes that the installation notes below have already been followed and all dependencies and scripts are set up. The exact commands to call the MapReduce scripts, for various group parameters, are given in this section.

First of all, ensure that the data sets are on the HDFS:

    $ hdfs dfs -put commit_comments.json
    $ hdfs dfs -put commit_comments.labeled.json
    $ hdfs dfs -put words/positive.txt words/positive.txt
    $ hdfs dfs -put words/negative.txt words/negative.txt

Now, one can start a MapReduce job which classifies each record in the data set and then counts the frequency of each score as follows:

    $ pyhadoop commit_comments.json score classify.py reducer.py "score" score -D stream.num.map.output.key.fields=2 -files \"$HDFS_URL/words/positive.txt#words/positive.txt,$HDFS_URL/words/negative.txt#words/negative.txt\" -file commit_comments.labeled.json -file commit_comments.json -file analyze.py

For the naive analyzer, use `analyze.py` instead of `classify.py`, and the last `-file` argument can be omitted. To count frequencies of scores within a specific group, use the following:

    $ pyhadoop commit_comments.json score_lang classify.py reducer.py "lang" lang -D stream.num.map.output.key.fields=2 -files \"$HDFS_URL/words/positive.txt#words/positive.txt,$HDFS_URL/words/negative.txt#words/negative.txt\" -file commit_comments.labeled.json -file commit_comments.json -file analyze.py

This ensures that MapReduce knows which parts of the outputs are keys and which are values.

Installation notes for the DAS-3
================================

This section describes how to set up all dependencies for running the Python code on the Distributed ASCI Supercomputer 3 at LIACS. Among others, this gives instructions
for installing Python 2.7 that can be run in a virtual environment, Hadoop configuration and MPI.

Python
------

Compile Python (version 2.7.9) from source:

    $ wget https://www.python.org/ftp/python/2.7.9/Python-2.7.9.tgz
    $ tar xzvf Python-2.7.9.tgz
    $ cd Python-2.7.9
    $ ./configure --prefix=$HOME/.local
    $ make
    $ make install
    $ rm Python-2.7.9.tgz

Virtualenv
----------

Install `virtualenv` using `pip` and create a virtual environment called `python` that we can distribute over the nodes using HDFS:

    $ pip install --user virtualenv
    $ mkdir /scratch/scratch/{username}
    $ cd /scratch/scratch
    $ chmod 700 {username}
    $ cd {username}
    $ ~/.local/bin/virtualenv -p ~/.local/bin/python2.7 python
    $ ~/.local/bin/virtualenv --relocatable python

OpenMPI
-------

Compile OpenMPI from source:

    $ cd ~
    $ wget http://www.open-mpi.org/software/ompi/v1.8/downloads/openmpi-1.8.4.tar.gz
    $ tar xzvf openmpi-1.8.4.tar.gz
    $ cd openmpi-1.8.4/
    $ ./configure --prefix=$HOME/.local
    $ make
    $ make install
    $ rm openmpi-1.8.4.tar.gz

OpenBLAS
--------

Compile OpenBLAS from source:

    $ cd ~
    $ git clone git://github.com/xianyi/OpenBLAS
    $ cd OpenBLAS && make FC=gfortran
    $ make PREFIX=$HOME/.local install

Update ~/.bashrc
----------------

Append the following segment to `~/.bashrc`:

    if [ "$HOSTNAME" = "fs.das3" ]; then
        export SCRATCH="/scratch/scratch/{username}"
    else   
        export SCRATCH="/scratch/{username}"
    fi
    alias activate="source $SCRATCH/python/bin/activate"
    export PATH="$PATH:$HOME/.local/bin:/mounts/CentOS/6.6/root/usr/bin:$SCRATCH/python/bin:$SCRATCH/opt/bin:$SCRATCH/opt/lib"
    export LIBRARY_PATH="$HOME/.local/lib:$SCRATCH/opt/lib"
    export LD_LIBRARY_PATH="$HOME/.local/lib:$SCRATCH/opt/lib"
    export CPATH="$HOME/.local/include:$SCRATCH/opt/include"
    export PKG_CONFIG_PATH="$HOME/.local/lib/pkgconfig:$SCRATCH/opt/lib/pkgconfig"
    export BLAS="$SCRATCH/opt/lib/libopenblas.a"

Then use `source ~/.bashrc` to reload the configuration.

Python libraries
----------------

Activate the virtual environment:

    $ activate

We now have a Python 2.7 virtual environment running, but `pip` is still from Python 2.6. In order to fix this, run the following:

    (python)$ cd $SCRATCH
    (python)$ wget https://bootstrap.pypa.io/get-pip.py
    (python)$ python get-pip.py -U -I

This installs `pip` for Python 2.7, which is less likely to give troubles with installing or upgrading dependencies.

First install the following dependencies:

    (python)$ pip install cython
    (python)$ pip install readline
    (python)$ pip install pymongo

Next we need to compile NumPy from source as we need it to work with OpenBLAS. It is not only better, but SciPy requires it because Lapack/BLAS are not installed on the
DAS-3. Follow the instructions from step 2 onward from this link: http://stackoverflow.com/questions/11443302/compiling-numpy-with-openblas-integration/14391693#14391693.
Make sure to use `/home/{username}/.local` for the paths.

If that is done (make sure to test that it is working) we continue installing the remaining dependencies:

    (python)$ pip install --no-deps scipy
    (python)$ pip install --no-deps pandas
    (python)$ pip install python-dateutil
    (python)$ pip install pytz
    (python)$ pip install --no-deps scikit-learn==0.16b1
    (python)$ pip install --no-deps numexpr
    (python)$ pip install --no-deps matplotlib
    (python)$ pip install pyparsing
    (python)$ pip install BeautifulSoup
    (python)$ pip install mpi4py

HDFS
----

Now we can put the entire environment on HDFS:

    $ tar czvf python.tgz python/
    $ tar czvf local.tgz ~/.local/
    $ tar czvf libs.tgz /usr/lib64/libg2c.so* /usr/lib64/libgfortran.so*
    $ hdfs dfs -put python.tgz
    $ hdfs dfs -put local.tgz
    $ hdfs dfs -put libs.tgz

Update ~/.bashrc again
----------------------

Append the following segment to `~/.bashrc`:

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

Let us first start with setting up an SSH key. Run `ssh-keygen -t rsa`. For the first question, keep the default file of `~/.ssh/id_rsa`. For the next two questions, enter and confirm a strong passphrase. Not entering one would make it easier to share the key, but is extremely unsafe and should not be done. After this, `cd ~/.ssh` and make the key authorized: `cp id_rsa.pub authorized_keys`. Ensure that these two files are world-readable for SSH and that `id_rsa` is only read/writable by the user with `ls -la`.

Once again, add the following to `~/.bashrc` to make running the SSH authentication and MPI easier:

    alias ssh-activate='eval $(ssh-agent);ssh-add ~/.ssh/id_rsa'
    pympi () {
            procs=$1;shift;
            if [[ "x$procs" = "x" ]]; then
                    echo "Usage: pympi <procs> <program> <progargs> [...]"
                    echo "Program is a file in this directory."
                    echo "Specify program arguments between quotes."
                    echo "Rest of the parameters are used for the mpi command."
                    echo "Example: pympi 8 test.py \"\" --hostfile hosts"
                    return
            fi
            prog=$1;shift;
            args=$1;shift;
            # Automatically replace /scratch/scratch/{username} with $SCRATCH
            # in working directory so that it works on other nodes
            workdir=${PWD/$SCRATCH/\$SCRATCH};
            mpirun -np $procs $@ bash -c "source ~/.bashrc;source activate;cd $workdir; python $prog $args"
    }

Now `source ~/.bashrc` and then run `ssh-activate` in order to set up an SSH agent with your key by entering your passphrase. We can already use the `pympi` function to run a program locally without problem, however we are not yet done setting up which hosts we can connect to. Use `./ssh-setup.sh /scratch/spark/conf/slaves` (after cloning the code from this repository) to set up a hosts file as well as check if all connections are OK. If the script complains about bad permissions, run `chown 600 $HOME/.ssh/config`. Follow any further instructions from the script and rerun it in case something goes wrong. Note that `ssh-activate` must be run every session before using `pympi`, while setup only needs to be done once.

The final stap is to edit `$SCRATCH/python/bin/activate`. Replace:

    VIRTUAL_ENV="/scratch/scratch/{username}/python"
    export VIRTUAL_ENV

with:

    SCRIPT="${BASH_SOURCE[0]}"
    pushd `dirname $SCRIPT` > /dev/null
    SCRIPTPATH=`pwd`
    VIRTUAL_ENV=`dirname $SCRIPTPATH`
    popd > /dev/null
    export VIRTUAL_ENV

This has to be done to make the virtual environment actually relocatable, otherwise it would be nonfunctional on the nodes, where we would still have Python 2.6.

Once everything is set up, check whether the Python scripts are distributed as follows: `pympi 8 mpi-test.py "" --hostfile hosts --map-by node`.

MPI also allows running parts of the preprocessing and classification steps on the worker nodes. As explained in the Groups section, we can preprocess the repos dumps in order to extract the languages. We can also download all the commit comments dumps in this way, keep them on local hard drives, and use a pretrained model to classify all the comments. This can be done for the `language` group as an example, as follows:

    $ python classify.py --model model.pickle --only-train [algorithm parameters]
    $ pympi 8 preprocess.py "commit_comments language /local/SDDM" --hostfile hosts --map-by node
    $ pympi 8 classify.py "language model.pickle /local/SDDM > \$HOSTNAME.dat" --hostfile hosts --map-by node
    $ cat node*.dat | sort | python reducer.py language > all-group.dat
    $ python plot.py language all-group.dat

The training of the model only needs to be done once to create the `model.pickle` file for one algorithm. The preprocess script automatically creates the given local path on the worker nodes when necessary. The classifications also happen on the workers, and are collected in a shared location. This allows us to pass it to the reducer to group the data for the plot script. This means that MapReduce is not necessary to perform the classification in this way.

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
* http://streamhacker.com/2010/05/10/text-classification-sentiment-analysis-naive-bayes-classifier/ (NLTK Naive Bayes classification, not used)
* http://www.cs.duke.edu/courses/spring14/compsci290/assignments/lab02.html#tf-idf-in-scikit-learn (TF.IDF in NLTK with stemming, not used)
* http://stackoverflow.com/questions/3667865/python-tarfile-progress-output (preprocess progress)

Related research:
* http://geeksta.net/geeklog/exploring-expressions-emotions-github-commit-messages/ (word lists approach)
* http://www.win.tue.nl/~aserebre/msr14daniel.pdf (Security and Emotion: Sentiment Analysis of Security Discussions on GitHub)

Scikit Learn:
* http://scikit-learn.org/stable/modules/classes.html
* http://scikit-learn.org/stable/tutorial/text_analytics/working_with_text_data.html (transformers and pipeline)

Hadoop:
* http://hadoop.apache.org/docs/r1.2.1/streaming.html
* http://henning.kropponline.de/2014/07/18/virtualenv-hadoop-streaming/
* https://altiscale.zendesk.com/hc/en-us/articles/200681097-Using-Python-Virtual-Environments-In-Hadoop
* http://www.michael-noll.com/tutorials/writing-an-hadoop-mapreduce-program-in-python/
* http://stackoverflow.com/questions/14291170/how-does-hadoop-process-records-records-split-across-block-boundaries

MPI and SSH:
* API Documentation:
  * http://mpi4py.scipy.org/docs/usrman/index.html
  * http://mpi4py.scipy.org/docs/apiref/mpi4py.MPI.Comm-class.html
* Idle jobs:
  * https://groups.google.com/forum/#!topic/mpi4py/nArVuMXyyZI
  * https://groups.google.com/forum/#!topic/mpi4py/Y0HrQkaPeNs
  * https://groups.google.com/forum/#!topic/mpi4py/LDHbzApI55c
* http://www.open-mpi.org/faq/?category=running
* http://www.open-mpi.org/faq/?category=rsh#ssh-keys (MPI setup)
* http://arc.liv.ac.uk/SGE/howto/hostbased-ssh.html (unsafe and nonfunctional authentication)
* https://developer.github.com/guides/using-ssh-agent-forwarding/ (agent forwarding)
