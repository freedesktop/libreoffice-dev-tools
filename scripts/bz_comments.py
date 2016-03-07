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
import json
from   urllib.request import urlopen, URLError



def get_list_easyHacks() :
    url = 'https://bugs.documentfoundation.org/buglist.cgi?' \
          'bug_status=UNCONFIRMED&bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&bug_status=VERIFIED&bug_status=NEEDINFO' \
          '&columnlist=Cbug_id' \
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
    resp.close()
    rawList = []
    for row in xCSV[1:]:
       rawList.append(row[0])
    return rawList



def get_bug(id) :
    url = 'https://bugs.documentfoundation.org/show_bug.cgi?ctype=xml&id=' + id
    try:
        resp = urlopen(url)
    except URLError:
        sys.stderr.write('Error fetching {}'.format(url))
        sys.exit(1)
    xText = resp.read().decode("utf8")
    resp.close()
    return xText



if __name__ == '__main__':
    # get data from bugzilla and gerrit
    easyHacks = get_list_easyHacks()
    for id in easyHacks :
      bug = get_bug(id)
      print(bug)

    print('end of report')

