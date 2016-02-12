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



def get_easyHacks() :
    url = 'https://bugs.documentfoundation.org/buglist.cgi?' \
          'bug_status=UNCONFIRMED&bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&bug_status=VERIFIED&bug_status=NEEDINFO' \
          '&columnlist=Cbug_id%2Cassigned_to%2Cbug_status%2Cshort_desc%2Cchangeddate%2Creporter%2Clongdescs.count%2Copendate%2Cstatus_whiteboard' \
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
       rawList[id] = {'id'         : id,
                      'assign'     : assign,
                      'status'     : row[2],
                      'desc'       : row[3],
                      'change'     : datetime.datetime.strptime(row[4].split(' ')[0], '%Y-%m-%d').date(),
                      'reporter'   : row[5],
                      'comments'   : int(row[6]),
                      'created'    : datetime.datetime.strptime(row[7].split(' ')[0], '%Y-%m-%d').date(),
                      'whiteboard' : row[8]
                     }
    return rawList



def get_gerrit(doNonCom) :
    url = 'https://gerrit.libreoffice.org/changes/?' \
          'q=status:open'
    if (doNonCom) :
      url = url + '+-ownerin:committer'

    # Add needed fields
    url = url + '&o=DETAILED_LABELS&o=MESSAGES'
    #url = url + '&o=code_review&o=reviewers&pp=0'

    try:
        resp = urlopen(url)
    except URLError:
        sys.stderr.write('Error fetching {}'.format(url))
        sys.exit(1)

    data = resp.read().decode('utf8')[5:]
    rawList = json.loads(data)
    return rawList




def formatEasy(easyHack) :
    return 'https://bugs.documentfoundation.org/show_bug.cgi?id={} mentor:{} -> "{}"'.format(easyHack['id'], easyHack['reporter'], easyHack['desc'])



def ESC_report(easyHacks, gerritOpen, gerritContributor) :
    # prepare to count easyHacks, and list special status, new hacks (7 days)
    xTot    = len(easyHacks)
    xAssign = 0
    xOpen   = 0
    xInfo   = 0
    xComm   = 0
    xRevi   = 0
    pNew    = []
    pInfo   = []
    cDate   = datetime.date.today() - datetime.timedelta(days=8)
    mDate   = datetime.date(2016, month=2, day=11)
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
      if row['comments'] > 5 :
        xComm += 1
      if row['change'] <= mDate or row['whiteboard'] == 'ToBeReviewed':
        xRevi += 1

      if row['created'] >= cDate :
        pNew.append(row)

    print('    easyHacks: total {}: {} waiting for contributor, {} Assigned to contriburs, {} need info'.format(xTot, xOpen, xAssign, xInfo))
    print('               cleanup: {} has more than 5 comments, {} needs to be reviewed'.format(xComm, xRevi))
    print('        new last 8 days:')
    for row in pNew :
      print('            ', end='')
      print(formatEasy(row))
    if xInfo > 0 :
      print('        need info, please help:')
      for row in pInfo :
        print('            ', end='')
        print(formatEasy(row))
    print('     gerrit: open patches {} from non-committers {} non-mergeable {} not reviewd {}'.format(0,0,0,0))



def DAY_report(easyHacks, gerritOpen, gerritContributor) :
    # Day report looks 2 days back
    cDate   = datetime.date.today() - datetime.timedelta(days=2)

    print('*** day report ***')
    print('new easyHacks:')
    for key, row in easyHacks.items():
      if row['created'] >= cDate :
        print('    ', end='')
        print(formatEasy(row))
    print('changed easyHacks:')
    for key, row in easyHacks.items():
      if row['change'] >= cDate :
        print('    ', end='')
        print(formatEasy(row))



def MONTH_report(easyHacks, gerritOpen, gerritContributor) :
    # Month report looks 30 days back
    cDate   = datetime.date.today() - datetime.timedelta(days=30)
    mDate   = datetime.date(2016, month=2, day=11)

    print('*** month report ***')
    print('assigned easyHacks, no movement')
    for key, row in easyHacks.items():
      if row['change'] <= cDate and row['status'] == 'ASSIGNED':
        print('    ', end='')
        print(formatEasy(row))
    print('easyHacks with more than 5 comments:')
    for key, row in easyHacks.items():
      if row['comments'] > 5 :
        print('    ', end='')
        print(formatEasy(row))
    print('easyHacks needing review:')
    for key, row in easyHacks.items():
      if row['change'] <= mDate :
        print('    ', end='')
        print(formatEasy(row))
    print('easyHacks needing review due to whiteboard:')
    for key, row in easyHacks.items():
      if row['whiteboard'] == 'ToBeReviewed' :
        print('    ', end='')
        print(formatEasy(row))



if __name__ == '__main__':
    # check command line options
    doESC   = False
    doDay   = False
    doMonth = False
    if len(sys.argv) <= 1 :
      doESC = True
    else :
      for row in sys.argv[1:] :
        if row.lower() == 'esc' :
          doESC = True
        elif row.lower() == 'day' :
          doDay = True
        elif row.lower() == 'month' :
          doMonth = True
        else :
          print('Illegal use {}, syntax: esc_mentoring.py esc day month'.format(row))
          exit(-1)

    # get data from bugzilla and gerrit
    easyHacks          = get_easyHacks()
    gerritOpen         = get_gerrit(False)
    gerritContributor  = get_gerrit(True)

    if doESC :
      ESC_report(easyHacks, gerritOpen, gerritContributor)
    if doDay :
      print("\n\n\n")
      DAY_report(easyHacks, gerritOpen, gerritContributor)
    if doMonth :
      print("\n\n\n")
      MONTH_report(easyHacks, gerritOpen, gerritContributor)
    print('end of report')

