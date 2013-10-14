#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import sys
import re
import sh
from urllib.request import urlopen, URLError
from io import BytesIO

def get_fixed_regression_bugs():
    url = 'https://bugs.freedesktop.org/buglist.cgi?bug_status=UNCONFIRMED&bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&bug_status=RESOLVED&bug_status=VERIFIED&bug_status=CLOSED&bug_status=NEEDINFO&bug_status=PLEASETEST&columnlist=&keywords=regression%2C%20&keywords_type=allwords&limit=0&list_id=354018&product=LibreOffice&query_format=advanced&resolution=FIXED&ctype=csv&human=0'
    try:
        resp = urlopen(url)
    except URLError:
        sys.stderr.write('Error fetching {}'.format(url))
        sys.exit(1)
    bug_ids=[]
    for line in [raw.decode('utf-8').strip('\n') for raw in BytesIO(resp.read())][1:]:
        bug_ids.append(int(line))
    return bug_ids

def get_dir_counts(file_counts, level):
    dir_counts = {}
    for (filename, count) in file_counts.items():
        fileparts = filename.split('/')
        if len(fileparts) > level:
            dirpart = '/'.join(fileparts[:level])
            if dirpart in dir_counts:
                dir_counts[dirpart]+=1
            else:
                dir_counts[dirpart]=1
    return dir_counts

def print_counts(counts):
    printorder = reversed(sorted((count, name) for (name, count) in counts.items()))
    for count in printorder:
        print('%5d %s' % (count[0], count[1]))

if __name__ == '__main__':
    file_counts = {}
    statregex = re.compile('^ ([^ ]+) \|')
    fixed_regression_ids = get_fixed_regression_bugs()
    sys.stderr.write('found %d fixed regressions: %s\n' % (len(fixed_regression_ids), fixed_regression_ids))
    for bug_id in fixed_regression_ids:
        sys.stderr.write('working on bug %d\n' % bug_id)
        logstat = sh.git('--no-pager', 'log', '--grep', 'fdo#%d' % bug_id, '--stat')
        for line in logstat:
            match = statregex.search(line)
            if match and match.group(1):
                filename = match.group(1)
                sys.stderr.write('regression fix touched file: %s\n' % filename)
                if filename in file_counts:
                    file_counts[filename]+=1
                else:
                    file_counts[filename]=1
    print('top level dirs:')
    print_counts(get_dir_counts(file_counts, 1))
    print('\nsecond level dirs:')
    print_counts(get_dir_counts(file_counts, 2))
    print('\nthird level dirs:')
    print_counts(get_dir_counts(file_counts, 3))
    print('\nfiles:')
    print_counts(file_counts)
