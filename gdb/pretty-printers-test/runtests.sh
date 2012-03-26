#!/bin/sh

for mod in cppu sal svl; do
    ./runtest.sh ${mod}
done

# vim:set shiftwidth=4 tabstop=4 expandtab:
