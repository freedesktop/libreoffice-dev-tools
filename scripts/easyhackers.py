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

def get_easyhacks():
    url = 'https://bugs.libreoffice.org/buglist.cgi?bug_status=UNCONFIRMED&bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&bug_status=RESOLVED&bug_status=VERIFIED&bug_status=CLOSED&bug_status=NEEDINFO&bug_status=PLEASETEST&columnlist=&limit=0&list_id=355677&product=LibreOffice&query_format=advanced&status_whiteboard=EasyHack&status_whiteboard_type=allwords&ctype=csv&human=0'
    try:
        resp = urlopen(url)
    except URLError:
        sys.stderr.write('Error fetching {}'.format(url))
        sys.exit(1)
    bug_ids=[]
    for line in [raw.decode('utf-8').strip('\n') for raw in BytesIO(resp.read())][1:]:
        bug_ids.append(int(line))
    return bug_ids

def print_counts(counts):
    printorder = reversed(sorted((count, name) for (name, count) in counts.items()))
    for count in printorder:
        print('%5d %s' % (count[0], count[1]))

if __name__ == '__main__':
    easyhacker_counts = {}
    easyhack_ids = get_easyhacks()
    sys.stderr.write('found %d easyhacks: %s\n' % (len(easyhack_ids), easyhack_ids))
    for bug_id in easyhack_ids:
        sys.stderr.write('working on bug %d\n' % bug_id)
        # FIXME: use --numstat instead, which does not abbreviate filenames
        logstat = sh.git('--no-pager', 'log', '--grep', 'fdo#%d' % bug_id, '--pretty=%aE')
        for line in logstat:
            sys.stderr.write('found easyhacker: %s\n' % line)
            if line in easyhacker_counts:
                easyhacker_counts[line]+=1
            else:
                easyhacker_counts[line]=1
    print('easyhackers:')
    print_counts(easyhacker_counts)
