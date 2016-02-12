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

def formatEasy(easyHack) :
    return 'https://bugs.documentfoundation.org/show_bug.cgi?id={} {}'.format(easyHack['id'], easyHack['desc'])



def ESC_easyHacks(easyHacks) :

    # prepare to count easyHacks, and list special status, new hacks (7 days)
    xTot    = len(easyHacks)
    xAssign = 0
    xOpen   = 0
    xInfo   = 0
    pNew    = []
    pInfo   = []
    cDate   = datetime.date.today() - datetime.timedelta(days=8)

    for key, row in easyHacks.items():
      # Calculate type of status
      status = row['status']
      if status == 'ASSIGNED' :
        xAssign += 1
      elif status == 'NEEDINFO' :
        xInfo += 1
        pInfo.append(row)
      elif status == 'NEW' or status == 'REOPENED' :
        xOpen += 1

      if row['created'] >= cDate :
        pNew.append(row)

    print('    easyHacks {}: {} ready to be worked on, {} being worked on, {} need info'.format(xTot, xOpen, xAssign, xInfo))
    print('        new since last:')
    for row in pNew :
      print('            ', end='')
      print(formatEasy(row))
    if xInfo > 0 :
      print('        need info, please help:')
      for row in pInfo :
        print('            ', end='')
        print(formatEasy(row))




if __name__ == '__main__':
    easyHacks = get_easyHacks()

    ESC_easyHacks(easyHacks)

