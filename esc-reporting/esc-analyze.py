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
# This program uses data collected by esc-collect.py:
# The data is dumped to json files, with a history of minimum 1 year
#     esc/dump/['openhub','bugzilla','gerrit','git']_dump.json
#
# it generates and maintains
#      esc/stats.json (the daily data)
#      esc/archive/stats_YYYY_MM_DD.json (copy of stats.json)
#      esc/weeks/week_YYYY_NN.json (thursday copy of stats.json)
#
# The analyze functions run through the data files and generates interesting numbers
# You can add your own analyze function (see analyze_myfunc() for example).
# The numbers are stored in stats.json, and a diff with last weeks numbers are automatically build
#
# dump/developers_dump.json is used to identify:
#   new contributors
#   contributors missing licensek
#   contributor award scheme
#   cross reference emails (several people uses multiple emails, there is a function to control that)
#
# Expand this program if you want to present numbers compared to last week (for e.g. the ESC meeting)
#
# By storing the data over time:
#      archive/  contains ca. 1 month
#      weeks/    contains ca. 1 year
# it is possible to make trend analysis, this is however not part of this program
#
# Installed on vm174:/usr/local/bin runs every night (generating esc/stats.json)
#
# This program is intended to be extended by people interesting in performance numbers
#



import sys
import csv
import io
import os
import operator
import datetime
import json
import xmltodict


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


def util_load_csv(fileName, split):
    global statList
    rawData = {}
    with open(fileName, 'r', encoding='utf-8') as fp:
      fp.readline()
      fp.readline()
      for line in fp:
        line = line[:-1]
        if len(line) == 0:
          continue
        x = line.split(split)
        if split == ';' and len(x) != 3:
          raise Exception('misformed entry ' + line + ' in filename ' + fileName)
        if split == ' ' and len(x) != 2:
          y = line.split('"')
          if len(y) != 3:
            raise Exception('misformed entry ' + line + ' in filename ' + fileName)
          x[0] = y[1]
          x[1] = y[2].split()[0]
          del x[2:]

        if x[0] in rawData:
          raise Exception('duplicate entry ' + x[0] + ' in filename ' + fileName)
        elif len(x) == 3:
          rawData[x[0]] = {'name': x[1], 'license': x[2]}
        else:
          rawData[x[0]] = x[1]
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



def util_build_period_stat(xDate, email, base, peopleTarget=None, dataTarget=None):
    global cfg, statList

    xType = 'contributor'
    if email:
      statList['people'][email][base]['total'] += 1
      if statList['people'][email]['isCommitter'] and base != 'ui':
        xType = 'committer'
    if dataTarget:
      statList['data'][base][xType]['total'] += 1

    for i in '1year', '3month', '1month', '1week':
      if xDate >= cfg[i + 'Date']:
        if peopleTarget:
          statList['people'][email][base][i][peopleTarget] += 1
        if dataTarget:
          statList['data'][base][xType][i][dataTarget] += 1



def util_load_data_file(fileName):
    rawList = util_load_file(fileName)
    if rawList == None:
      exit(-1)
    return rawList



def util_create_person_gerrit(person, email):
    return { 'name': person,
             'email': email,
             'commits': {'1year':  {'owner': 0, 'reviewMerged': 0},
                         '3month': {'owner': 0, 'reviewMerged': 0},
                         '1month': {'owner': 0, 'reviewMerged': 0},
                         '1week':  {'owner': 0, 'reviewMerged': 0},
                         'total':  0},
             'gerrit':  {'1year':  {'owner': 0, 'reviewer': 0},
                         '3month': {'owner': 0, 'reviewer': 0},
                         '1month': {'owner': 0, 'reviewer': 0},
                         '1week':  {'owner': 0, 'reviewer': 0},
                         'total':  0,
                         'userName': '*DUMMY*'},
             'ui':      {'1year':  {'commented': 0, 'history': 0},
                         '3month': {'commented': 0, 'history': 0},
                         '1month': {'commented': 0, 'history': 0},
                         '1week':  {'commented': 0, 'history': 0},
                         'total':  0},
             'qa': {'1year':  {'owner': 0, 'reviewer': 0, 'regression': 0, 'bibisected': 0,
                               'bisected': 0, 'backtrace': 0, 'fixed': 0, 'total': 0},
                    '3month': {'owner': 0, 'reviewer': 0, 'regression': 0, 'bibisected': 0,
                               'bisected': 0, 'backtrace': 0, 'fixed': 0, 'total': 0},
                    '1month': {'owner': 0, 'reviewer': 0, 'regression': 0, 'bibisected': 0,
                               'bisected': 0, 'backtrace': 0, 'fixed': 0, 'total': 0},
                    '1week':  {'owner': 0, 'reviewer': 0, 'regression': 0, 'bibisected': 0,
                               'bisected': 0, 'backtrace': 0, 'fixed': 0, 'total': 0},
                    'total': 0},
             'isCommitter': False,
             'isContributor': False,
             'licenseOK': False,
             'licenseText': '',
             'newestCommit' : datetime.datetime(2001, 1, 1),
             'prevCommit':  datetime.datetime(2001, 1, 1)}



def util_create_statList():
    return {'data': {'commits': {'committer':   {'1year':  {'owner': 0, 'reviewMerged': 0},
                                                 '3month': {'owner': 0, 'reviewMerged': 0},
                                                 '1month': {'owner': 0, 'reviewMerged': 0},
                                                 '1week':  {'owner': 0, 'reviewMerged': 0},
                                                 'total':  0},
                                 'contributor': {'1year':  {'owner': 0, 'reviewMerged': 0},
                                                 '3month': {'owner': 0, 'reviewMerged': 0},
                                                 '1month': {'owner': 0, 'reviewMerged': 0},
                                                 '1week':  {'owner': 0, 'reviewMerged': 0},
                                                 'total':  0}},
                     'openhub': {'lines_of_code': 0,
                                 'total_commits': 0,
                                 'total_contributors': 0,
                                 'year_commits': 0,
                                 'year_contributors': 0},
                     'gerrit': {'contributor': {'1year':  {'ABANDONED': 0, 'MERGED': 0, 'NEW': 0, 'reviewed': 0},
                                                '3month': {'ABANDONED': 0, 'MERGED': 0, 'NEW': 0, 'reviewed': 0},
                                                '1month': {'ABANDONED': 0, 'MERGED': 0, 'NEW': 0, 'reviewed': 0},
                                                '1week':  {'ABANDONED': 0, 'MERGED': 0, 'NEW': 0, 'reviewed': 0},
                                                'total': 0},
                                'committer': {'1year':  {'ABANDONED': 0, 'MERGED': 0, 'NEW': 0, 'reviewed': 0},
                                              '3month': {'ABANDONED': 0, 'MERGED': 0, 'NEW': 0, 'reviewed': 0},
                                              '1month': {'ABANDONED': 0, 'MERGED': 0, 'NEW': 0, 'reviewed': 0},
                                              '1week':  {'ABANDONED': 0, 'MERGED': 0, 'NEW': 0, 'reviewed': 0},
                                              'total': 0}},
                     'trend' : {'committer':   {'owner':        {'1year': {}, '3month': {}, '1month': {}, '1week': {}},
                                                'reviewMerged': {'1year': {}, '3month': {}, '1month': {}, '1week': {}}},
                                'contributor': {'owner':        {'1year': {}, '3month': {}, '1month': {}, '1week': {}},
                                                'reviewMerged': {'1year': {}, '3month': {}, '1month': {}, '1week': {}}},
                                'ui':          {'commented':    {'1year': {}, '3month': {}, '1month': {}, '1week': {}},
                                                'history':      {'1year': {}, '3month': {}, '1month': {}, '1week': {}}}},
                     'ui': {'contributor': {'1year':  {'added': 0, 'removed': 0, 'commented': 0, 'resolved': 0},
                                            '3month': {'added': 0, 'removed': 0, 'commented': 0, 'resolved': 0},
                                            '1month': {'added': 0, 'removed': 0, 'commented': 0, 'resolved': 0},
                                            '1week':  {'added': 0, 'removed': 0, 'commented': 0, 'resolved': 0},
                                            'total': 0},
                            'needsUXEval' : 0,
                            'topicUI': 0},
                     'qa': {'unconfirmed': {'count': 0, 'enhancement': 0, 'needsUXEval': 0,
                                            'haveBacktrace': 0, 'needsDevAdvice': 0}},
                     'easyhacks' : {'needsDevEval': 0,  'needsUXEval': 0, 'cleanup_comments': 0,
                                    'total': 0,         'assigned': 0,    'open': 0}},
                     'stat': {'openhub_last_analyse': "2001-01-01"},
                     'people': {}}




def util_check_mail(name, mail):
    global statList

    if mail in statList['aliases']:
      mail = statList['aliases'][mail]
    if not mail in statList['people']:
      statList['people'][mail] = util_create_person_gerrit(name, mail)
      if mail == '*DUMMY*':
        statList['people'][mail]['licenseOK'] = True
    else:
      if name and name != '*UNKNOWN*' and statList['people'][mail]['name'] == '*UNKNOWN*':
        statList['people'][mail]['name'] = name
    return mail



def util_build_diff(newList, oldList):
    result = {}
    for i in newList:
      if not i in oldList:
        oldList[i] = newList[i]
      if type(newList[i]) is dict:
        if not type(oldList[i]) is dict:
          result[i] = 0
        else:
          result[i] = util_build_diff(newList[i], oldList[i])
      else:
          result[i] = newList[i] - oldList[i]
    return result



def analyze_mentoring():
    global cfg, statList, openhubData, bugzillaData, gerritData, gitData

    print("mentoring: analyze openhub", end="", flush=True)
    statList['data']['openhub']['lines_of_code'] = int(openhubData['project']['analysis']['total_code_lines'])
    statList['data']['openhub']['total_commits'] = int(openhubData['project']['analysis']['total_commit_count'])
    statList['data']['openhub']['total_contributors'] = int(openhubData['project']['analysis']['total_contributor_count'])
    statList['data']['openhub']['year_commits'] = int(openhubData['project']['analysis']['twelve_month_commit_count'])
    statList['data']['openhub']['year_contributors'] = int(openhubData['project']['analysis']['twelve_month_contributor_count'])
    xDate = datetime.datetime.strptime(openhubData['project']['analysis']['updated_at'], "%Y-%m-%dT%H:%M:%SZ")
    statList['stat']['openhub_last_analyse'] = xDate.strftime('%Y-%m-%d')

    print(" to " + statList['stat']['openhub_last_analyse'])
    print("mentoring: analyze gerrit", end="", flush=True)

    for row in gerritData['committers']:
      mail = util_check_mail(row['name'], row['email'])
      statList['people'][mail]['gerrit']['userName'] = row['username']
      statList['people'][mail]['isCommitter'] = True
      statList['people'][mail]['isContributor'] = True

    statNewDate = cfg['1yearDate']
    statOldDate = cfg['nowDate']
    for key, row in gerritData['patch'].items():
      xDate = datetime.datetime.strptime(row['updated'], '%Y-%m-%d %H:%M:%S.%f000')
      if xDate > cfg['cutDate']:
        continue
      if xDate < statOldDate:
        statOldDate = xDate
      if xDate > statNewDate:
        statNewDate = xDate
      if row['status'] == 'SUBMITTED' or row['status'] == 'DRAFT':
        row['status'] = 'NEW'
      ownerEmail = util_check_mail(row['owner']['name'], row['owner']['email'])
      statList['people'][ownerEmail]['gerrit']['userName'] = row['owner']['username']
      statList['people'][ownerEmail]['isContributor'] = True
      util_build_period_stat(xDate, ownerEmail, 'gerrit', dataTarget=row['status'], peopleTarget='owner')

      for i in 'Verified', 'Code-Review':
        for x in row['labels'][i]['all']:
          xEmail = util_check_mail(x['name'], x['email'])
          if xEmail != ownerEmail:
            util_build_period_stat(xDate, xEmail, 'gerrit', dataTarget='reviewed', peopleTarget='reviewer')

    print(" from " + statOldDate.strftime('%Y-%m-%d') + " to " + statNewDate.strftime('%Y-%m-%d'))
    print("mentoring: analyze git", end="", flush=True)

    statNewDate = cfg['1yearDate']
    statOldDate = cfg['nowDate']
    for key, row in gitData['commits'].items():
      xDate = datetime.datetime.strptime(row['date'], "%Y-%m-%d %H:%M:%S")
      if xDate > cfg['cutDate']:
        continue
      if xDate < statOldDate:
        statOldDate = xDate
      if xDate > statNewDate:
        statNewDate = xDate
      author = util_check_mail(row['author'], row['author-email'])
      committer = util_check_mail(row['committer'], row['committer-email'])
      statList['people'][author]['isContributor'] = True
      statList['people'][committer]['isContributor'] = True
      statList['people'][committer]['isCommitter'] = True

      for i in author, committer:
        if xDate > statList['people'][i]['newestCommit']:
          if statList['people'][i]['newestCommit'] > statList['people'][i]['prevCommit']:
            statList['people'][i]['prevCommit'] = statList['people'][i]['newestCommit']
          statList['people'][i]['newestCommit'] = xDate
        elif xDate > statList['people'][i]['prevCommit']:
          statList['people'][i]['prevCommit'] = xDate
      util_build_period_stat(xDate, author, 'commits', dataTarget='owner', peopleTarget='owner')
      if author != committer:
        util_build_period_stat(xDate, committer, 'commits', dataTarget='reviewMerged', peopleTarget='reviewMerged')

    print(" from " + statOldDate.strftime("%Y-%m-%d") + " to " + statNewDate.strftime("%Y-%m-%d"))
    print("mentoring: analyze easyhacks", end="", flush=True)

    statNewDate = cfg['1yearDate']
    statOldDate = cfg['nowDate']
    for key, row in bugzillaData['bugs'].items():
      if row['status'] == 'RESOLVED' or row['status'] == 'VERIFIED' or not 'easyHack' in row['keywords']:
        continue

      xDate = datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ")
      if xDate > cfg['cutDate']:
        continue
      if xDate < statOldDate:
        statOldDate = xDate
      if xDate > statNewDate:
        statNewDate = xDate

      statList['data']['easyhacks']['total'] += 1
      bugBlocked = False
      if 'needsDevEval' in row['keywords']:
        statList['data']['easyhacks']['needsDevEval'] += 1
        bugBlocked = True
      if 'needsUXEval' in row['keywords']:
        statList['data']['easyhacks']['needsUXEval'] += 1
        bugBlocked = True

      if row['status'] == 'NEEDINFO':
        bugBlocked = True
      elif row['status'] == 'ASSIGNED':
        statList['data']['easyhacks']['assigned'] += 1
      elif row['status'] == 'NEW' and not bugBlocked:
        statList['data']['easyhacks']['open'] += 1

      if len(row['comments']) >= 5:
        statList['data']['easyhacks']['cleanup_comments'] += 1

    print(" from " + statOldDate.strftime("%Y-%m-%d") + " to " + statNewDate.strftime("%Y-%m-%d"))



def analyze_ui():
    global cfg, statList, bugzillaData

    print("ui: analyze bugzilla", flush=True)

    for key, row in bugzillaData['bugs'].items():
      xDate = datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ")
      if xDate > cfg['cutDate']:
        continue

      if not 'topicUI' in row['keywords'] and not 'needsUXEval' in row['keywords']:
        continue

      for change in row['comments']:
        email = util_check_mail('*UNKNOWN*', change['creator'])
        xDate = datetime.datetime.strptime(change['creation_time'], "%Y-%m-%dT%H:%M:%SZ")
        util_build_period_stat(xDate, email, 'ui', dataTarget='commented', peopleTarget='commented')

      for change in row['history']:
        email = util_check_mail('*UNKNOWN*', change['who'])
        xDate = datetime.datetime.strptime(change['when'], "%Y-%m-%dT%H:%M:%SZ")
        for entry in change['changes']:
          util_build_period_stat(xDate, email, 'ui', peopleTarget='history')

      if row['status'] == 'RESOLVED' or row['status'] == 'CLOSED' or row['status'] == 'VERIFIED':
        util_build_period_stat(xDate, None, 'ui', dataTarget='resolved')
        continue

      if 'needsUXEval' in row['keywords']:
        statList['data']['ui']['needsUXEval'] += 1

      if 'topicUI' in row['keywords']:
        statList['data']['ui']['topicUI'] += 1

      for change in row['history']:
        email = util_check_mail('*UNKNOWN*', change['who'])
        xDate = datetime.datetime.strptime(change['when'], "%Y-%m-%dT%H:%M:%SZ")
        for entry in change['changes']:
          if 'needsUXEval' in entry['added']:
            util_build_period_stat(xDate, email, 'ui', dataTarget='added')
          if 'needsUXEval' in entry['removed']:
            util_build_period_stat(xDate, email, 'ui', dataTarget='removed')



def analyze_qa():
    global cfg, statList, bugzillaData

    print("qa: analyze bugzilla", flush=True)

    for key, row in bugzillaData['bugs'].items():
	    #Ignore META bugs and deletionrequest bugs.
      if not row['summary'].startswith('[META]') \
		      and row['component'] != 'deletionrequest':
        email = util_check_mail(row['creator_detail']['real_name'], row['creator'])
        xDate = datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ")
        creationDate = datetime.datetime.strptime(row['creation_time'], "%Y-%m-%dT%H:%M:%SZ")

        if row['status'] == 'UNCONFIRMED':
          statList['data']['qa']['unconfirmed']['count'] += 1
          if 'needsUXEval' in row['keywords']:
            statList['data']['qa']['unconfirmed']['needsUXEval'] += 1
          if 'needsDevAdvice' in row['keywords']:
            statList['data']['qa']['unconfirmed']['needsDevAdvice'] += 1
          if 'haveBacktrace' in row['keywords']:
            statList['data']['qa']['unconfirmed']['haveBacktrace'] += 1
          if row['severity'] == 'enhancement':
            statList['data']['qa']['unconfirmed']['enhancement'] += 1

        util_build_period_stat(creationDate, email, 'qa', 'owner')

        for change in row['history']:
          email = util_check_mail('*UNKNOWN*', change['who'])
          xDate = datetime.datetime.strptime(change['when'], "%Y-%m-%dT%H:%M:%SZ")
          for entry in change['changes']:
            if entry['field_name'] == 'keywords':
              keywordsAdded = entry['added'].split(", ")
              for keyword in keywordsAdded:
                if keyword == 'bisected' and 'bisected' in row['keywords']:
                  util_build_period_stat(xDate, email, 'qa', 'bisected')
                if keyword == 'bibisected' and 'bibisected' in row['keywords']:
                  util_build_period_stat(xDate, email, 'qa', 'bibisected')
                if keyword == 'regression' and 'regression' in row['keywords']:
                  util_build_period_stat(xDate, email, 'qa', 'regression')
                if keyword == 'haveBacktrace' and 'haveBacktrace' in row['keywords']:
                  util_build_period_stat(xDate, email, 'qa', 'backtrace')
            elif entry['field_name'] == 'resolution':
              if entry['added'] == 'FIXED' and row['resolution'] == 'FIXED':
                util_build_period_stat(xDate, email, 'qa', 'fixed')

def analyze_myfunc():
    global cfg, statList, openhubData, bugzillaData, gerritData, gitData, licenceCompanyData, licencePersonalData

    print("myfunc: analyze nothing", flush=True)



def buildTrend(xType, xTarget, xDate, xNum):
    if xNum == 0:
      return
    xStr = str(xNum)
    if xNum in statList['data']['trend'][xType][xTarget][xDate]:
      statList['data']['trend'][xType][xTarget][xDate][xNum] += 1
    else:
      statList['data']['trend'][xType][xTarget][xDate][xNum] = 1



def analyze_trend():
    global statList

    for email, person in statList['people'].items():
      if person['isCommitter']:
        xType = 'committer'
      else:
        xType = 'contributor'
      for inx in '1year', '3month', '1month', '1week':
        buildTrend(xType, 'owner', inx, person['commits'][inx]['owner'])
        buildTrend(xType, 'reviewMerged', inx, person['commits'][inx]['reviewMerged'])
        buildTrend('ui', 'commented', inx, person['ui'][inx]['commented'])
        buildTrend('ui', 'history', inx, person['ui'][inx]['history'])



def analyze_final(weekList = None):
    global cfg, statList, openhubData, bugzillaData, gerritData, gitData

    print("Analyze final")
    statList['addDate'] = datetime.date.today().strftime('%Y-%m-%d')

    for i in statList['people']:
      person = statList['people'][i]
      person['newestCommit'] = person['newestCommit'].strftime("%Y-%m-%d")
      person['prevCommit'] = person['prevCommit'].strftime("%Y-%m-%d")

    analyze_trend()
    myDay = cfg['nowDate']
    x = (myDay - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    if weekList is None:
      weekList = util_load_file(cfg['homedir'] + 'archive/stats_' + x + '.json')
      if weekList is None:
        weekList = {'data': {}}
    statList['diff'] = util_build_diff(statList['data'], weekList['data'])
    sFile = cfg['homedir'] + 'stats.json'
    util_dump_file(sFile, statList)
    x = myDay.strftime('%Y-%m-%d')
    os.system('cp '+ sFile + ' ' + cfg['homedir'] + 'archive/stats_' + x + '.json')
    if myDay.strftime('%w') == '4':
        del statList['people']
        del statList['aliases']
        util_dump_file(cfg['homedir'] + 'weeks/week_' + myDay.strftime('%Y_%W') + '.json', statList)



def runLoadCSV():
    global cfg, statList

    try:
      fileName = cfg['homedir'] + 'gitdm-config/aliases'
      statList['aliases'] = util_load_csv(fileName, ' ')
      fileName = cfg['homedir'] + 'gitdm-config/licenseCompany.csv'
      cfg['companies'] = util_load_csv(fileName, ';')
      fileName = cfg['homedir'] + 'gitdm-config/licensePersonal.csv'
      licencePersonalData = util_load_csv(fileName, ';')

      # check consistency
      for i in statList['aliases']:
        if i in licencePersonalData:
          raise Exception('alias ' + i + ' in aliases is licensed')
        elif statList['aliases'][i] not in licencePersonalData:
          raise Exception('target ' + statList['aliases'][i] + ' for alias ' + i + ' in aliases is NOT licensed')

      # create base people info
      for id, row in licencePersonalData.items():
        statList['people'][id] = util_create_person_gerrit(row['name'], id)
        statList['people'][id]['licenseOK'] = True
        x = row['license']
        if not x.startswith('http') and not x.startswith('COMPANY') and not x.startswith('AUDIT'):
          statList['people'][id]['licenseText'] = row['license']

    except Exception as e:
      print('Error load file ' + fileName + ' due to ' + str(e))
      exit(-1)



def loadCfg(platform):
    global cfg

    if 'esc_homedir' in os.environ:
      homeDir = os.environ['esc_homedir']
    else:
      homeDir = '/home/jani/esc'
    cfg = util_load_data_file(homeDir + '/config.json')
    cfg['homedir'] = homeDir + '/'
    cfg['platform'] = platform
    cfg['nowDate'] = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    cfg['cutDate'] = cfg['nowDate']
    cfg['1weekDate'] = cfg['nowDate'] - datetime.timedelta(days=7)
    cfg['1monthDate'] = cfg['nowDate'] - datetime.timedelta(days=30)
    cfg['3monthDate'] = cfg['nowDate'] - datetime.timedelta(days=90)
    cfg['1yearDate'] = cfg['nowDate'] - datetime.timedelta(days=365)
    print("Reading and writing data to " + cfg['homedir'])



def runAnalyze():
    global cfg, statList, openhubData, bugzillaData, gerritData, gitData

    openhubData = util_load_data_file(cfg['homedir'] + 'dump/openhub_dump.json')
    bugzillaData = util_load_data_file(cfg['homedir'] + 'dump/bugzilla_dump.json')
    gerritData = util_load_data_file(cfg['homedir'] + 'dump/gerrit_dump.json')
    gitData = util_load_data_file(cfg['homedir'] + 'dump/git_dump.json')
    statList = util_create_statList()
    runLoadCSV()

    analyze_mentoring()
    analyze_ui()
    analyze_qa()
    analyze_myfunc()
    analyze_final()


def runUpgrade(args):
    global cfg, statList, openhubData, bugzillaData, gerritData, gitData

    args = args[1:]
    openhubData = util_load_data_file(cfg['homedir'] + 'dump/openhub_dump.json')
    bugzillaData = util_load_data_file(cfg['homedir'] + 'dump/bugzilla_dump.json')
    gerritData = util_load_data_file(cfg['homedir'] + 'dump/gerrit_dump.json')
    gitData = util_load_data_file(cfg['homedir'] + 'dump/git_dump.json')
    statList = util_create_statList()
    runLoadCSV()
    csvList = statList
    cfg['cutDate'] = datetime.datetime(day=27,month=8,year=2015)
    weekList = util_create_statList()

    for week in args:
      print('upgrading ' + week)

      # create new statlist
      cfg['cutDate'] += datetime.timedelta(days=7)
      cfg['nowDate'] = cfg['cutDate']
      statList = util_create_statList()
      statList['aliases'] = csvList['aliases']
      analyze_mentoring()
      analyze_ui()
      analyze_qa()
      analyze_myfunc()

      # combine old statlist with new statlist
      orgStatList = util_load_data_file(cfg['homedir'] + 'OLDweeks/' + week)

      # copy from old data
      statList['data']['easyhacks']['assigned'] = orgStatList['data']['easyhacks']['assigned']
      statList['data']['easyhacks']['cleanup_comments'] = orgStatList['data']['easyhacks']['cleanup_comments']
      statList['data']['easyhacks']['needsDevEval'] = orgStatList['data']['easyhacks']['needsDevEval']
      statList['data']['easyhacks']['needsUXEval'] = orgStatList['data']['easyhacks']['needsUXEval']
      statList['data']['easyhacks']['open'] = orgStatList['data']['easyhacks']['open']
      statList['data']['easyhacks']['total'] = orgStatList['data']['easyhacks']['total']
      statList['data']['gerrit']['committer']['1month']['ABANDONED'] = orgStatList['data']['gerrit']['committer']['1month']['ABANDONED']
      statList['data']['gerrit']['committer']['1month']['MERGED'] = orgStatList['data']['gerrit']['committer']['1month']['MERGED']
      statList['data']['gerrit']['committer']['1month']['NEW'] = orgStatList['data']['gerrit']['committer']['1month']['NEW']
      statList['data']['gerrit']['committer']['1month']['reviewed'] = orgStatList['data']['gerrit']['committer']['1month']['reviewed']
      statList['data']['gerrit']['committer']['1week']['ABANDONED'] = orgStatList['data']['gerrit']['committer']['1week']['ABANDONED']
      statList['data']['gerrit']['committer']['1week']['MERGED'] = orgStatList['data']['gerrit']['committer']['1week']['MERGED']
      statList['data']['gerrit']['committer']['1week']['NEW'] = orgStatList['data']['gerrit']['committer']['1week']['NEW']
      statList['data']['gerrit']['committer']['1week']['reviewed'] = orgStatList['data']['gerrit']['committer']['1week']['reviewed']
      statList['data']['gerrit']['committer']['1year']['ABANDONED'] = orgStatList['data']['gerrit']['committer']['1year']['ABANDONED']
      statList['data']['gerrit']['committer']['1year']['MERGED'] = orgStatList['data']['gerrit']['committer']['1year']['MERGED']
      statList['data']['gerrit']['committer']['1year']['NEW'] = orgStatList['data']['gerrit']['committer']['1year']['NEW']
      statList['data']['gerrit']['committer']['1year']['reviewed'] = orgStatList['data']['gerrit']['committer']['1year']['reviewed']
      statList['data']['gerrit']['committer']['3month']['ABANDONED'] = orgStatList['data']['gerrit']['committer']['3month']['ABANDONED']
      statList['data']['gerrit']['committer']['3month']['MERGED'] = orgStatList['data']['gerrit']['committer']['3month']['MERGED']
      statList['data']['gerrit']['committer']['3month']['NEW'] = orgStatList['data']['gerrit']['committer']['3month']['NEW']
      statList['data']['gerrit']['committer']['3month']['reviewed'] = orgStatList['data']['gerrit']['committer']['3month']['reviewed']
      statList['data']['gerrit']['committer']['total'] = orgStatList['data']['gerrit']['committer']['1year']['total']
      statList['data']['gerrit']['contributor']['1month']['ABANDONED'] = orgStatList['data']['gerrit']['contributor']['1month']['ABANDONED']
      statList['data']['gerrit']['contributor']['1month']['MERGED'] = orgStatList['data']['gerrit']['contributor']['1month']['MERGED']
      statList['data']['gerrit']['contributor']['1month']['NEW'] = orgStatList['data']['gerrit']['contributor']['1month']['NEW']
      statList['data']['gerrit']['contributor']['1month']['reviewed'] = orgStatList['data']['gerrit']['contributor']['1month']['reviewed']
      statList['data']['gerrit']['contributor']['1week']['ABANDONED'] = orgStatList['data']['gerrit']['contributor']['1week']['ABANDONED']
      statList['data']['gerrit']['contributor']['1week']['MERGED'] = orgStatList['data']['gerrit']['contributor']['1week']['MERGED']
      statList['data']['gerrit']['contributor']['1week']['NEW'] = orgStatList['data']['gerrit']['contributor']['1week']['NEW']
      statList['data']['gerrit']['contributor']['1week']['reviewed'] = orgStatList['data']['gerrit']['contributor']['1week']['reviewed']
      statList['data']['gerrit']['contributor']['1year']['ABANDONED'] = orgStatList['data']['gerrit']['contributor']['1year']['ABANDONED']
      statList['data']['gerrit']['contributor']['1year']['MERGED'] = orgStatList['data']['gerrit']['contributor']['1year']['MERGED']
      statList['data']['gerrit']['contributor']['1year']['NEW'] = orgStatList['data']['gerrit']['contributor']['1year']['NEW']
      statList['data']['gerrit']['contributor']['1year']['reviewed'] = orgStatList['data']['gerrit']['contributor']['1year']['reviewed']
      statList['data']['gerrit']['contributor']['3month']['ABANDONED'] = orgStatList['data']['gerrit']['contributor']['3month']['ABANDONED']
      statList['data']['gerrit']['contributor']['3month']['MERGED'] = orgStatList['data']['gerrit']['contributor']['3month']['MERGED']
      statList['data']['gerrit']['contributor']['3month']['NEW'] = orgStatList['data']['gerrit']['contributor']['3month']['NEW']
      statList['data']['gerrit']['contributor']['3month']['reviewed'] = orgStatList['data']['gerrit']['contributor']['3month']['reviewed']
      statList['data']['gerrit']['contributor']['total'] = orgStatList['data']['gerrit']['contributor']['1year']['total']
      statList['data']['openhub']['lines_of_code'] = orgStatList['data']['openhub']['lines_of_code']
      statList['data']['openhub']['total_commits'] = orgStatList['data']['openhub']['total_commits']
      statList['data']['openhub']['total_contributors'] = orgStatList['data']['openhub']['total_contributors']
      statList['data']['openhub']['year_commits'] = orgStatList['data']['openhub']['year_commits']
      statList['data']['openhub']['year_contributors'] = orgStatList['data']['openhub']['year_contributors']


      analyze_final(weekList=weekList)
      weekList = statList


if __name__ == '__main__':
    loadCfg(sys.platform)
    runAnalyze()
#    runUpgrade(sys.argv)
