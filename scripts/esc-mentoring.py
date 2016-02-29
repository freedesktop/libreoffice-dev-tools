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



def get_count_needsDevEval() :
    url = 'https://bugs.documentfoundation.org/buglist.cgi?' \
          'bug_status=UNCONFIRMED&bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&bug_status=VERIFIED&bug_status=NEEDINFO' \
          '&columnlist=Cbug_id%2Cassigned_to%2Cbug_status%2Cshort_desc%2Cchangeddate%2Creporter%2Clongdescs.count%2Copendate%2Cstatus_whiteboard' \
          '&keywords=needsDevEval%2C%20' \
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
    return len(xCSV) -1



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
       status = row[2]
       if status == 'REOPENED' :
         status = 'NEW'
       rawList[id] = {'id'         : id,
                      'assign'     : assign,
                      'status'     : status,
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
    for row in rawList :
      row['updated'] = datetime.datetime.strptime(row['updated'].split(' ')[0], '%Y-%m-%d').date()
    return rawList




def formatEasy(easyHack) :
    return 'https://bugs.documentfoundation.org/show_bug.cgi?id={} mentor:{} -> "{}"'.format(easyHack['id'], easyHack['reporter'], easyHack['desc'])



def formatGerrit(patch) :
    return 'https://gerrit.libreoffice.org/#/c/{}/ author:{} -> "{}"'.format(patch['_number'], patch['owner']['name'], patch['subject'])



def checkGerrit(checkType, patch, cDate=0, eDate=0) :
    if checkType == 1 or checkType == 3:
      # True, if there are no -1 and patch is mergeable
      # 3 also checks on start/end date
      # Optional Check no open comments

      # date check (3 days old)
      if checkType == 3 and (patch['updated'] < cDate or patch['updated'] > eDate) :
        return False

      # not mergeable
      if not patch['mergeable'] :
        return False

      # review or verify -1
      if 'labels' in patch and 'Code-Review' in patch['labels']  and 'all' in patch['labels']['Code-Review'] :
        for chk in patch['labels']['Code-Review']['all'] :
          if 'value' in chk and chk['value'] < 0 :
            return False
      if 'labels' in patch and 'Verified' in patch['labels']  and 'all' in patch['labels']['Verified'] :
        for chk in patch['labels']['Verified']['all'] :
          if 'value' in chk and chk['value'] < 0 :
            return False
      return True
    elif checkType == 2 :
      # True if there are reviewer
      if 'labels' in patch and 'Code-Review' in patch['labels']  and 'all' in patch['labels']['Code-Review'] :
        for chk in patch['labels']['Code-Review']['all'] :
          name = chk['name']
          if not name == 'Jenkins' and not name == patch['owner'] :
            return True
      return False
    elif checkType == 4 :
      # True if merge conflict and no jani comment
      return False
    elif checkType == 5 :
      # true if last change is older than startDate
      if patch['updated'] <= cDate :
        return True
      return False
    return False



def ESC_report(easyHacks, gerritOpen, gerritContributor, needsDevEval) :
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
      elif status == 'NEW' :
        xOpen += 1
      if row['comments'] >= 5 :
        xComm += 1
      if row['change'] <= mDate or row['whiteboard'] == 'ToBeReviewed':
        xRevi += 1

      if row['created'] >= cDate :
        pNew.append(row)

    print('    easyHacks: total {}: {} waiting for contributor, {} Assigned to contributors, {} need info'.format(xTot, xOpen, xAssign, xInfo))
    print('               needsDevEval {} needs to be evaluated'.format(needsDevEval))
    print('               cleanup: {} has more than 4 comments, {} needs to be reviewed'.format(xComm, xRevi))
    print('        new last 8 days:')
    for row in pNew :
      print('            ', end='')
      print(formatEasy(row))
    if xInfo > 0 :
      print('        need info (mentor or code pointer), please help:')
      for row in pInfo :
        print('            ', end='')
        print(formatEasy(row))

    xTot  = len(gerritOpen)
    xRevi = 0
    for row in gerritOpen:
      # can be merged (depending comments)
      if checkGerrit(1, row) :
        xRevi += 1
    print('     gerrit: {} open patches of which {} can be merged if no open comments'.format(xTot, xRevi))
    xTot  = len(gerritContributor)
    xRevi = 0
    for row in gerritContributor:
      # can be merged (depending comments)
      if checkGerrit(1, row) :
        xRevi += 1
    print('             {} from contributors of which {} can be merged if no open comments'.format(xTot, xRevi))



def DAY_report(isWeekend, easyHacks, gerritOpen, gerritContributor) :
    # Day report looks 2 days back
    if isWeekend :
      cDate = datetime.date.today() - datetime.timedelta(days=3)
    else :
      cDate = datetime.date.today() - datetime.timedelta(days=1)

    print("\n\n*** day report ***")
    print("\n\n*** new easyHacks:")
    for key, row in easyHacks.items():
      if row['created'] >= cDate :
        print('    ', end='')
        print(formatEasy(row))
    print("\n\n*** changed easyHacks:")
    for key, row in easyHacks.items():
      if row['change'] >= cDate :
        print('    ', end='')
        print(formatEasy(row))

    print("\n\n*** Gerrit mangler reviewer:")
    for row in gerritContributor:
      if not checkGerrit(2, row) :
        print('    ', end='')
        print(formatGerrit(row))

    eDate = datetime.date.today() - datetime.timedelta(days=3)
    if isWeekend :
      cDate = datetime.date.today() - datetime.timedelta(days=5)
    else :
      cDate = datetime.date.today() - datetime.timedelta(days=3)
    print("\n\n*** Gerrit check for merge:")
    for row in gerritContributor:
      if checkGerrit(3, row, cDate=cDate, eDate=eDate) :
        print('    ', end='')
        print(formatGerrit(row))


def MONTH_report(easyHacks, gerritOpen, gerritContributor) :
    # Month report looks 30 days back
    cDate   = datetime.date.today() - datetime.timedelta(days=30)
    mDate   = datetime.date(2016, month=2, day=11)

    print("\n\n*** month report ***")
    print('assigned easyHacks, no movement')
    for key, row in easyHacks.items():
      if row['change'] <= cDate and row['status'] == 'ASSIGNED':
        print('    ', end='')
        print(formatEasy(row))
    print("\n\n*** easyHacks with more than 5 comments:")
    for key, row in easyHacks.items():
      if row['comments'] >= 5 :
        print('    ', end='')
        print(formatEasy(row))
    print("\n\n*** easyHacks needing review:")
    for key, row in easyHacks.items():
      if row['change'] <= mDate :
        print('    ', end='')
        print(formatEasy(row))
    print("\n\ne*** asyHacks needing review due to whiteboard:")
    for key, row in easyHacks.items():
      if row['whiteboard'] == 'ToBeReviewed' :
        print('    ', end='')
        print(formatEasy(row))

    print("\n\n*** Gerrit check Abandon:")
    for row in gerritOpen:
      if checkGerrit(5, row, cDate=cDate) :
        print('    ', end='')
        print(formatGerrit(row))




if __name__ == '__main__':
    # check command line options
    doESC   = False
    doDay   = False
    doWeek  = False
    doMonth = False
    if len(sys.argv) <= 1 :
      doESC = True
    else :
      for row in sys.argv[1:] :
        if row.lower() == 'esc' :
          doESC = True
        elif row.lower() == 'day' :
          doDay = True
        elif row.lower() == 'week' :
          doWeek = True
        elif row.lower() == 'month' :
          doMonth = True
        else :
          print('Illegal use {}, syntax: esc_mentoring.py esc day month'.format(row))
          exit(-1)

    # get data from bugzilla and gerrit
    easyHacks          = get_easyHacks()
    needsDevEval       = get_count_needsDevEval()
    gerritOpen         = get_gerrit(False)
    gerritContributor  = get_gerrit(True)
    

    if doESC :
      ESC_report(easyHacks, gerritOpen, gerritContributor, needsDevEval)
    if doDay or doWeek:
      print("\n\n\n")
      DAY_report(doWeek, easyHacks, gerritOpen, gerritContributor)
    if doMonth :
      print("\n\n\n")
      MONTH_report(easyHacks, gerritOpen, gerritContributor)
    print('end of report')

