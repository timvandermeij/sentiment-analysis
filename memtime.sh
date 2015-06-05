#!/bin/bash
echo "Running $@" >&2
# time sends to stderr, so we can easily ignore the output of the program.
stdbuf -o L `which time` -f "real\t%E\nuser\t%U\nsys\t%S\nmem\t%M/4 kB" "$@"
echo "We are interested in user+system time (both seconds) and peak memory use." >&2
