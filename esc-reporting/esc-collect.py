#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#


### DESCRIPTION
#
# This program collect data from
#     Openhub (including history and committer list)
#     Bugzilla (including comments and history)
#     Gerrit (including list of committers)
#     Git (all LibreOffice repos)
#
# The data is dumped to json files, with a history of minimum 1 year
#     esc/dump/['openhub','bugzilla','gerrit','git']_dump.json
#
# The JSON is a 1-1 copy of the data in the systems
# This program should only be changed when one of systems is updated.
#
# Installed on vm174:/usr/local/bin runs every night (making delta collection)
#
# Remark this program put a heavy load on our services, so please do not just run it.
# For analysis and reporting see the 2 other programs available.
#

import sys
import csv
import io
import os
import operator
import datetime
import json
import xmltodict
import requests
from requests.auth import HTTPDigestAuth



def util_load_file(fileName):
    try:
      fp = open(fileName, encoding='utf-8')
      rawData = json.load(fp)
      fp.close()
    except Exception as e:
      print('Error load file ' + fileName + ' due to ' + str(e))
      rawData = None
      pass
    return rawData



def util_load_url(url, useDict=False, useRaw=False, uUser=None, uPass=None):
    try:
      if uUser is None:
        r = requests.get(url)
        if useDict:
          try:
            rawData = xmltodict.parse(x)
          except Exception as e:
            rawData = {'response': {'result': {'project': {},
                                    'contributor_fact': {}}}}
        elif useRaw:
          rawData = r.text
        else:
          rawData = r.json()
      else:
        r = requests.get(url, auth=HTTPDigestAuth(uUser, uPass))
        rawData = json.loads(r.text[5:])
      r.close()
    except Exception as e:
      print('Error load url ' + url + ' due to ' + str(e))
      exit(-1)
    return rawData



def util_dump_file(fileName, rawList):
    try:
      fp = open(fileName, 'w', encoding='utf-8')
      json.dump(rawList, fp, ensure_ascii=False, indent=4, sort_keys=True)
      fp.close()
    except Exception as e:
      print('Error dump file ' + fileName + ' due to ' + str(e))
      os.remove(fileName)
      exit(-1)



def util_load_data_file(cfg, fileName, funcName, rawListProto):
    rawList = util_load_file(fileName)
    if rawList == None:
      rawList = rawListProto
      rawList['newest-entry'] = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime("%Y-%m-%d 00")
      print('retrieving full year of ' + funcName + ', take a coffee')
    searchDate = datetime.datetime.strptime(rawList['newest-entry'], "%Y-%m-%d %H") - datetime.timedelta(days=2)
    return searchDate, rawList



def get_openhub(cfg):
    fileName = cfg['homedir'] + 'dump/openhub_dump.json'
    searchDate, rawList = util_load_data_file(cfg, fileName, 'openhub', {'project': {}, 'people': {}})
    newDate = searchDate
    print("Updating openHub dump from " + rawList['newest-entry'])

    urlBase = 'https://www.openhub.net/p/libreoffice'
    url = urlBase + '.xml?api_key=' + cfg['openhub']['api-key']
    rawList['project'] = util_load_url(url, useDict=True)['response']['result']['project']

    url = urlBase + '/contributors.xml?api_key=' + cfg['openhub']['api-key'] + '&sort=latest_commit&page='
    pageId = -1
    while True:
      pageId += 1
      idList = util_load_url(url + str(pageId), useDict=True)['response']['result']['contributor_fact']
      for row in idList:
        rawList['people'][row['contributor_id']] = row
      if len(idList) == 0:
        break
      xDate = datetime.datetime.strptime(idList[-1]['last_commit_time'], "%Y-%m-%dT%H:%M:%SZ")
      if xDate < searchDate:
        break
      if xDate > newDate:
        newDate = xDate
    rawList['newest-entry'] = newDate.strftime("%Y-%m-%d %H")

    util_dump_file(fileName, rawList)
    return rawList



def get_bugzilla(cfg):
    fileName = cfg['homedir'] + 'dump/bugzilla_dump.json'
    searchDate, rawList = util_load_data_file(cfg, fileName, 'bugzilla', {'bugs': {}})
    print("Updating bugzilla dump from " + rawList['newest-entry'])

    url = 'https://bugs.documentfoundation.org/rest/bug?' \
          '&order=changeddate&chfieldto=Now&chfieldfrom=' + searchDate.strftime("%Y-%m-%d") + \
          '&limit=200&offset='
    newList = []
    while True:
      tmp = util_load_url(url + str(len(newList)))['bugs']
      if len(tmp) == 0:
        break
      newList.extend(tmp)

    urlH = 'https://bugs.documentfoundation.org/rest/bug/{}/history'
    urlC = 'https://bugs.documentfoundation.org/rest/bug/{}/comment'
    cnt = 0
    for row in newList:
      id = str(row['id'])
      if not 'cc' in row:
        row['cc'] = []
      if not 'keywords' in row:
        row['keywords'] = []
      tmp = util_load_url(urlH.format(id))
      row['history'] = tmp['bugs'][0]['history']
      tmp = util_load_url(urlC.format(id))
      row['comments'] = tmp['bugs'][id]['comments']
      rawList['bugs'][id] = row
      xDate = datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ")
      if xDate > searchDate:
        searchDate = xDate
      cnt += 1
      if cnt > 400:
        rawList['newest-entry'] = searchDate.strftime('%Y-%m-%d %H')
        util_dump_file(fileName, rawList)
        cnt = 0

    rawList['newest-entry'] = searchDate.strftime('%Y-%m-%d %H')
    util_dump_file(fileName, rawList)
    return rawList



def do_ESC_QA_STATS_UPDATE():
    tmp= util_load_url('https://bugs.documentfoundation.org/page.cgi?id=weekly-bug-summary.html', useRaw=True)

    rawList = {}

    startIndex = tmp.find('Total Reports: ') + 15
    stopIndex  = tmp.find(' ', startIndex)
    rawList['total'] = int(tmp[startIndex:stopIndex])
    startIndex = tmp.find('>', stopIndex) +1
    stopIndex = tmp.find('<', startIndex)
    rawList['opened'] = int(tmp[startIndex:stopIndex])
    startIndex = tmp.find('>', stopIndex + 5) +1
    stopIndex = tmp.find('<', startIndex)
    rawList['closed'] = int(tmp[startIndex:stopIndex])

    # outer loop, collect 3 Top 15 tables
    topNames = ['top15_modules', 'top15_closers', 'top15_reporters']
    curTopIndex = -1
    while True:
      startIndex = tmp.find('Top 15', startIndex+1)
      if startIndex == -1:
        break
      startIndex = tmp.find('</tr>', startIndex+1) + 5
      stopIndex = tmp.find('</table', startIndex+1)
      curTopIndex += 1
      rawList[topNames[curTopIndex]] = []

      # second loop, collect all lines <tr>..</tr>
      curLineIndex = -1
      while True:
        startIndex = tmp.find('<tr', startIndex)
        if startIndex == -1 or startIndex >= stopIndex:
          startIndex = stopIndex
          break
        stopLineIndex = tmp.find('</tr>', startIndex)
        curLineIndex += 1

        # third loop, collect single element
        curItemIndex = -1
        tmpList = []
        while True:
          startIndex = tmp.find('<td', startIndex)
          if startIndex == -1 or startIndex >= stopLineIndex:
            startIndex = stopLineIndex
            break
          while tmp[startIndex] == '<':
            tmpIndex = tmp.find('>', startIndex) + 1
            if tmp[startIndex+1] == 'a':
              i = tmp.find('bug_id=', startIndex) +7
              if -1 < i < tmpIndex:
                x = tmp[i:tmpIndex-2]
                tmpList.append(x)
            startIndex = tmpIndex
          stopCellIndex = tmp.find('<', startIndex)
          x = tmp[startIndex:stopCellIndex].replace('\n', '')
          if '0' <= x[0] <= '9' or x[0] == '+' or x[0] == '-':
            x = int(x)
          tmpList.append(x)
        if len(tmpList):
          if curTopIndex == 0:
              x = {'product': tmpList[0],
                   'open': tmpList[1],
                   'opened7DList': tmpList[2].split(','),
                   'opened7D': tmpList[3],
                   'closed7DList': tmpList[4].split(','),
                   'closed7D': tmpList[5],
                   'change': tmpList[6]}
          elif curTopIndex == 1:
              x = {'position': tmpList[0],
                   'who': tmpList[1],
                   'closedList' : tmpList[2].split(','),
                   'closed': tmpList[3]}
          else:
              x = {'position': tmpList[0],
                   'who': tmpList[1],
                   'reportedList' : tmpList[2].split(','),
                   'reported': tmpList[3]}
          rawList[topNames[curTopIndex]].append(x)
    return rawList



def do_ESC_MAB_UPDATE(bz):
    # load report from Bugzilla
    url = bz + '&f1=version&o1=regexp&priority=highest&v1=^'
    rawList = {}

    series = {'5.3' : '5.3',
              '5.2' : '5.2',
              '5.1' : '5.1',
              '5.0' : '5.0',
              '4.5' : '5.0',  # urgh
              '4.4' : '4.4',
              '4.3' : '4.3',
              '4.2' : '4.2',
              '4.1' : '4.1',
              '4.0' : '4.0',
              '3.6' : 'old',
              '3.5' : 'old',
              '3.4' : 'old',
              '3.3' : 'old',
              'Inherited from OOo' : 'old',
              'PreBibisect' : 'old',
              'unspecified' : 'old'
             }

    for key, id in series.items():
      if id not in rawList:
        rawList[id] = {'open': 0, 'total': 0}

      urlCall = url + key + '.*'
      tmpTotal = util_load_url(urlCall, useRaw=True)
      rawList[id]['total'] += len(tmpTotal.split('\n')) -1
      tmpOpen = util_load_url(urlCall + "&resolution=---", useRaw=True)
      rawList[id]['open'] += len(tmpOpen.split('\n')) - 1

    return rawList



def do_ESC_counting(bz, urlAdd):
    rawList = []
    tmp = util_load_url(bz + urlAdd, useRaw=True).split('\n')[1:]
    cnt = len(tmp)
    for line in tmp:
      rawList.append(line.split(',')[0])
    return cnt, rawList



def get_esc_bugzilla(cfg):
    fileName = cfg['homedir'] + 'dump/bugzilla_esc_dump.json'

    print("Updating ESC bugzilla dump")

    rawList = {'ESC_QA_STATS_UPDATE': {},
               'ESC_MAB_UPDATE': {},
               'ESC_BISECTED_UPDATE': {},
               'ESC_BIBISECTED_UPDATE': {},
               'ESC_COMPONENT_UPDATE': {'all': {}, 'high': {}, 'os': {}},
               'ESC_REGRESSION_UPDATE': {}}

    bz = 'https://bugs.documentfoundation.org/buglist.cgi?' \
         'product=LibreOffice' \
         '&keywords_type=allwords' \
         '&query_format=advanced' \
         '&limit=0' \
         '&ctype=csv' \
         '&human=1'

    rawList['ESC_QA_STATS_UPDATE'] = do_ESC_QA_STATS_UPDATE()
    rawList['ESC_MAB_UPDATE'] = do_ESC_MAB_UPDATE(bz)

    urlBi = '&keywords=bisected%2C'
    url = '&order=tag DESC%2Cchangeddate DESC%2Cversion DESC%2Cpriority%2Cbug_severity'
    rawList['ESC_BISECTED_UPDATE']['total'], \
    rawList['ESC_BISECTED_UPDATE']['total_list'] = do_ESC_counting(bz, urlBi+url)
    url = '&bug_status=UNCONFIRMED' \
          '&bug_status=NEW' \
          '&bug_status=ASSIGNED' \
          '&bug_status=REOPENED' \
          '&resolution=---'
    rawList['ESC_BISECTED_UPDATE']['open'], \
    rawList['ESC_BISECTED_UPDATE']['open_list'] = do_ESC_counting(bz, urlBi + url)

    url = '&f2=status_whiteboard' \
          '&f3=OP' \
          '&f4=keywords' \
          '&f5=status_whiteboard' \
          '&j3=OR' \
          '&known_name=BibisectedAll' \
          '&n2=1' \
          '&o1=substring' \
          '&o2=substring' \
          '&o4=substring' \
          '&o5=substring' \
          '&order=changeddate DESC%2Cop_sys%2Cbug_status%2Cpriority%2Cassigned_to%2Cbug_id' \
          '&resolution=---' \
          '&resolution=FIXED' \
          '&resolution=INVALID' \
          '&resolution=WONTFIX' \
          '&resolution=DUPLICATE' \
          '&resolution=WORKSFORME' \
          '&resolution=MOVED' \
          '&resolution=NOTABUG' \
          '&resolution=NOTOURBUG' \
          '&v1=bibisected' \
          '&v2=bibisected35older' \
          '&v4=bibisected' \
          '&v5=bibisected'
    rawList['ESC_BIBISECTED_UPDATE']['total'], \
    rawList['ESC_BIBISECTED_UPDATE']['total_list'] = do_ESC_counting(bz, url)
    url = '&f2=status_whiteboard' \
          '&f3=OP' \
          '&f4=keywords' \
          '&f5=status_whiteboard' \
          '&j3=OR' \
          '&known_name=Bibisected' \
          '&n2=1' \
          '&o1=substring' \
          '&o2=substring' \
          '&o4=substring' \
          '&o5=substring' \
          '&query_based_on=Bibisected' \
          '&resolution=---' \
          '&v1=bibisected' \
          '&v2=bibisected35older' \
          '&v4=bibisected' \
          '&v5=bibisected'
    rawList['ESC_BIBISECTED_UPDATE']['open'], \
    rawList['ESC_BIBISECTED_UPDATE']['open_list'] = do_ESC_counting(bz, url)

    url = 'columnlist=bug_severity%2Cpriority%2Ccomponent%2Cop_sys%2Cassigned_to%2Cbug_status%2Cresolution%2Cshort_desc' \
          '&keywords=regression%2C%20' \
          '&order=bug_id'
    rawList['ESC_REGRESSION_UPDATE']['total'], \
    rawList['ESC_REGRESSION_UPDATE']['total_list']  = do_ESC_counting(bz, url)
    url = '&keywords=regression%2C%20' \
          '&columnlist=bug_severity%2Cpriority%2Ccomponent%2Cop_sys%2Cassigned_to%2Cbug_status%2Cresolution%2Cshort_desc' \
          '&resolution=---' \
          '&query_based_on=Regressions' \
          '&known_name=Regressions'
    rawList['ESC_REGRESSION_UPDATE']['open'], \
    rawList['ESC_REGRESSION_UPDATE']['open_list'] = do_ESC_counting(bz, url)
    url = url + '&bug_severity=blocker' \
                '&bug_severity=critical' \
                '&bug_status=NEW' \
                '&bug_status=ASSIGNED' \
                '&bug_status=REOPENED'
    rawList['ESC_REGRESSION_UPDATE']['high'], \
    rawList['ESC_REGRESSION_UPDATE']['high_list'] = do_ESC_counting(bz, url)

    rawList['ESC_COMPONENT_UPDATE']['all']['Crashes'] = {}
    url = '&keywords=regression' \
          '&short_desc=crash' \
          '&query_based_on=CrashRegressions' \
          '&bug_status=UNCONFIRMED' \
          '&bug_status=NEW' \
          '&bug_status=ASSIGNED' \
          '&bug_status=REOPENED' \
          '&bug_status=NEEDINFO' \
          '&short_desc_type=allwordssubstr' \
          '&known_name=CrashRegressions'
    rawList['ESC_COMPONENT_UPDATE']['all']['Crashes']['count'], \
    rawList['ESC_COMPONENT_UPDATE']['all']['Crashes']['list'] = do_ESC_counting(bz, url)
    rawList['ESC_COMPONENT_UPDATE']['all']['Borders'] = {}
    url = '&keywords=regression' \
          '&short_desc=border' \
          '&query_based_on=BorderRegressions' \
          '&bug_status=UNCONFIRMED' \
          '&bug_status=NEW' \
          '&bug_status=ASSIGNED' \
          '&bug_status=REOPENED' \
          '&bug_status=NEEDINFO' \
          '&short_desc_type=allwordssubstr' \
          '&known_name=BorderRegressions'
    rawList['ESC_COMPONENT_UPDATE']['all']['Borders']['count'], \
    rawList['ESC_COMPONENT_UPDATE']['all']['Borders']['list'] = do_ESC_counting(bz, url)
    rawList['ESC_COMPONENT_UPDATE']['all']['Writer: docx filter'] = {}
    url = '&bug_status=NEW' \
          '&bug_status=ASSIGNED' \
          '&bug_status=REOPENED' \
          '&bug_status=PLEASETEST' \
          '&component=Writer' \
          '&keywords=regression%2C filter%3Adocx%2C '
    rawList['ESC_COMPONENT_UPDATE']['all']['Writer: docx filter']['count'], \
    rawList['ESC_COMPONENT_UPDATE']['all']['Writer: docx filter']['list'] = do_ESC_counting(bz, url)
    rawList['ESC_COMPONENT_UPDATE']['all']['Writer: doc filter'] = {}
    url = '&bug_status=NEW' \
          '&bug_status=ASSIGNED' \
          '&bug_status=REOPENED' \
          '&bug_status=PLEASETEST' \
          '&component=Writer' \
          '&keywords=regression%2C filter%3Adoc%2C '
    rawList['ESC_COMPONENT_UPDATE']['all']['Writer: doc filter']['count'], \
    rawList['ESC_COMPONENT_UPDATE']['all']['Writer: doc filter']['list'] = do_ESC_counting(bz, url)
    rawList['ESC_COMPONENT_UPDATE']['all']['Writer: other filter'] = {}
    url = '&bug_status=NEW' \
          '&bug_status=ASSIGNED' \
          '&bug_status=REOPENED' \
          '&bug_status=PLEASETEST' \
          '&component=Writer' \
          '&f1=keywords' \
          '&f2=keywords' \
          '&keywords=regression%2C' \
          '&o1=nowords' \
          '&o2=substring' \
          '&v1=filter%3Adocx%2C filter%3Adoc' \
          '&v2=filter%3A'
    rawList['ESC_COMPONENT_UPDATE']['all']['Writer: other filter']['count'], \
    rawList['ESC_COMPONENT_UPDATE']['all']['Writer: other filter']['list'] = do_ESC_counting(bz, url)
    rawList['ESC_COMPONENT_UPDATE']['all']['Writer: perf'] = {}
    url = '&bug_status=NEW' \
          '&bug_status=ASSIGNED' \
          '&bug_status=REOPENED' \
          '&bug_status=PLEASETEST' \
          '&component=Writer' \
          '&keywords=regression%2C perf%2C '
    rawList['ESC_COMPONENT_UPDATE']['all']['Writer: perf']['count'], \
    rawList['ESC_COMPONENT_UPDATE']['all']['Writer: perf']['list'] = do_ESC_counting(bz, url)
    rawList['ESC_COMPONENT_UPDATE']['all']['Writer: other'] = {}
    url = '&bug_status=NEW' \
          '&bug_status=ASSIGNED' \
          '&bug_status=REOPENED' \
          '&bug_status=PLEASETEST' \
          '&component=Writer' \
          '&f1=keywords' \
          '&keywords=regression%2C' \
          '&o1=nowordssubstr' \
          '&v1=filter%3A%2C perf'
    rawList['ESC_COMPONENT_UPDATE']['all']['Writer: other']['count'], \
    rawList['ESC_COMPONENT_UPDATE']['all']['Writer: other']['list'] = do_ESC_counting(bz, url)

    for comp in ['Calc', 'Impress', 'Base', 'Draw', 'LibreOffice', 'Writer', 'BASIC', 'Chart', 'Extensions',
                 'Formula Editor', 'Impress Remote', 'Installation', 'Linguistic', 'Printing and PDF export',
                 'UI', 'filters and storage', 'framework', 'graphics stack', 'sdk']:
      compUrl = comp
      url = '&keywords=regression' \
            '&bug_status=NEW' \
            '&bug_status=ASSIGNED' \
            '&bug_status=REOPENED' \
            '&bug_status=PLEASETEST' \
            '&component=' + compUrl
      rawList['ESC_COMPONENT_UPDATE']['all'][comp] = {}
      rawList['ESC_COMPONENT_UPDATE']['all'][comp]['count'], \
      rawList['ESC_COMPONENT_UPDATE']['all'][comp]['list'] = do_ESC_counting(bz, url)
      url = url + '&bug_severity=blocker' \
                  '&bug_severity=critical'
      rawList['ESC_COMPONENT_UPDATE']['high'][comp] = {}
      rawList['ESC_COMPONENT_UPDATE']['high'][comp]['count'], \
      rawList['ESC_COMPONENT_UPDATE']['high'][comp]['list'] = do_ESC_counting(bz, url)

    for os in ['Linux (All)', 'Windows (All)', 'Mac OS X (All)', 'All']:
        url = '&keywords=regression' \
              '&bug_status=NEW' \
              '&bug_status=ASSIGNED' \
              '&bug_status=REOPENED' \
              '&bug_status=PLEASETEST' \
              '&bug_severity=blocker' \
              '&bug_severity=critical' \
              '&op_sys=' + os
        rawList['ESC_COMPONENT_UPDATE']['os'][os] = {}
        rawList['ESC_COMPONENT_UPDATE']['os'][os]['count'], \
        rawList['ESC_COMPONENT_UPDATE']['os'][os]['list'] = do_ESC_counting(bz, url)

    url = '&bug_status=UNCONFIRMED' \
          '&bug_status=NEW' \
          '&bug_status=ASSIGNED' \
          '&bug_status=REOPENED' \
          '&chfield=priority' \
          '&chfieldfrom=-8d' \
          '&chfieldto=Now' \
          '&chfieldvalue=highest' \
          '&priority=highest' \
          '&resolution=---'
    rawList['MostPressingBugs'] = {'open': {}, 'closed': {}}
    rawList['MostPressingBugs']['open']['count'], \
    rawList['MostPressingBugs']['open']['list'] = do_ESC_counting(bz, url)
    url = '&bug_status=RESOLVED' \
          '&bug_status=VERIFIED' \
          '&bug_status=CLOSED' \
          '&chfield=priority' \
          '&chfieldfrom=-8d' \
          '&chfieldto=Now' \
          '&chfieldvalue=highest' \
          '&priority=highest' \
          '&resolution=---'
    rawList['MostPressingBugs']['closed']['count'], \
    rawList['MostPressingBugs']['closed']['list'] = do_ESC_counting(bz, url)

    util_dump_file(fileName, rawList)
    return rawList



def get_gerrit(cfg):
    fileName = cfg['homedir'] + 'dump/gerrit_dump.json'
    searchDate, rawList = util_load_data_file(cfg, fileName, 'gerrit', {'patch': {}, 'committers' : []})
    print("Updating gerrit dump from " + rawList['newest-entry'])

    urlBase = 'https://gerrit.libreoffice.org/a/'
    uid = cfg['gerrit']['user']
    upw = cfg['gerrit']['password']
    rawList['committers'] = []
    tmp = util_load_url(urlBase + 'groups/Committers/members', uUser=uid, uPass=upw)
    for row in tmp:
      for i in 'username', 'email':
        if not i in row:
          row[i] = '*dummy*'
      rawList['committers'].append(row)

    url = urlBase + 'changes/?q=after:' + searchDate.strftime("%Y-%m-%d") + \
         '&o=DETAILED_LABELS&o=DETAILED_ACCOUNTS&o=MESSAGES&limit=200&start='
    offset = 0
    if 'offset' in rawList:
      offset = int(rawList['offset'])
    while True:
      tmp = util_load_url(url + str(offset), uUser=uid, uPass=upw)
      for row in tmp:
        for i in 'email', 'username', 'name':
          if not i in row['owner']:
            row['owner'][i] = '*dummy*'
        for x in row['messages']:
          if not 'author' in x:
            x['author'] = {}
          for i in 'email', 'username', 'name':
            if not i in x['author']:
              x['author'][i] = '*dummy*'
        for i in 'Verified', 'Code-Review':
          if not i in row['labels']:
            row['labels'][i] = {}
          if not 'all' in row['labels'][i]:
            row['labels'][i]['all'] = []
          for x in row['labels'][i]['all']:
            if 'name' not in x:
              x['name'] = '*dummy*'
            if 'email' not in x:
              x['email'] = '*dummy*'
            if 'username' not in x:
              x['username'] = '*dummy*'
            if 'value' not in x:
              x['value'] = 0

        rawList['patch'][str(row['_number'])] = row
        xDate = datetime.datetime.strptime(row['updated'], "%Y-%m-%d %H:%M:%S.%f000")
        if xDate > searchDate:
          searchDate = xDate
      if '_more_changes' in tmp[-1] and tmp[-1]['_more_changes'] == True:
        rawList['offset'] = offset
        offset += len(tmp)
        del rawList['patch'][str(row['_number'])]['_more_changes']
      else:
        break
    if 'offset' in rawList:
      del rawList['offset']

    rawList['newest-entry'] = searchDate.strftime('%Y-%m-%d %H')
    util_dump_file(fileName, rawList)
    return rawList



def get_git(cfg):
    fileName = cfg['homedir'] + 'dump/git_dump.json'
    searchDate, rawList = util_load_data_file(cfg, fileName, 'git', {'commits': {}})
    print("Updating git dump from " + rawList['newest-entry'])

    for repo in cfg['git']['repos']:
      print(' working on ' + repo['name'])
      useFormat = '{"hash": "%H", "date": "%ci", "author": "%an", "author-email": "%ae", ' \
                  '"committer": "%cn", "committer-email": "%ce" }'
      basedir = cfg['homedir'] + '../libreoffice/'
      if repo['git'] and cfg['platform'] == 'linux':
        os.system('(cd ' + basedir + repo['dir'] + ';git pull -r;git fetch --all) > /dev/null')
      os.system('(cd ' + basedir + repo['dir'] + ";git log --pretty=format:'" + useFormat + "') > /tmp/git.log")
      fp = open('/tmp/git.log', encoding='utf-8')
      while True:
        x = fp.readline()
        if x is None or x == '':
          break
        row = json.loads(x)
        row['repo'] = repo['name']
        key = repo['name'] + '_' + row['hash']
        if not key in rawList['commits']:
          row['date'] = row['date'][:-6]
          rawList['commits'][key] = row
        x = row['date'].split(' ')[:2]
        xDate = datetime.datetime.strptime(x[0]+' '+x[1], "%Y-%m-%d %H:%M:%S")
        if xDate < searchDate:
          break

    nDate = searchDate
    for key in rawList['commits']:
      xDate = datetime.datetime.strptime(rawList['commits'][key]['date'], "%Y-%m-%d %H:%M:%S")
      if xDate > nDate:
        nDate = xDate

    rawList['newest-entry'] = nDate.strftime('%Y-%m-%d %H')
    util_dump_file(fileName, rawList)
    return rawList



def get_crash(cfg):
    fileName = cfg['homedir'] + 'dump/crash_dump.json'
    searchDate, rawList = util_load_data_file(cfg, fileName, 'crash', {'crashtest': {}, 'crashreport': {}})

    print("Updating crashtest dump from " + rawList['newest-entry'])
    dirList = util_load_url('http://dev-builds.libreoffice.org/crashtest/?C=M;O=D', useRaw=True)
    inx = dirList.find('alt="[DIR]"', 0)
    if inx == -1:
       print("ERROR: http://dev-builds.libreoffice.org/crashtest/?C=M;O=D not showing DIR list")
       return
    inx = dirList.find('alt="[DIR]"', inx+8)
    inx = dirList.find('href="', inx) +6
    end = dirList.find('"', inx)
    url = 'http://dev-builds.libreoffice.org/crashtest/' + dirList[inx:end]

    for type in 'exportCrashes', 'importCrash', 'validationErrors':
        tmp = util_load_url(url + type + '.csv', useRaw=True).replace('\r', '').split('\n')
        csv = []
        for line in tmp:
            csv.append(line.split(','))
        for line in csv[1:]:
            for inx, item in enumerate(line):
                if item == '':
                   line[inx] = 0
                else:
                   line[inx] = int(item)
        rawList['crashtest'][type] = {}
        rawList['crashtest'][type]['title'] = csv[0]
        rawList['crashtest'][type]['data'] = csv[1:]

    print("Updating crashreport dump from " + rawList['newest-entry'])
    print(".....talk with moggi, about REST API")


    rawList['newest-entry'] = datetime.datetime.now().strftime('%Y-%m-%d %H')
    util_dump_file(fileName, rawList)
    return rawList



def runCfg(platform):
    if 'esc_homedir' in os.environ:
      homeDir = os.environ['esc_homedir']
    else:
      homeDir = '/home/esc-mentoring/esc'

    cfg = util_load_file(homeDir + '/config.json')
    if cfg == None:
        exit(-1)
    keys = util_load_file(homeDir + '/config_collect.json')
    if keys == None:
        exit(-1)

    cfg.update(keys)
    cfg['homedir'] = homeDir + '/'
    cfg['platform'] = platform
    print("Reading and writing data to " + cfg['homedir'])
    return cfg



def runBuild(cfg):
    try:
      crashData = get_crash(cfg)
    except:
      pass
    try:
      openhubData = get_openhub(cfg)
    except:
      pass
    try:
      bugzillaData = get_bugzilla(cfg)
    except:
      pass
    try:
      ESCData = get_esc_bugzilla(cfg)
    except:
      pass
    try:
      gerritData = get_gerrit(cfg)
    except:
      pass
    try:
      gitData = get_git(cfg)
    except:
      pass



if __name__ == '__main__':
    runBuild(runCfg(sys.platform))
