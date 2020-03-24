#! /usr/bin/python3
# Version: MPL 1.1 / GPLv3+ / LGPLv3+
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License or as specified alternatively below. You may obtain a copy of
# the License at http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# Major Contributor(s):
# Copyright (C) 2012 Red Hat, Inc., Michael Stahl <mstahl@redhat.com>
#  (initial developer)
#
# All Rights Reserved.
#
# For minor contributions see the git repository.
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 3 or later (the "GPLv3+"), or
# the GNU Lesser General Public License Version 3 or later (the "LGPLv3+"),
# in which case the provisions of the GPLv3+ or the LGPLv3+ are applicable
# instead of those above.

import sys, os, getopt

def readFile(url):
    d = {}
    with open(url) as f:
        for line in f:
           key = line.strip().split(' ')[2]
           val = line.strip().split('- ')[1]

           d[key] = float(val)
    return d

def usage():
    message = """usage: {program} [option]..."
 -h | --help:      print usage information
 --old=URL     path to old file to be compared
 --new=URL     path to new file to be comparted"""

    print(message.format(program = os.path.basename(sys.argv[0])))


if __name__ == "__main__":

    try:
        opts,args = getopt.getopt(sys.argv[1:], "o:n:h",
                ["old=", "new=", "help"])
    except getopt.GetoptError:
        usage()
        sys.exit(1)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(1)
        elif opt in ('-o', '--old'):
            old_url = arg
        elif opt in ('-n', '--new'):
            new_url = arg
        else:
            usage()
            sys.exit(1)

    if not os.path.exists(old_url):
        print("File " + old_url + " doesn't exist!")
        sys.exit(1)
    elif not os.path.exists(new_url):
        print("File " + new_url + " doesn't exist!")
        sys.exit(1)

    oldValues = readFile(old_url)
    newValues = readFile(new_url)
    meanOld = sum(oldValues.values())/len(oldValues)
    maxValue = max(oldValues.values())

    results = {}
    print("Mean value: " + str(meanOld))

    for k, v in oldValues.items():
        if k not in newValues:
            print("File: " + k + " doesn't exist. Why?")
            continue
        diff = newValues[k] / v
        # check if it's 3 times slower for small values
        # or 2 times slower for greater values
        # or timeout is reached
        if diff >= 3 \
                or (v > meanOld and diff >= 2 ) \
                or (v != maxValue and newValues[k] == maxValue):
            results[k] = [diff, v, newValues[k]]
    
    sorted_results = sorted(results.items(), key=lambda kv: kv[1], reverse=True)
    for k, v in sorted_results:
        print("File " + k + " is " + str('%.3f' % v[0]) + " slower. Before: " + str('%.3f' % v[1]) + ". After: " + str('%.3f' % v[2]))

# vim:set shiftwidth=4 softtabstop=4 expandtab:
