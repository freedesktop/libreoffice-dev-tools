#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
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
import re



def util_errorMail(text):
    print(text)
    sendMail = 'mail -r mentoring@documentfoundation.org ' + cfg['mail']['bcc'] + ' -s "ERROR: esc-analyze FAILED" mentoring@documentfoundation.org <<EOF\n' + text + '\nPlease have a look at vm174\nEOF\n'
    os.system(sendMail)




def util_errorMail(text):
    print(text)
    sendMail = 'mail -r mentoring@documentfoundation.org -s "' + text + '" mentoring@documentfoundation.org <<EOF\nPlease have a look at vm174\nEOF\n'
    os.system(sendMail)


def util_load_file(fileName, isJson=True):
    try:
      fp = open(fileName, encoding='utf-8')
      if(isJson):
        rawData = json.load(fp)
      else:
        rawData = fp.readlines()
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
      for line in fp:
        line = line[:-1]
        if len(line) == 0:
          continue
        if line[0] == '#':
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
                         'userName': '*dummy*'},
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
                     'qa': {'unconfirmed': {'count': 0, 'documentation': 0, 'enhancement': 0, 'needsUXEval': 0,
                         'haveBacktrace': 0, 'needsDevAdvice': 0, 'android': 0}},
                     'easyhacks' : {'needsDevEval': 0,  'needsUXEval': 0, 'cleanup_comments': 0,
                                    'total': 0,         'assigned': 0,    'open': 0},
                     'esc': {}},
                     'stat': {'openhub_last_analyse': "2001-01-01"},
                     'people': {},
                     'escList': {},
                     'reportList': {}}




def util_check_mail(name, xmail):
    global statList

    mail = xmail.lower()
    if mail in statList['aliases']:
      mail = statList['aliases'][mail]
    if not mail in statList['people']:
      statList['people'][mail] = util_create_person_gerrit(name, mail)
      if mail == '*dummy*':
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
    if 'analysis' in openhubData['project']:
      statList['data']['openhub']['lines_of_code'] = int(openhubData['project']['analysis']['total_code_lines'])
      statList['data']['openhub']['total_commits'] = int(openhubData['project']['analysis']['total_commit_count'])
      statList['data']['openhub']['total_contributors'] = int(openhubData['project']['analysis']['total_contributor_count'])
      statList['data']['openhub']['year_commits'] = int(openhubData['project']['analysis']['twelve_month_commit_count'])
      statList['data']['openhub']['year_contributors'] = int(openhubData['project']['analysis']['twelve_month_contributor_count'])
      xDate = datetime.datetime.strptime(openhubData['project']['analysis']['updated_at'], "%Y-%m-%dT%H:%M:%SZ")
      statList['stat']['openhub_last_analyse'] = xDate.strftime('%Y-%m-%d')
    else:
      statList['data']['openhub']['lines_of_code'] = -1
      statList['data']['openhub']['total_commits'] = -1
      statList['data']['openhub']['total_contributors'] = -1
      statList['data']['openhub']['year_commits'] = -1
      statList['data']['openhub']['year_contributors'] = -1
      statList['stat']['openhub_last_analyse'] = '2001-01-01'

    print(" to " + statList['stat']['openhub_last_analyse'])
    print("mentoring: analyze gerrit", end="", flush=True)

    for row in gerritData['committers']:
      mail = util_check_mail(row['name'], row['email'])
      statList['people'][mail]['gerrit']['userName'] = row['username']
      statList['people'][mail]['gerrit']['reviewName'] = '{} <{}>'.format(row['name'],row['email'])
      statList['people'][mail]['isCommitter'] = True
      statList['people'][mail]['isContributor'] = True
    x1 = statList['people']['admin@shinnok.com']
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
          if row['component'] == 'Documentation':
            statList['data']['qa']['unconfirmed']['documentation'] += 1
          if row['component'] == 'Android app' or row['component'] == 'Android Viewer':
            statList['data']['qa']['unconfirmed']['android'] += 1

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



def analyze_esc():
    global cfg, statList, bugzillaData, bugzillaESCData, crashData, weekList

    print("esc: analyze bugzilla", flush=True)

    statList['data']['esc']['QAstat'] = {'opened': bugzillaESCData['ESC_QA_STATS_UPDATE']['opened'],
                                         'closed': bugzillaESCData['ESC_QA_STATS_UPDATE']['closed']}
    statList['data']['esc']['MAB'] = {}
    statList['escList']['QAstat'] = {'top15_squashers' : {},
                                     'top15_reporters' : {},
                                     'top15_fixers' : [],
                                     'top15_confirmers' : []}
    for line in bugzillaESCData['ESC_QA_STATS_UPDATE']['top15_closers']:
      statList['escList']['QAstat']['top15_squashers'][str(line['who'])] = line['closed']
    for line in bugzillaESCData['ESC_QA_STATS_UPDATE']['top15_reporters']:
      statList['escList']['QAstat']['top15_reporters'][str(line['who'])] = line['reported']
    statList['escList']['MostPressingBugs'] = {'open': {'list': {}}, 'closed': {'list': {}}}
    for type in 'open', 'closed':
       statList['escList']['MostPressingBugs'][type]['count'] = bugzillaESCData['MostPressingBugs'][type]['count']
       for id in bugzillaESCData['MostPressingBugs'][type]['list']:
           statList['escList']['MostPressingBugs'][type]['list'][id] = bugzillaData['bugs'][id]['summary']

    bug_fixers = {}
    bug_confirmers = {}
    for id, bug in bugzillaData['bugs'].items():
      if ((bug['status'] == 'RESOLVED' or bug['status'] == 'VERIFIED' or bug['status'] == 'CLOSED') and 'FIXED' == bug['resolution']) or \
          bug['is_confirmed']:

        fixer = None
        confirmer = None
        for i in range(len(bug['history'])-1,-1,-1):
          changes = bug['history'][i]['changes']
          when = datetime.datetime.strptime(bug['history'][i]['when'], "%Y-%m-%dT%H:%M:%SZ")
          for j in range(0,len(changes)):
            if when >= cfg['1weekDate']:
              if changes[j]['field_name'] == 'resolution' and changes[j]['added'] == 'FIXED':
                fixer = bug['history'][i]['who'].lower()
              if changes[j]['field_name'] == 'is_confirmed' and changes[j]['added'] == '1':
                confirmer = bug['history'][i]['who'].lower()

        if fixer and fixer != 'libreoffice-commits@lists.freedesktop.org':
          if fixer in statList['aliases']:
            fixer = statList['aliases'][fixer]
          if fixer in statList['people']:
            fixer = statList['people'][fixer]['name']
          if not fixer in bug_fixers:
            bug_fixers[fixer] = 0
          bug_fixers[str(fixer)] += 1

        if confirmer and confirmer != 'libreoffice-commits@lists.freedesktop.org':
          if confirmer in statList['aliases']:
            confirmer = statList['aliases'][confirmer]
          if confirmer in statList['people']:
            confirmer = statList['people'][confirmer]['name']
          if not confirmer in bug_confirmers:
            bug_confirmers[confirmer] = 0
          bug_confirmers[str(confirmer)] += 1

    statList['escList']['QAstat']['top15_fixers'] = bug_fixers
    statList['escList']['QAstat']['top15_confirmers'] = bug_confirmers

    for id, row in bugzillaESCData['ESC_MAB_UPDATE'].items():
      statList['data']['esc']['MAB'][id] = row
      statList['data']['esc']['MAB'][id]['%'] = int((row['open'] / row['total'])*100)

    statList['escList']['bisect'] = weekList['escList']['bisect']
    statList['escList']['bisect'].insert(0, [bugzillaESCData['ESC_BISECTED_UPDATE']['open'],
                                             bugzillaESCData['ESC_BISECTED_UPDATE']['total']])
    del statList['escList']['bisect'][-1]
    statList['escList']['bibisect'] = weekList['escList']['bibisect']
    statList['escList']['bibisect'].insert(0, [bugzillaESCData['ESC_BIBISECTED_UPDATE']['open'],
                                               bugzillaESCData['ESC_BIBISECTED_UPDATE']['total']])
    del statList['escList']['bibisect'][-1]

    statList['data']['esc']['regression'] = {}
    statList['data']['esc']['regression']['high'] = bugzillaESCData['ESC_REGRESSION_UPDATE']['high']
    statList['data']['esc']['regression']['open'] = bugzillaESCData['ESC_REGRESSION_UPDATE']['open']
    statList['data']['esc']['regression']['open-1'] = weekList['data']['esc']['regression']['open']
    statList['data']['esc']['regression']['total'] = bugzillaESCData['ESC_REGRESSION_UPDATE']['total']
    statList['data']['esc']['regression']['total-1'] = weekList['data']['esc']['regression']['total']

    statList['data']['esc']['component'] = {}
    statList['data']['esc']['component']['high'] = {}
    for id, row in bugzillaESCData['ESC_COMPONENT_UPDATE']['high'].items():
      statList['data']['esc']['component']['high'][id] = row['count']
    statList['data']['esc']['component']['all'] = {}
    for id, row in bugzillaESCData['ESC_COMPONENT_UPDATE']['all'].items():
      statList['data']['esc']['component']['all'][id] = row['count']
    statList['data']['esc']['component']['os'] = {}
    for id, row in bugzillaESCData['ESC_COMPONENT_UPDATE']['os'].items():
      statList['data']['esc']['component']['os'][id] = row['count']

    statList['data']['esc']['crashtest'] = {'import': crashData['crashtest']['crashlog'],
                                            'export': crashData['crashtest']['exportCrash']}
    statList['data']['esc']['crashreport'] = crashData['crashreport']['versions']


def util_is_company_license(email):
    domainMap = util_load_file(cfg['homedir'] + 'gitdm-config/domain-map', False)
    for line in domainMap:
      line = line[:-1]
      if line.startswith('#') or line.startswith(' ') or len(line) == 0:
        continue
      domain = line
      if '\t' in domain:
        domain = line[:line.index('\t')]
      else:
        domain = line[:line.index(' ')]
      if email.endswith(domain):
        return True
    for domain in cfg['companies']:
      if email.endswith(domain):
        return True
    return False

def analyze_reports():
    global cfg, statList, openhubData, bugzillaData, gerritData, gitData, automateData

    print("reports: analyze", flush=True)
    mailedDate = cfg['3monthDate'] - datetime.timedelta(days=90)
    zeroDate = datetime.datetime(year=2001, month=1, day=1)
    statList['reportList'] = {'award_1st_email': [],
                              'pending_license': [],
                              'missing_license': [],
                              'to_be_closed': [],
                              'needsDevEval': [],
                              'needsUXEval': [],
                              'needinfo': [],
                              'easyhacks_new': [],
                              'too_many_comments': [],
                              'top10commit': [],
                              'top10review': []}
    fileAutomate = cfg['homedir'] + 'automateTODO.json'
    automateList = util_load_data_file(fileAutomate)
    automateList['gerrit']['to_abandon_abandon'] = {}
    automateList['gerrit']['to_abandon_comment'] = {}
    automateList['gerrit']['to_review'] = {}
    automateList['bugzilla']['missing_cc'] = {}
    automateList['bugzilla']['remove_cc'] = {}
    automateList['bugzilla']['to_unassign_comment'] = {}
    automateList['bugzilla']['to_unassign_unassign'] = {}

    automateNow = cfg['nowDate'].strftime("%Y-%m-%d")

    for id, row in statList['people'].items():
      entry = {'name': row['name'], 'email': id, 'license': row['licenseText']}
      if row['newestCommit'] > mailedDate\
      and row['newestCommit'] < cfg['3monthDate']\
      and id not in automateData['reminder']\
      and not util_is_company_license(entry['email']):
        automateList['mail']['we_miss_you_email'][entry['email']] = entry['name']
        automateData['reminder'][id] = automateNow
      x = row['commits']['1month']['owner']
      if x != 0 and row['commits']['total'] == x and not id in automateData['award']:
          automateList['mail']['award_1st_email'][entry['email']] = entry['name']
          automateData['award'][entry['email']] = automateNow
      if row['licenseText'].startswith('PENDING'):
          statList['reportList']['pending_license'].append(entry)
    delList = []
    for id, xTime in automateData['reminder'].items():
      x = datetime.datetime.strptime(xTime, '%Y-%m-%d')
      if x < cfg['3monthDate']:
        delList.append(id)
    for id in delList:
      del automateData['reminder'][id]
    delList = []
    for id, xTime in automateData['award'].items():
      x = datetime.datetime.strptime(xTime, '%Y-%m-%d')
      if x > cfg['1weekDate']:
        entry = {'name': statList['people'][id]['name'], 'email': id, 'license': statList['people'][id]['licenseText']}
        statList['reportList']['award_1st_email'].append(entry)
      if x < cfg['1monthDate']:
        delList.append(id)
    for id in delList:
      del automateData['award'][id]

    tmpListToReview = []
    for key,row in gerritData['patch'].items():
      if row['status'] == 'SUBMITTED' or row['status'] == 'DRAFT':
        row['status'] = 'NEW'
      xDate = datetime.datetime.strptime(row['updated'], '%Y-%m-%d %H:%M:%S.%f000')
      ownerEmail = util_check_mail(row['owner']['name'], row['owner']['email'])
      # while web is happy with the unique project~branch~changeID label, commandline interface
      # only accepts ambiguous changeID, doesn't help, so fullid is not really fullid, but at least
      # less prone to conflicts than just changeset-number that also can easily prefix-match commit-hashes
      entry = {'id': key, 'fullid': row['change_id'], 'name': row['owner']['name'], 'email': ownerEmail, 'title': row['subject']}
      if row['status'] != 'ABANDONED':
        if ownerEmail is None:
          ownerEmail = row['owner']['email']
          entry['email'] = ownerEmail
          entry['license'] = 'GERRIT NO LICENSE'
          statList['reportList']['missing_license'].append(entry)
        elif not statList['people'][ownerEmail]['licenseOK']\
          and not util_is_company_license(ownerEmail):
          print(ownerEmail)
          entry['license'] = 'GERRIT: ' + statList['people'][ownerEmail]['licenseText']
          statList['reportList']['missing_license'].append(entry)

      if row['status'] == 'NEW':
        doBlock = False
        cntReview = 0
        for x1 in 'Code-Review', 'Verified':
          for x in row['labels'][x1]['all']:
            if x['value'] == -2:
              doBlock = True
            if x['email'] != ownerEmail and x['email'] != 'ci@libreoffice.org':
              cntReview += 1

        x = len(row['messages']) - 1
        if x >= 0:
          patchset = row['messages'][x]['_revision_number']
          txt = row['messages'][x]['message']
        else:
          patchset = 1
          txt = ''
        if xDate < cfg['1monthDate'] and not doBlock:
          # gerrit cli sucks and doesn't accept changeset,patchrev but only uses numericID
          if 'A polite ping' in txt:
            automateList['gerrit']['to_abandon_abandon'][entry['id']] = patchset
          else:
            automateList['gerrit']['to_abandon_comment'][entry['id']] = patchset
        if cntReview == 0 and not statList['people'][ownerEmail]['isCommitter']:
            tmpListToReview.append({'id': entry['id'], 'fullid': entry['fullid'], 'patchset': patchset})

    defaultEmail = util_check_mail('', cfg['automate']['gerritReviewUserEmail'])
    for rowTmp in tmpListToReview:
      reviewEmail = defaultEmail
      txt = gerritData['patch'][rowTmp['id']]['subject']
      if txt.startswith('tdf#'):
        try:
          row = bugzillaData['bugs'][re.findall('\d+', txt)[0]]
          ownerEmail = util_check_mail(row['creator_detail']['name'], row['creator_detail']['email'])
          if 'reviewName' in statList['people'][ownerEmail]['gerrit']:
            reviewEmail = ownerEmail
          else:
            for comment in row['comments']:
              email = util_check_mail('', comment['creator'])
              if not email == 'anistenis@gmail.com' and not email == 'admin@shinnok.com' and 'reviewName' in statList['people'][ownerEmail]['gerrit']:
                reviewEmail = email
                break
        except Exception as e:
          pass
      x = statList['people'][reviewEmail]
      automateList['gerrit']['to_review'][rowTmp['fullid']] = {'name': statList['people'][reviewEmail]['gerrit']['reviewName'],
                                                               'patchset': rowTmp['patchset'], 'id': rowTmp['id']}

    for key, row in bugzillaData['bugs'].items():
      if not 'cc' in row:
        row['cc'] = []
      if not 'keywords' in row:
        row['keywords'] = []

      if row['status'] == 'RESOLVED' or row['status'] == 'VERIFIED':
        continue

      if not 'easyHack' in row['keywords']:
        if 'mentoring' in row['cc']:
            automateList['bugzilla']['remove_cc'][key] = 0
        continue

      if 'needsDevEval' in row['keywords']:
          statList['reportList']['needsDevEval'].append(key)
      if 'needsUXEval' in row['keywords']:
          statList['reportList']['needsUXEval'].append(key)
      if row['status'] == 'NEEDINFO':
          statList['reportList']['needinfo'].append(key)
      elif row['status'] == 'ASSIGNED':
        xDate = datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ")
        if xDate < cfg['1monthDate']:
          txt = row['comments'][len(row['comments'])-1]
          if 'A polite ping' in txt:
            automateList['bugzilla']['to_unassign_unassign'][key]= 0
          else:
            automateList['bugzilla']['to_unassign_comment'][key] = 0
      if len(row['comments']) >= 5:
        statList['reportList']['too_many_comments'].append(key)
      if not 'mentoring@documentfoundation.org' in row['cc']:
          automateList['bugzilla']['missing_cc'][key] = 0
      if row['comments'][-1]['creator'] == 'libreoffice-commits@lists.freedesktop.org' and not key in cfg['bugzilla']['close_except']:
          statList['reportList']['to_be_closed'].append(key)
      cDate = datetime.datetime.strptime(row['creation_time'], "%Y-%m-%dT%H:%M:%SZ")
      if cDate >= cfg['1weekDate'] or 'easyhack' in row['history'][-1]['changes'][0]['added']:
        statList['reportList']['easyhacks_new'].append(key)

    tmpClist = sorted(statList['people'], key=lambda k: (statList['people'][k]['commits']['1month']['owner']),reverse=True)
    for i in tmpClist:
        if not statList['people'][i]['isCommitter']:
            x = {'mail': i, 'name': statList['people'][i]['name'],
                 'month': statList['people'][i]['commits']['1month']['owner'],
                 'year': statList['people'][i]['commits']['1year']['owner']}
            statList['reportList']['top10commit'].append(x)
            if len(statList['reportList']['top10commit']) >= 10:
                break
    tmpRlist = sorted(statList['people'], key=lambda k: (statList['people'][k]['gerrit']['1month']['reviewer']),reverse=True)
    for i in tmpRlist:
        if i != 'ci@libreoffice.org':
            x = {'mail': i, 'name': statList['people'][i]['name'],
                 'month': statList['people'][i]['gerrit']['1month']['reviewer'],
                 'year': statList['people'][i]['gerrit']['1year']['reviewer']}
            statList['reportList']['top10review'].append(x)
            if len(statList['reportList']['top10review']) >= 10:
                break

    util_dump_file(fileAutomate, automateList)
    util_dump_file(cfg['homedir'] + 'dump/automate.json', automateData)



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



def analyze_final():
    global cfg, statList, openhubData, bugzillaData, gerritData, gitData, weekList

    print("Analyze final")
    statList['addDate'] = datetime.date.today().strftime('%Y-%m-%d')

    for i in statList['people']:
      person = statList['people'][i]
      person['newestCommit'] = person['newestCommit'].strftime("%Y-%m-%d")
      person['prevCommit'] = person['prevCommit'].strftime("%Y-%m-%d")

#    analyze_trend()
    myDay = cfg['nowDate']
    statList['diff'] = util_build_diff(statList['data'], weekList['data'])
    sFile = cfg['homedir'] + 'stats.json'
    util_dump_file(sFile, statList)
    x = myDay.strftime('%Y-%m-%d')
    os.system('cp '+ sFile + ' ' + cfg['homedir'] + 'archive/stats_' + x + '.json')
    if myDay.strftime('%w') == '4':
      if 'people' in statList:
        del statList['people']
      if 'aliases' in statList:
        del statList['aliases']
      if 'escList' in statList:
        del statList['escList']
      if 'reportList' in statList:
        del statList['reportList']
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
          print('alias ' + i + ' in aliases is licensed')
        elif statList['aliases'][i] not in licencePersonalData:
          print('target ' + statList['aliases'][i] + ' for alias ' + i + ' in aliases is NOT licensed')

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
      homeDir = '/home/esc-mentoring/esc'

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
    global cfg, statList
    global openhubData, bugzillaData, bugzillaESCData, gerritData, gitData, crashData, weekList, automateData

    x = (cfg['nowDate'] - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    weekList = util_load_file(cfg['homedir'] + 'archive/stats_' + x + '.json')

    openhubData = util_load_data_file(cfg['homedir'] + 'dump/openhub_dump.json')
    bugzillaData = util_load_data_file(cfg['homedir'] + 'dump/bugzilla_dump.json')
    bugzillaESCData = util_load_data_file(cfg['homedir'] + 'dump/bugzilla_esc_dump.json')
    gerritData = util_load_data_file(cfg['homedir'] + 'dump/gerrit_dump.json')
    gitData = util_load_data_file(cfg['homedir'] + 'dump/git_dump.json')
    crashData = util_load_data_file(cfg['homedir'] + 'dump/crash_dump.json')
    automateData = util_load_data_file(cfg['homedir'] + 'dump/automate.json')
    statList = util_create_statList()
    try:
      runLoadCSV()
    except Exception as e:
      util_errorMail('ERROR: runLoadCSV failed with ' + str(e))
      pass
    try:
      analyze_mentoring()
    except Exception as e:
      util_errorMail('ERROR: analyze_mentoring failed with ' + str(e))
      pass
    try:
      analyze_ui()
    except Exception as e:
      util_errorMail('ERROR: analyze_ui failed with ' + str(e))
      pass
    try:
      analyze_qa()
    except Exception as e:
      util_errorMail('ERROR: analyze_qa failed with ' + str(e))
      pass
    try:
      analyze_esc()
    except Exception as e:
      util_errorMail('ERROR: analyze_esc failed with ' + str(e))
      pass
    try:
      analyze_myfunc()
    except Exception as e:
      util_errorMail('ERROR: analyze_myfunc failed with ' + str(e))
      pass
    try:
      analyze_reports()
    except Exception as e:
      util_errorMail('ERROR: analyze_reports failed with ' + str(e))
      pass
    try:
      analyze_final()
    except Exception as e:
      util_errorMail('ERROR: analyze_final failed with ' + str(e))
      pass


def runUpgrade(args):
    global cfg, statList, openhubData, bugzillaData, bugzillaESCData, gerritData, gitData, crashData, weekList

    args = args[1:]
    openhubData = util_load_data_file(cfg['homedir'] + 'dump/openhub_dump.json')
    bugzillaData = util_load_data_file(cfg['homedir'] + 'dump/bugzilla_dump.json')
    bugzillaESCData = util_load_data_file(cfg['homedir'] + 'dump/bugzilla_esc_dump.json')
    gerritData = util_load_data_file(cfg['homedir'] + 'dump/gerrit_dump.json')
    gitData = util_load_data_file(cfg['homedir'] + 'dump/git_dump.json')
    crashData = util_load_data_file(cfg['homedir'] + 'dump/crash_dump.json')
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
      cfg['1weekDate'] = cfg['nowDate'] - datetime.timedelta(days=7)
      cfg['1monthDate'] = cfg['nowDate'] - datetime.timedelta(days=30)
      cfg['3monthDate'] = cfg['nowDate'] - datetime.timedelta(days=90)
      cfg['1yearDate'] = cfg['nowDate'] - datetime.timedelta(days=365)

      statList = util_create_statList()
      statList['aliases'] = csvList['aliases']
      analyze_mentoring()
      analyze_ui()
      analyze_qa()
      analyze_esc()
      analyze_myfunc()

      analyze_final()
      weekList = statList


if __name__ == '__main__':
    loadCfg(sys.platform)
    runAnalyze()
#    runUpgrade(sys.argv)
