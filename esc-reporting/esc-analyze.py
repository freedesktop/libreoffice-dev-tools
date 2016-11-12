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
#   contributors missing license
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



def util_dump_file(fileName, rawList):
    try:
      fp = open(fileName, 'w', encoding='utf-8')
      json.dump(rawList, fp, ensure_ascii=False, indent=4, sort_keys=True)
      fp.close()
    except Exception as e:
      print('Error dump file ' + fileName + ' due to ' + str(e))
      os.remove(fileName)
      exit(-1)



def util_build_period_stat(cfg, statList, xDate, email, status, pstatus, base = 'gerrit'):
    for i in '1year', '3month', '1month', '1week':
      if xDate > cfg[i + 'Date']:
        statList['people'][email][base][i][pstatus] += 1
        statList['people'][email][base][i]['total'] += 1
        if not base == 'gerrit' :
          statList['data'][base][i][status] += 1
          statList['data'][base][i]['total'] += 1
        elif statList['people'][email]['isCommitter']:
          statList['data'][base]['committer'][i][status] += 1
          statList['data'][base]['committer'][i]['total'] += 1
        else:
          statList['data'][base]['contributor'][i]['total'] += 1
          statList['data'][base]['contributor'][i][status] += 1



def util_load_data_file(fileName):
    rawList = util_load_file(fileName)
    if rawList == None:
      exit(-1)
    return rawList



def util_create_person_gerrit(person, email):
    return { 'name': person,
             'email': email,
             'commits': {'1year':  {'merged': 0, 'reviewMerged': 0},
                         '3month': {'merged': 0, 'reviewMerged': 0},
                         '1month': {'merged': 0, 'reviewMerged': 0},
                         '1week':  {'merged': 0, 'reviewMerged': 0}},
             'gerrit':  {'1year':  {'owner': 0, 'reviewer': 0, 'total': 0},
                         '3month': {'owner': 0, 'reviewer': 0, 'total': 0},
                         '1month': {'owner': 0, 'reviewer': 0, 'total': 0},
                         '1week':  {'owner': 0, 'reviewer': 0, 'total': 0},
                         'userName': '*DUMMY*'},
             'ui':      {'1year':  {'owner': 0, 'reviewer': 0, 'total': 0},
                         '3month': {'owner': 0, 'reviewer': 0, 'total': 0},
                         '1month': {'owner': 0, 'reviewer': 0, 'total': 0},
                         '1week':  {'owner': 0, 'reviewer': 0, 'total': 0}},
             'qa':      {'1year':  {'owner': 0, 'reviewer': 0, 'total': 0},
                         '3month': {'owner': 0, 'reviewer': 0, 'total': 0},
                         '1month': {'owner': 0, 'reviewer': 0, 'total': 0},
                         '1week':  {'owner': 0, 'reviewer': 0,'total': 0}},
             'isCommitter': False,
             'isContributor': False,
             'hasLicense': False,
             'newestCommit' : datetime.datetime(2001, 1, 1),
             'prevCommit':  datetime.datetime(2001, 1, 1)}



def util_create_statList():
    return {'data': {'commits': {'committer':   {'1year': {'#': 0}, '3month': {'#': 0}, '1month': {'#': 0}, '1week': {'#': 0}},
                                 'contributor': {'1year': {'#': 0}, '3month': {'#': 0}, '1month': {'#': 0}, '1week': {'#': 0}}},
                     'openhub': {'lines_of_code': 0,
                                 'total_commits': 0,
                                 'total_contributors': 0,
                                 'year_commits': 0,
                                 'year_contributors': 0},
                     'gerrit': {'contributor': {'1year':  {'ABANDONED': 0, 'MERGED': 0, 'NEW': 0, 'reviewed': 0, 'total': 0},
                                                '3month': {'ABANDONED': 0, 'MERGED': 0, 'NEW': 0, 'reviewed': 0, 'total': 0},
                                                '1month': {'ABANDONED': 0, 'MERGED': 0, 'NEW': 0, 'reviewed': 0, 'total': 0},
                                                '1week':  {'ABANDONED': 0, 'MERGED': 0, 'NEW': 0, 'reviewed': 0, 'total': 0}},
                                'committer': {'1year':  {'ABANDONED': 0, 'MERGED': 0, 'NEW': 0, 'reviewed': 0, 'total': 0},
                                              '3month': {'ABANDONED': 0, 'MERGED': 0, 'NEW': 0, 'reviewed': 0, 'total': 0},
                                              '1month': {'ABANDONED': 0, 'MERGED': 0, 'NEW': 0, 'reviewed': 0, 'total': 0},
                                              '1week':  {'ABANDONED': 0, 'MERGED': 0, 'NEW': 0, 'reviewed': 0, 'total': 0}}},
                     'ui': {'1year':  {'added': 0, 'removed': 0, 'commented': 0, 'total': 0},
                            '3month': {'added': 0, 'removed': 0, 'commented': 0, 'total': 0},
                            '1month': {'added': 0, 'removed': 0, 'commented': 0, 'total': 0},
                            '1week':  {'added': 0, 'removed': 0, 'commented': 0, 'total': 0},
                            'needsUXEval' : 0,
                            'topicUI': 0},
                     'qa': {'1year':  {'UNCONFIRMED': 0, 'NEW': 0, 'ASSIGNED': 0, 'REOPENED': 0, 'RESOLVED': 0,
                                       'VERIFIED': 0, 'CLOSED': 0, 'NEEDINFO': 0, 'PLEASETEST': 0, 'commented': 0, 'total': 0},
                            '3month': {'UNCONFIRMED': 0, 'NEW': 0, 'ASSIGNED': 0, 'REOPENED': 0, 'RESOLVED': 0,
                                       'VERIFIED': 0, 'CLOSED': 0, 'NEEDINFO': 0, 'PLEASETEST': 0, 'commented': 0, 'total': 0},
                            '1month': {'UNCONFIRMED': 0, 'NEW': 0, 'ASSIGNED': 0, 'REOPENED': 0, 'RESOLVED': 0,
                                       'VERIFIED': 0, 'CLOSED': 0, 'NEEDINFO': 0, 'PLEASETEST': 0, 'commented': 0, 'total': 0},
                            '1week':  {'UNCONFIRMED': 0, 'NEW': 0, 'ASSIGNED': 0, 'REOPENED': 0, 'RESOLVED': 0,
                                       'VERIFIED': 0, 'CLOSED': 0, 'NEEDINFO': 0, 'PLEASETEST': 0, 'commented': 0, 'total': 0}},
                     'easyhacks' : {'needsDevEval': 0,  'needsUXEval': 0, 'cleanup_comments': 0,
                                    'total': 0,         'assigned': 0,    'open': 0}},
                     'stat': {'openhub_last_analyse': "2001-01-01"},
                     'people': {}}




def util_check_mail(name, mail, statList, combineMail):
    if mail in combineMail:
      mail = combineMail[mail]
    if not mail in statList['people']:
      statList['people'][mail] = util_create_person_gerrit(name, mail)
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



def analyze_mentoring(statList, openhubData, gerritData, gitData, bugzillaData, cfg):
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
      mail = util_check_mail(row['name'], row['email'], statList, cfg['contributor']['combine-email'])
      statList['people'][mail]['gerrit']['userName'] = row['username']
      statList['people'][mail]['isCommitter'] = True
      statList['people'][mail]['isContributor'] = True

    statNewDate = cfg['1yearDate']
    statOldDate = cfg['nowDate']
    for key in gerritData['patch']:
      row = gerritData['patch'][key]
      if row['status'] == 'SUBMITTED' or row['status'] == 'DRAFT':
        row['status'] = 'NEW'
      xDate = datetime.datetime.strptime(row['updated'], '%Y-%m-%d %H:%M:%S.%f000')
      ownerEmail = util_check_mail(row['owner']['name'], row['owner']['email'], statList, cfg['contributor']['combine-email'])
      statList['people'][ownerEmail]['gerrit']['userName'] = row['owner']['username']
      util_build_period_stat(cfg, statList, xDate, ownerEmail, row['status'], 'owner')
      if ownerEmail in cfg['contributor']['contributors'] or ownerEmail in cfg['contributor']['license-pending']:
        statList['people'][ownerEmail]['hasLicense'] = True
      if xDate < statOldDate:
        statOldDate = xDate
      if xDate > statNewDate:
        statNewDate = xDate

      for i in 'Verified', 'Code-Review':
        for x in row['labels'][i]['all']:
          xEmail = util_check_mail(x['name'], x['email'], statList, cfg['contributor']['combine-email'])
          if xEmail != ownerEmail:
            util_build_period_stat(cfg, statList, xDate, xEmail, 'reviewed', 'reviewer')

    print(" from " + statOldDate.strftime('%Y-%m-%d') + " to " + statNewDate.strftime('%Y-%m-%d'))
    print("mentoring: analyze git", end="", flush=True)

    statNewDate = cfg['1yearDate']
    statOldDate = cfg['nowDate']
    for key in gitData['commits']:
      row = gitData['commits'][key]
      xDate = datetime.datetime.strptime(row['date'], "%Y-%m-%d %H:%M:%S")
      if xDate < statOldDate:
        statOldDate = xDate
      if xDate > statNewDate:
        statNewDate = xDate
      author = util_check_mail(row['author'], row['author-email'], statList, cfg['contributor']['combine-email'])
      committer = util_check_mail(row['committer'], row['committer-email'], statList, cfg['contributor']['combine-email'])
      statList['people'][author]['isContributor'] = True
      statList['people'][committer]['isContributor'] = True

      for i in author, committer:
        if xDate > statList['people'][i]['newestCommit']:
          if statList['people'][i]['newestCommit'] > statList['people'][i]['prevCommit']:
            statList['people'][i]['prevCommit'] = statList['people'][i]['newestCommit']
          statList['people'][i]['newestCommit'] = xDate
        elif xDate > statList['people'][i]['prevCommit']:
          statList['people'][i]['prevCommit'] = xDate

      for i in '1year', '3month', '1month', '1week':
        if xDate > cfg[i + 'Date']:
          if author != committer:
            statList['people'][author]['commits'][i]['merged'] += 1
            statList['people'][committer]['commits'][i]['reviewMerged'] += 1
            statList['data']['commits']['contributor'][i]['#'] += 1
          else:
            statList['people'][author]['commits'][i]['merged'] += 1
            statList['data']['commits']['committer'][i]['#'] += 1

    print(" from " + statOldDate.strftime("%Y-%m-%d") + " to " + statNewDate.strftime("%Y-%m-%d"))
    print("mentoring: analyze easyhacks", end="", flush=True)

    statNewDate = cfg['1yearDate']
    statOldDate = cfg['nowDate']
    for key, row in bugzillaData['bugs'].items():
      if row['status'] == 'RESOLVED' or row['status'] == 'VERIFIED' or not 'easyHack' in row['keywords']:
        continue

      xDate = datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ")
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



def analyze_ui(statList, openhubData, gerritData, gitData, bugzillaData, cfg):
    print("ui: analyze bugzilla", flush=True)

    for key, row in bugzillaData['bugs'].items():
      if row['status'] == 'RESOLVED' or row['status'] == 'VERIFIED' or not 'topicUI' in row['keywords']:
        continue

      statList['data']['ui']['topicUI'] += 1
      if 'needsUXEval' in row['keywords']:
        statList['data']['ui']['needsUXEval'] += 1

      for change in row['comments']:
        email = util_check_mail('*UNKNOWN*', change['creator'], statList, cfg['contributor']['combine-email'])
        xDate = datetime.datetime.strptime(change['creation_time'], "%Y-%m-%dT%H:%M:%SZ")
        util_build_period_stat(cfg, statList, xDate, email, 'commented', 'reviewer', base='ui')

      for change in row['history']:
        email = util_check_mail('*UNKNOWN*', change['who'], statList, cfg['contributor']['combine-email'])
        xDate = datetime.datetime.strptime(change['when'], "%Y-%m-%dT%H:%M:%SZ")
        for entry in change['changes']:
          if entry['added'] != '':
            st = 'added'
          else:
            st = 'removed'
          util_build_period_stat(cfg, statList, xDate, email, st, 'reviewer', base='ui')


def analyze_qa(statList, openhubData, gerritData, gitData, bugzillaData, cfg):
    print("qa: analyze bugzilla", flush=True)

    for key, row in bugzillaData['bugs'].items():
      email = util_check_mail('*UNKNOWN*', row['creator'], statList, cfg['contributor']['combine-email'])
      xDate = datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ")
      util_build_period_stat(cfg, statList, xDate, email, row['status'], 'owner', base='qa')

      for change in row['comments']:
        email = util_check_mail('*UNKNOWN*', change['creator'], statList, cfg['contributor']['combine-email'])
        xDate = datetime.datetime.strptime(change['creation_time'], "%Y-%m-%dT%H:%M:%SZ")
        util_build_period_stat(cfg, statList, xDate, email, 'commented', 'reviewer', base='qa')



def analyze_myfunc(statList, openhubData, gerritData, gitData, bugzillaData, cfg):
    print("myfunc: analyze nothing", flush=True)



def analyze_final(statList, cfg):
    print("Analyze final")
    statList['addDate'] = datetime.date.today().strftime('%Y-%m-%d')

    zDate = datetime.datetime(year=2001, month=1, day=1)
    for i in statList['people']:
      person = statList['people'][i]
      delta = person['newestCommit'] - person['prevCommit']
      person['newestCommit'] = person['newestCommit'].strftime("%Y-%m-%d")
      person['prevCommit'] = person['prevCommit'].strftime("%Y-%m-%d")

    myDay = datetime.date.today()
    x = (myDay - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    weekList = util_load_file(cfg['homedir'] + 'archive/stats_' + x + '.json')
    if weekList is None:
      weekList = {'data': {}}
    statList['diff'] = util_build_diff(statList['data'], weekList['data'])
    util_dump_file(cfg['homedir'] + 'stats.json', statList)
    x = myDay.strftime('%Y-%m-%d')
    util_dump_file(cfg['homedir'] + 'archive/stats_' + x + '.json', statList)
    if myDay.strftime('%w') == '4':
      util_dump_file(cfg['homedir'] + 'weeks/week_' + myDay.strftime('%Y_%W') + '.json', statList)



def runCfg(platform):
    if 'esc_homedir' in os.environ:
      homeDir = os.environ['esc_homedir']
    else:
      homeDir = '/home/jani/esc'
    cfg = util_load_data_file(homeDir + '/config.json')
    cfg['homedir'] = homeDir + '/'
    cfg['platform'] = platform
    print("Reading and writing data to " + cfg['homedir'])

    cfg['contributor'] = util_load_data_file(cfg['homedir'] + 'dump/developers_dump.json')
    cfg['nowDate'] = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    cfg['cutDate'] = cfg['nowDate'] - datetime.timedelta(days=365)
    cfg['1weekDate'] = cfg['nowDate'] - datetime.timedelta(days=7)
    cfg['1monthDate'] = cfg['nowDate'] - datetime.timedelta(days=30)
    cfg['3monthDate'] = cfg['nowDate'] - datetime.timedelta(days=90)
    cfg['1yearDate'] = cfg['nowDate'] - datetime.timedelta(days=365)
    return cfg



def runAnalyze(cfg):
    openhubData = util_load_data_file(cfg['homedir'] + 'dump/openhub_dump.json')
    bugzillaData = util_load_data_file(cfg['homedir'] + 'dump/bugzilla_dump.json')
    gerritData = util_load_data_file(cfg['homedir'] + 'dump/gerrit_dump.json')
    gitData = util_load_data_file(cfg['homedir'] + 'dump/git_dump.json')

    statList = util_create_statList()
    analyze_mentoring(statList, openhubData, gerritData, gitData, bugzillaData, cfg)
    analyze_ui(statList, openhubData, gerritData, gitData, bugzillaData, cfg)
    analyze_qa(statList, openhubData, gerritData, gitData, bugzillaData, cfg)
    analyze_myfunc(statList, openhubData, gerritData, gitData, bugzillaData, cfg)
    analyze_final(statList, cfg)



if __name__ == '__main__':
    runAnalyze(runCfg(sys.platform))
