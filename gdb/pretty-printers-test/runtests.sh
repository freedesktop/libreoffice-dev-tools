#!/bin/sh

for mod in cppu sal svl tl; do
    ./runtest.sh ${mod}
done

# vim:set shiftwidth=4 tabstop=4 expandtab:
