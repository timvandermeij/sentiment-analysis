-------------------------------------------------------------------
Install Python 2.7 in a Virtualenv with libraries and use on Hadoop
-------------------------------------------------------------------

Python 2.7
$ wget https://www.python.org/ftp/python/2.7.9/Python-2.7.9.tgz
$ tar xzvf Python-2.7.9.tgz
$ cd Python-2.7.9
$ ./configure --prefix=$HOME/.local
$ make
$ make install

Virtualenv
$ pip install --user virtualenv
  (^this can be run with Python 2.6's pip, this does not matter at this point)
$ cd /scratch/scratch/... (we assume this directory from now on)
$ virtualenv -p $HOME/.local/bin/python2.7 python
$ virtualenv --relocatable python

Shared libaries (optional)
It's mostly about wget, ./configure --prefix=/scratch/scratch/.../opt then make and make install.
- OpenBLAS: Instead do the first part of http://stackoverflow.com/questions/11443302/compiling-numpy-with-openblas-integration/14391693#14391693
  with correct PREFIX=... and no sudo nor ldconfig.
- OpenMPI

Update ~/.bashrc with the following variables:
PATH="$PATH:$HOME/.local/bin:/mounts/CentOS/6.6/root/usr/bin:/scratch/scratch/.../python/bin:/scratch/scratch/.../opt/bin"
export LIBRARY_PATH="$HOME/.local/lib:/scratch/scratch/.../opt/lib"
export LD_LIBRARY_PATH="$HOME/.local/lib:/scratch/scratch/.../opt/lib"
export CPATH="$HOME/.local/include:/scratch/scratch/.../opt/include"
export BLAS="$HOME/.local/lib/libopenblas.a" (optional)

Then use `source ~/.bashrc`

Python libraries
$ source python/bin/activate (alternatively, make an alias for it)
(python)$ pip install cython,readline
(python)$ pip install numpy
   (^there's a chance that this does not work because you might want OpenBLAS,
   then we would need to install from source according to the following:
   http://stackoverflow.com/questions/11443302/compiling-numpy-with-openblas-integration/14391693#14391693
   Note that this might screw up the latter pip installations since they depend
   on numpy and consider a numpy installed this way to be incompatible, but that
   can be avoided by passing --no-deps to at least scipy,pandas,scikit-learn,numexpr.)
(python)$ pip install scipy,pandas,scikit-learn,numexpr,matplotlib,mpi4py (optional)

Hadoop
$ tar xzvf python.tgz python/
$ tar xzvf local.tgz $HOME/.local/*
  (or perhaps in that directory to ensure it has no path in the tarball)
$ tar xzvf libs.tgz /usr/lib64/libg2c.so* /usr/lib/libgfortran.so*
$ hdfs dfs -put python.tgz,local.tgz,libs.tgz

Add the following to ~/.bashrc:

# Add username here
export HDFS_URL='hdfs://fs.das3.liacs.nl:8020/user/...'
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
    hadoop jar /usr/lib/hadoop-mapreduce/hadoop-streaming.jar -archives "$HDFS_URL/python.tgz#python,$HDFS_URL/local.tgz#local,$HDFS_URL/libs.tgz#libs" $@ -input "$input" -output "$output" -cmdenv "LD_LIBRARY_PATH=./local/lib:./libs/usr/lib64" -cmdenv "PYTHONHOME=./python/python:./local" -cmdenv "PYTHONPATH=./python/python/lib/python2.7:./local/lib/python2.7" -mapper "./python/python/bin/python $mapper $margs" -reducer "./python/python/bin/python $reducer $rargs" -file "$mapper" -file "$reducer"
}

After sourcing the ~/.bashrc again, the function gives help by running `pyhadoop`.

------------------------
Finding application logs
------------------------
After completing a job, you can find the logs with:
$ hdfs dfs -ls /app-logs/.../logs/

The latest one is the most recent application job. Copy the whole application ID behind the slash, e.g. application_1421846212827_0079. Then you can read the logs with:
$ yarn logs -applicationId application_1421846212827_0079 | less
