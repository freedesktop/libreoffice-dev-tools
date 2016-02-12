#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import sys
import csv
import io
import datetime
from urllib.request import urlopen, URLError

def get_easyHacks():
    url = 'https://bugs.documentfoundation.org/buglist.cgi?' \
          'bug_status=UNCONFIRMED&bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&bug_status=VERIFIED&bug_status=NEEDINFO' \
          '&columnlist=Cbug_id%2Cassigned_to%2Cbug_status%2Cshort_desc%2Cchangeddate%2Creporter%2Clongdescs.count%2Copendate' \
          '&keywords=easyHack%2C%20' \
          '&keywords_type=allwords' \
          '&query_format=advanced' \
          '&resolution=---' \
          '&ctype=csv' \
          '&human=0'
    try:
        resp = urlopen(url)
    except URLError:
        sys.stderr.write('Error fetching {}'.format(url))
        sys.exit(1)
    xCSV = list(csv.reader(io.TextIOWrapper(resp)))
    rawList = {}
    for row in xCSV[1:]:
       id = int(row[0])
       if row[1] == 'libreoffice-bugs' :
         assign = ''
       else :
         assign = row[1]
       rawList[id] = {'id'       : id,
                      'assign'   : assign,
                      'status'   : row[2],
                      'desc'     : row[3],
                      'change'   : datetime.datetime.strptime(row[4].split(' ')[0], '%Y-%m-%d').date(),
                      'reporter' : row[5],
                      'comments' : int(row[6]),
                      'created'  : datetime.datetime.strptime(row[7].split(' ')[0], '%Y-%m-%d').date()
                     }
    return rawList
def print_counts(counts):
    printorder = reversed(sorted((count, name) for (name, count) in counts.items()))
    for count in printorder:
        print('%5d %s' % (count[0], count[1]))

if __name__ == '__main__':
    fixed_regression_ids = get_easyHacks()
    sys.stderr.write('found %d fixed regressions: %s\n' % (len(fixed_regression_ids), fixed_regression_ids))
#    for bug_id in fixed_regression_ids:
#        sys.stderr.write('working on bug %d\n' % bug_id)
#        # FIXME: use --numstat instead, which does not abbreviate filenames
#        logstat = sh.git('--no-pager', 'log', '--grep', '[fdo|tdf]#%d' % bug_id, '--stat')
#        for line in logstat:
#            match = statregex.search(str(line))
#            if match and match.group(1):
#                filename = match.group(1)
#                sys.stderr.write('regression fix touched file: %s\n' % filename)
#                if filename in file_counts:
#                    file_counts[filename]+=1
#                else:
#                    file_counts[filename]=1
#    print('top level dirs:')
#    print_counts(get_dir_counts(file_counts, 1))
#    print('\nsecond level dirs:')
#    print_counts(get_dir_counts(file_counts, 2))
#    print('\nthird level dirs:')
#    print_counts(get_dir_counts(file_counts, 3))
#    print('\nfourth level dirs:')
#    print_counts(get_dir_counts(file_counts, 4))
#    print('\nfiles:')
#    print_counts(file_counts)
