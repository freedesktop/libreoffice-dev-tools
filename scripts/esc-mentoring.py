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
import xmltodict
from xml.etree.ElementTree import XML
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
    xCSV = list(csv.reader(io.TextIOWrapper(resp)))[1:]
    resp.close()
    xCSV.sort()
    rawList = {}
    for row in xCSV:
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
    url = url + '&o=DETAILED_LABELS&o=MESSAGES&o=DETAILED_ACCOUNTS'
    #url = url + '&o=code_review&o=reviewers&pp=0'

    try:
        resp = urlopen(url)
    except URLError:
        sys.stderr.write('Error fetching {}'.format(url))
        sys.exit(1)

    data = resp.read().decode('utf8')[5:]
    rawList = json.loads(data)
    resp.close()
    for row in rawList :
      row['updated'] = datetime.datetime.strptime(row['updated'].split(' ')[0], '%Y-%m-%d').date()
    return rawList



def get_bug(id) :
    url = 'https://bugs.documentfoundation.org/show_bug.cgi?ctype=xml&id=' + str(id)
    try:
        resp = urlopen(url)
    except URLError:
        sys.stderr.write('Error fetching {}'.format(url))
        sys.exit(1)
    bug = xmltodict.parse(resp.read())
    resp.close()
    return bug



def optimize_bug(bug_org) :
    bug = bug_org['bugzilla']['bug']
    del bug['bug_file_loc']
    del bug['cclist_accessible']
    del bug['classification']
    del bug['classification_id']
    del bug['comment_sort_order']
    del bug['creation_ts']
    del bug['delta_ts']
    del bug['reporter_accessible']
    del bug['resolution']

    # collect info for new comments:
    if 'reporter' not in bug :
        newText = 'org_reporter: MISSING'
    else :
        if type(bug['reporter']) is str:
            newText = 'org_reporter: ' + bug['reporter'] + '\n'
        else :
            newText = 'org_reporter: ' + bug['reporter']['@name'] + '/' + bug['reporter']['#text'] + '\n'
        del bug['reporter']

    for line in bug['long_desc'] :
       if 'who' not in line or type(line) is str:
         newText += 'who: UNKNOWN' + '\n' + line
       else :
         newText += 'who: ' + line['who']['@name'] + '/' + line['who']['#text']
    bug['long_desc'] = []
    bug['long_desc'].append({'thetext' : newText})
    addAlso = 'https://issues.apache.org/ooo/show_bug.cgi?id='+bug['bug_id']
    if 'see_also' not in bug :
      bug['see_also'] = addAlso
    elif not type(bug['see_also']) is list :
        x = bug['see_also']
        bug['see_also']  = [x, addAlso]
    else :
      bug['see_also'].append(addAlso)
    return bug



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
      if row['whiteboard'] == 'ToBeReviewed':
        xRevi += 1

      if row['created'] >= cDate :
        pNew.append(row)
    print('* Easy Hacks (JanI)')
    print('    + total {}: {} not assigned, {} Assigned to contributors, {} need info'.format(xTot, xOpen, xAssign, xInfo))
    print('    + needsDevEval {} needs to be evaluated'.format(needsDevEval))
    print('    + cleanup: {} has more than 4 comments, {} needs to be reviewed'.format(xComm, xRevi))
    print('    + new last 8 days:')
    for row in pNew :
      print('            ', end='')
      print(formatEasy(row))
    print ('    + <text>')
    print('\n\n')

    xTot  = len(gerritOpen)
    xRevi = 0
    for row in gerritOpen:
      # can be merged (depending comments)
      if checkGerrit(1, row) :
        xRevi += 1
    print ('* Mentoring Update (JanI)')
    print ('    + total: {} open gerrit patches of which {} are mergeable'.format(xTot, xRevi))
    xTot  = len(gerritContributor)
    xRevi = 0
    for row in gerritContributor:
      # can be merged (depending comments)
      if checkGerrit(1, row) :
        xRevi += 1
    print ('    + contributors: {} open gerrit patches of which {} are mergeable'.format(xTot, xRevi))
    print ('    + <text>')



def DAY_report(runMsg, easyHacks, gerritOpen, gerritContributor) :
    # Day report looks 8 days back
    cDate = datetime.date.today() - datetime.timedelta(days=8)

    print("*** new easyHacks (verify who created it):")
    for key, row in easyHacks.items():
      if row['created'] >= cDate :
        print('    ', end='')
        print(formatEasy(row))

    print("\n\n*** Gerrit mangler reviewer:")
    for row in gerritContributor:
      if not checkGerrit(2, row) :
        print('    ', end='')
        print(formatGerrit(row))

    # Month report looks 30 days back
    cDate   = datetime.date.today() - datetime.timedelta(days=30)

    print("\n\n*** Gerrit to abandon:")
    for row in gerritContributor:
      # can be merged (depending comments)
      if checkGerrit(5, row, cDate=cDate) :
        print('    ', end='')
        print(formatGerrit(row))

    print('\n\n*** assigned easyHacks, no movement')
    for key, row in easyHacks.items():
      if row['change'] <= cDate and row['status'] == 'ASSIGNED':
        print('    ', end='')
        print(formatEasy(row))

    print("\n\ne*** asyHacks needing review due to whiteboard:")
    bugs = []
    for key, row in easyHacks.items():
      if row['comments'] < 5 and 'ToBeReviewed' in row['whiteboard']  :
        print('    ', end='')
        print(formatEasy(row))

    if runMsg == "dump" :
        print("\n\n*** easyHacks with more than 5 comments:")
        bugs = []
        for key, row in easyHacks.items():
            if row['comments'] >= 5 :
                bugs.append(optimize_bug(get_bug(key)))
        with open('bz_comments.json', 'w') as f:
            json.dump(bugs, f, ensure_ascii=False, indent=4, sort_keys=True)
        xTot = len(bugs)
        print('    wrote {} entries to bz_comments.json'.format(xTot))




if __name__ == '__main__':
    # check command line options
    doESC   = True
    if len(sys.argv) > 1 :
      if sys.argv[1] != 'esc' :
        doESC = False

    # get data from bugzilla and gerrit
    easyHacks         = get_easyHacks()
    needsDevEval      = get_count_needsDevEval()
    gerritOpen        = get_gerrit(False)
    gerritContributor = get_gerrit(True)

    if doESC :
      ESC_report(easyHacks, gerritOpen, gerritContributor, needsDevEval)
    else :
      DAY_report(sys.argv[1],easyHacks, gerritOpen, gerritContributor)
    print('\n\nend of report')

