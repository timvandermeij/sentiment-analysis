from mpi4py import MPI
import socket
import os

comm = MPI.COMM_WORLD

print('Hello World I am rank {} of {} running on {} in path {}'.format(comm.rank, comm.size, socket.gethostname(), os.getcwd()))
