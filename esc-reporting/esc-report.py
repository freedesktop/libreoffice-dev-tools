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
# and statistics created by esc-analyze.py:
#      esc/stats.json (the daily data)
#
# The report functions run through the data files and prints interesting numbers and lists
# You can add your own report function (see analyze_myfunc() for example).
# You can also get it mailed on a daily basis
#
# Installed on vm174:/usr/local/bin runs every night (generating and mailing reports)
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


def util_load_data_file(fileName):
    try:
      fp = open(fileName, encoding='utf-8')
      rawData = json.load(fp)
      fp.close()
    except Exception as e:
      print('Error load file ' + fileName + ' due to ' + str(e))
      exit(-1)
    return rawData



def util_check_mail(mail, statList, combineMail):
    if mail in combineMail:
      mail = combineMail[mail]
    if not mail in statList['people']:
      print('Error mail ' + mail + ' not in stats.json/people')
      exit(-1)
    return mail



def util_formatBugzilla(id, reporter, title):
    return 'https://bugs.documentfoundation.org/show_bug.cgi?id={} reporter:{} -> "{}"'.format(id, reporter, title)



def util_formatGerrit(id, owner, title):
    return 'https://gerrit.libreoffice.org/#/c/{}/ author:{} -> "{}"'.format(id, owner, title)



def util_print_line(fp, loopList, title, doGerrit=False, doBugzilla=False, doName=None):
    print("\n\n" + title + ':', file=fp)
    for i in loopList:
      if doGerrit:
        x = 'https://gerrit.libreoffice.org/#/c/{}   {} -> "{}"'.format(i['id'], i['email'], i['title'])
      elif doBugzilla:
        x = 'https://bugs.documentfoundation.org/show_bug.cgi?id=' + i
      elif not doName is None:
        x = i + '    ' + doName[i]['name']
      else:
        x = i
      print('    ' + x, file=fp)



def util_build_escNumber(db, tag, statList):
    return str(statList['data'][db][tag]) + '(' + str(statList['data'][db][tag]) + ')'



def util_build_matrix(title, lineDesc, index, statList):
    xValue = [[title, '1 week', '', '1 month', '', '3 months', '', '12 months', '']]
    xLen = [len(xValue[0][0]), 0, 0, 0, 0, 0, 0, 0, 0]
    for row in lineDesc:
      xLine = [row['text']]
      for i in '1week', '1month', '3month', '1year':
        if index is None:
          x1 = statList['data'][row['db']][i][row['tag']]
          x2 = statList['diff'][row['db']][i][row['tag']]
        else:
          x1 = statList['data'][row['db']][index][i][row['tag']]
          x2 = statList['diff'][row['db']][index][i][row['tag']]
        xLine.append(str(x1))
        xLine.append('(' + str(x2) + ')')
      xValue.append(xLine)
      for i in range(0,9):
        x = len(xLine[i])
        if x > xLen[i]:
          xLen[i] = x
    xText = ''
    for i in 1, 3, 5, 7:
      x = len(xValue[0][i])
      if x > xLen[i]+xLen[i+1]:
        xLen[i+1] = x - xLen[i]
    for row in xValue:
      xText += ('        {:>' + str(xLen[0]) + '}  ').format(row[0])
      for i in 1,3,5,7:
        if row[2] == '':
          xText += (' {:<' + str(xLen[i]+xLen[i+1]) + '}  ').format(row[i])
        else:
          xText += ('   {:>' + str(xLen[i]) + '}{:<' + str(xLen[i+1]) + '}').format(row[i], row[i+1])
      xText += '\n'
    return xText



def report_mentoring(statList, openhubData, gerritData, gitData, bugzillaData, cfg):
    myStatList = {'missing_license': {},
                  'to_abandon': [],
                  'to_review': [],
                  'we_miss_you_email': [],
                  'remove_cc': [],
                  'needsDevEval': [],
                  'needsUXEval': [],
                  'missing_ui_cc': [],
                  'needinfo': [],
                  'to_unassign': [],
                  'assign_problem': [],
                  'too_many_comments': [],
                  'missing_cc': [],
                  'to_be_closed': [],
                  'easyhacks_new': [],
                  'top10commit': [],
                  'top10review': [],
                  'welcome_back_email': [],
                  'award_1st_email': []}

    mailedDate = datetime.datetime.strptime(cfg['git']['last-mail-run'], '%Y-%m-%d') - datetime.timedelta(days=90)
    zDate = datetime.datetime(year=2001, month=1, day=1)
    for i in statList['people']:
      row = statList['people'][i]
      if not row['hasLicense'] and row['isContributor'] and row['commits']['1month']['merged'] != 0:
        myStatList['missing_license'][row['email']] = row['name']
      if row['commits']['1year']['merged'] == row['commits']['1month']['merged'] and \
         row['commits']['1month']['merged'] != 0 and not row['email'] in cfg['contributor']['award-mailed']:
        myStatList['award_1st_email'].append(row['email'])

      newestCommitDate = datetime.datetime.strptime(row['newestCommit'], '%Y-%m-%d')
      prevCommitDate = datetime.datetime.strptime(row['prevCommit'], '%Y-%m-%d')
      if newestCommitDate >= mailedDate and \
         newestCommitDate < cfg['3monthDate']:
        myStatList['we_miss_you_email'].append(i)
      delta = newestCommitDate - prevCommitDate
      if delta > datetime.timedelta(days=180) and prevCommitDate != zDate and \
         newestCommitDate > cfg['1weekDate'] :
        myStatList['welcome_back_email'].append(i)

    for key in gerritData['patch']:
      row = gerritData['patch'][key]
      if row['status'] == 'SUBMITTED' or row['status'] == 'DRAFT':
        row['status'] = 'NEW'
      xDate = datetime.datetime.strptime(row['updated'], '%Y-%m-%d %H:%M:%S.%f000')
      ownerEmail = util_check_mail(row['owner']['email'], statList, cfg['contributor']['combine-email'])

      if row['status'] == 'NEW':
        doBlock = False
        cntReview = 0
        for x1 in 'Code-Review', 'Verified':
          for x in row['labels'][x1]['all']:
            if x['value'] == -2:
              doBlock = True
            if x['email'] != ownerEmail and x['email'] != 'ci@libreoffice.org':
              cntReview += 1
        if xDate < cfg['1monthDate'] and not doBlock:
            myStatList['to_abandon'].append({'id': key, 'email': row['owner']['email'], 'title': row['subject']})
        if cntReview == 0 and not statList['people'][ownerEmail]['isCommitter']:
          myStatList['to_review'].append({'id': key, 'email': row['owner']['email'], 'title': row['subject']})

    for key, row in bugzillaData['bugs'].items():
      if not 'cc' in row:
        row['cc'] = []
      if not 'keywords' in row:
        row['keywords'] = []

      if row['status'] == 'RESOLVED' or row['status'] == 'VERIFIED':
        continue

      if not 'easyHack' in row['keywords']:
        if 'jani' in row['cc']:
          myStatList['remove_cc'].append(key)
        continue

      if 'needsDevEval' in row['keywords']:
        myStatList['needsDevEval'].append(key)
      if 'needsUXEval' in row['keywords']:
        myStatList['needsUXEval'].append(key)
      if 'topicUI' in row['keywords'] and 'libreoffice-ux-advise@lists.freedesktop.org' not in row['cc']:
        myStatList['missing_ui_cc'].append(key)

      if row['status'] == 'NEEDINFO':
        myStatList['needinfo'].append(key)
      elif row['status'] == 'ASSIGNED':
        xDate = datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ")
        if xDate < cfg['1monthDate']:
          myStatList['to_unassign'].append(key)

      if (row['status'] == 'ASSIGNED' and row['assigned_to'] == '') or \
         (row['status'] != 'ASSIGNED' and row['assigned_to'] != '' and \
          row['assigned_to'] != 'libreoffice-bugs@lists.freedesktop.org') :
        myStatList['assign_problem'].append(key)

      if len(row['comments']) >= 5:
        myStatList['too_many_comments'].append(key)

      if not 'jani@documentfoundation.org' in row['cc']:
        myStatList['missing_cc'].append(key)

      if row['comments'][-1]['creator'] == 'libreoffice-commits@lists.freedesktop.org' and \
         not key in cfg['bugzilla']['close_except']:
        myStatList['to_be_closed'].append(key)

      cDate = datetime.datetime.strptime(row['creation_time'], "%Y-%m-%dT%H:%M:%SZ")
      if cDate >= cfg['1weekDate'] or 'easyhack' in row['history'][-1]['changes'][0]['added']:
        myStatList['easyhacks_new'].append(key)

    tmpClist = sorted(statList['people'], key=lambda k: (statList['people'][k]['commits']['1month']['merged']), reverse=True)
    for i in tmpClist:
      if not statList['people'][i]['isCommitter']:
        x = {'mail': i, 'name': statList['people'][i]['name'],
             'month' :statList['people'][i]['commits']['1month']['merged'],
             'year':statList['people'][i]['commits']['1year']['merged']}
        myStatList['top10commit'].append(x)
        if len(myStatList['top10commit']) >= 10:
          break
    tmpRlist = sorted(statList['people'], key=lambda k: (statList['people'][k]['gerrit']['1month']['reviewer']), reverse=True)
    for i in tmpRlist:
      if i != 'ci@libreoffice.org':
        x = {'mail': i, 'name': statList['people'][i]['name'],
             'month' :statList['people'][i]['gerrit']['1month']['reviewer'],
             'year':statList['people'][i]['gerrit']['1year']['reviewer']}
        myStatList['top10review'].append(x)
        if len(myStatList['top10review']) >= 10:
          break

    fp = open('/tmp/esc_mentoring_report.txt', 'w', encoding='utf-8')
    print('ESC mentoring report, generated {} based on stats.json from {}'.format(
           datetime.datetime.now().strftime("%Y-%m-%d"), statList['addDate']), file=fp)

    print("copy/paste to esc pad:\n"
          "* mentoring/easyhack update (janI)\n"
          "    + openhub statistics based on analysis from {}\n"
          "      {} people did in total: {} commits in {} lines of code\n"
          "      {} people did in 12 month: {} commits\n"
          "    + gerrit/git statistics:".format(
          statList['stat']['openhub_last_analyse'],
          util_build_escNumber('openhub', 'total_contributors', statList),
          util_build_escNumber('openhub', 'total_commits', statList),
          util_build_escNumber('openhub', 'lines_of_code', statList),
          util_build_escNumber('openhub', 'year_contributors', statList),
          util_build_escNumber('openhub', 'year_commits', statList)), file=fp)

    xRow = [{'db': 'gerrit',  'tag': 'NEW',       'text': 'open'},
            {'db': 'gerrit',  'tag': 'reviewed',  'text': 'reviews'},
            {'db': 'gerrit',  'tag': 'MERGED',    'text': 'merged'},
            {'db': 'gerrit',  'tag': 'ABANDONED', 'text': 'abandoned'},
            {'db': 'commits', 'tag': '#',         'text': 'commits'}]
    print(util_build_matrix('committer...', xRow, 'committer', statList), end='', file=fp)
    print(util_build_matrix('contributor...', xRow, 'contributor', statList), end='', file=fp)

    print("    + Distribution of people based on number of merged patches:", file=fp)
    xRow = [{'db': 'trendCommitter',  'tag': '1-5',    'text': '1-5'},
            {'db': 'trendCommitter',  'tag': '6-25',   'text': '6-25'},
            {'db': 'trendCommitter',  'tag': '26-50',  'text': '26-50'},
            {'db': 'trendCommitter',  'tag': '51-100', 'text': '51-100'},
            {'db': 'trendCommitter',  'tag': '100+',   'text': '100+'}]
    print(util_build_matrix('Committer distribution', xRow, None, statList), end='', file=fp)
    for i in xRow:
      i['db'] = 'trendContributor'
    print(util_build_matrix('Contributor distribution', xRow, None, statList), end='', file=fp)

    print("    + easyHack statistics:\n       ", end='', file=fp)
    for i1 in 'needsDevEval', 'needsUXEval', 'cleanup_comments', 'total', 'assigned', 'open':
      print(i1 + ' ' + util_build_escNumber('easyhacks', i1, statList) + '   ', end="", file=fp)
      if i1 == 'cleanup_comments':
        print('\n       ', end='', file=fp)
    print("\n    + received patches from " + str(len(myStatList['missing_license'])) + " emails the last month without licesense statement",  file=fp)
    print("    + top 5 contributors:", file=fp)
    for i in range(0, 5):
      print('          {} made {} patches in 1 month, and {} patches in 1 year'.format(
            myStatList['top10commit'][i]['name'],
            myStatList['top10commit'][i]['month'],
            myStatList['top10commit'][i]['year']), file=fp)
    print("    + top 5 reviewers:", file=fp)
    for i in range(0, 5):
      print('          {} made {} review comments in 1 month, and {} in 1 year'.format(
            myStatList['top10review'][i]['name'],
            myStatList['top10review'][i]['month'],
            myStatList['top10review'][i]['year']), file=fp)

    print("    + big CONGRATULATIONS to contributors who have at least 1 merged patch, since last report:", file=fp)
    for i in myStatList['award_1st_email']:
        print('          ' + statList['people'][i]['name'], file=fp)
    print("\n\n\n\n\n\n\n\n\n\n", file=fp)

    print('Day mentoring report, generated {} based on stats.json from {}'.format(
           datetime.datetime.now().strftime("%Y-%m-%d"), statList['addDate']), file=fp)

    util_print_line(fp, myStatList['welcome_back_email'], 'welcome back',              doName=statList['people'])
    util_print_line(fp, myStatList['missing_license'],    'missing license statement', doName=statList['people'])
    util_print_line(fp, myStatList['to_abandon'],         'gerrit to abandon',         doGerrit=True)
    util_print_line(fp, myStatList['to_review'],          'gerrit to review',          doGerrit=True)
    util_print_line(fp, myStatList['to_unassign'],        'easyhacks to unassign',     doBugzilla=True)
    util_print_line(fp, myStatList['needinfo'],           'easyhacks with NEEDINFO',     doBugzilla=True)
    util_print_line(fp, myStatList['easyhacks_new'],      'easyhacks new',             doBugzilla=True)
    util_print_line(fp, myStatList['missing_cc'],         'easyhacks missing cc',      doBugzilla=True)
    util_print_line(fp, myStatList['remove_cc'],          'easyhacks remove cc',       doBugzilla=True)
    util_print_line(fp, myStatList['missing_ui_cc'],      'easyhacks missing ui cc',   doBugzilla=True)
    util_print_line(fp, myStatList['assign_problem'],     'easyhacks assign problem',  doBugzilla=True)
    util_print_line(fp, myStatList['to_be_closed'],       'easyhacks to be closed',    doBugzilla=True)
    util_print_line(fp, myStatList['needsDevEval'],       'easyhacks needsDevEval',    doBugzilla=True)
    util_print_line(fp, myStatList['needsUXEval'],        'easyhacks needsUXEval',     doBugzilla=True)
    util_print_line(fp, myStatList['we_miss_you_email'],  'we miss you email',         doName=statList['people'])
    util_print_line(fp, myStatList['too_many_comments'],  'easyhacks reduce comments', doBugzilla=True)
    fp.close()

    return {'title': 'esc_mentoring, MENTORING', 'mail': 'jani@documentfoundation.org', 'file': '/tmp/esc_mentoring_report.txt'}



def report_ui(statList, openhubData, gerritData, gitData, bugzillaData, cfg):
    tmpClist = sorted(statList['people'], key=lambda k: (statList['people'][k]['ui']['1month']['total']), reverse=True)
    top10list = []
    for i in tmpClist:
      if i != 'qa-admin@libreoffice.org' and i != 'libreoffice-commits@lists.freedesktop.org':
        x = {'mail': i, 'name': statList['people'][i]['name'],
             'month' :statList['people'][i]['ui']['1month']['total'],
             'year':statList['people'][i]['ui']['1year']['total']}
        top10list.append(x)
        if len(top10list) >= 10:
          break

    fp = open('/tmp/esc_ui_report.txt', 'w', encoding='utf-8')
    print('ESC UI report, generated {} based on stats.json from {}'.format(
          datetime.datetime.now().strftime("%Y-%m-%d"), statList['addDate']), file=fp)

    print("copy/paste to esc pad:\n"
          "* UX update (heiko)\n"
          "    + Bugzilla (topicUI) statistics\n"
          "        {} (topicUI) bugs open, {} (needsUXEval) needs to be evaluated by the UXteam\n"
          "    + Updates:".format(
          util_build_escNumber('ui', 'topicUI', statList),
          util_build_escNumber('ui', 'needsUXEval', statList)), file=fp)

    xRow = [{'db': 'ui', 'tag': 'added',     'text': 'added'},
            {'db': 'ui', 'tag': 'commented', 'text': 'commented'},
            {'db': 'ui', 'tag': 'removed',   'text': 'removed'},
            {'db': 'ui', 'tag': 'resolved',  'text': 'resolved'}]
    print(util_build_matrix('BZ changes', xRow, None, statList), end='', file=fp)
#    print("    + Distribution of people based on number of changes:", file=fp)
#    xRow = [{'db': 'trendUI',  'tag': '1-5',    'text': '1-5'},
#            {'db': 'trendUI',  'tag': '6-25',   'text': '6-25'},
#            {'db': 'trendUI',  'tag': '26-50',  'text': '26-50'},
#            {'db': 'trendUI',  'tag': '51-100', 'text': '51-100'},
#            {'db': 'trendUI',  'tag': '100+',   'text': '100+'}]
#    print(util_build_matrix('distribution', xRow, None, statList), end='', file=fp)

    print("    + top 10 contributors:", file=fp)
    for i in range(0, 10):
      print('          {} made {} changes in 1 month, and {} changes in 1 year'.format(
            top10list[i]['name'], top10list[i]['month'], top10list[i]['year']), file=fp)
    fp.close()
    return {'title': 'esc_mentoring, UI', 'mail': 'jani@documentfoundation.org',
            'file': '/tmp/esc_ui_report.txt'}



def report_qa(statList, openhubData, gerritData, gitData, bugzillaData, cfg):
    tmpClist = sorted(statList['people'], key=lambda k: (statList['people'][k]['qa']['1month']['total']), reverse=True)
    top10list = []
    for i in tmpClist:
      if i != 'qa-admin@libreoffice.org' and i != 'libreoffice-commits@lists.freedesktop.org':
        x = {'mail': i, 'name': statList['people'][i]['name'],
             'month' :statList['people'][i]['qa']['1month']['total'],
             'year':statList['people'][i]['qa']['1year']['total']}
        top10list.append(x)
        if len(top10list) >= 10:
          break

    fp = open('/tmp/esc_qa_report.txt', 'w', encoding='utf-8')
    print('ESC QA report, generated {} based on stats.json from {}'.format(
          datetime.datetime.now().strftime("%Y-%m-%d"), statList['addDate']), file=fp)

    print("copy/paste to esc pad:\n"
          "* qa update (xisco)\n"
          "    + Bugzilla statistics", file=fp)

    xRow = [{'db': 'qa',  'tag': 'ASSIGNED',       'text': 'ASSIGNED'},
            {'db': 'qa',  'tag': 'CLOSED',  'text': 'CLOSED'},
            {'db': 'qa',  'tag': 'NEEDINFO',  'text': 'NEEDINFO'},
            {'db': 'qa',  'tag': 'NEW',  'text': 'NEW'},
            {'db': 'qa',  'tag': 'PLEASETEST',  'text': 'PLEASETEST'},
            {'db': 'qa',  'tag': 'REOPENED',  'text': 'REOPENED'},
            {'db': 'qa',  'tag': 'RESOLVED',  'text': 'RESOLVED'},
            {'db': 'qa',  'tag': 'UNCONFIRMED',  'text': 'UNCONFIRMED'},
            {'db': 'qa',  'tag': 'VERIFIED',  'text': 'VERIFIED'},
            {'db': 'qa',  'tag': 'commented',  'text': 'commented'},
            {'db': 'qa',  'tag': 'total',    'text': 'total'}]
    print(util_build_matrix('BZ changes', xRow, None, statList), end='', file=fp)
    print("    + Distribution of people based on number of changes:", file=fp)
    xRow = [{'db': 'trendQA',  'tag': '1-5',    'text': '1-5'},
            {'db': 'trendQA',  'tag': '6-25',   'text': '6-25'},
            {'db': 'trendQA',  'tag': '26-50',  'text': '26-50'},
            {'db': 'trendQA',  'tag': '51-100', 'text': '51-100'},
            {'db': 'trendQA',  'tag': '100+',   'text': '100+'}]
    print(util_build_matrix('distribution', xRow, None, statList), end='', file=fp)

    print("\n    + top 10 contributors:", file=fp)
    for i in range(0, 10):
      print('          {} made {} changes in 1 month, and {} changes in 1 year'.format(
            top10list[i]['mail'], top10list[i]['month'], top10list[i]['year']), file=fp)
    fp.close()
    return None



def report_myfunc(statList, openhubData, gerritData, gitData, bugzillaData, cfg):

   # {'title': 'mail from me', 'addr': 'my@own.home', 'file': '/tmp/myfile.txt'}
   return None



def DUMP_report(cfg, statList) :
  return
  tot = len(statList['list']['easyHacks_comments'])
  print('duming {} easyHacks with more than 5 comments:'.format(tot))
  x = 0
  for id in statList['list']['easyHacks_comments']:
    if x%10 == 0:
      print('dumping {} of {}'.format(x, tot))
    x += 1
    bug = get_bug(id)
    fileName = homeDir + 'bz_comments/bug_' + str(id) + '.json'
    try:
      fp = open(fileName, 'w')
      json.dump(bug, fp, ensure_ascii=False, indent=4, sort_keys=True)
    except:
      print("could not dump "+fileName)
      fp.close()
      os.remove(fileName)
      exit(-1)
    fp.close()
    fileName = homeDir + 'bz_comments/comment_' + str(id) + '.json'
    try:
      fp = open(fileName, 'w')
      json.dump(bug['long_desc'], fp, ensure_ascii=False, indent=4, sort_keys=True)
    except:
      print("could not dump "+fileName)
      fp.close()
      os.remove(fileName)
      exit(-1)
    fp.close()



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



def runReport(cfg):
    statList = util_load_data_file(cfg['homedir'] + 'stats.json')
    openhubData = util_load_data_file(cfg['homedir'] + 'dump/openhub_dump.json')
    bugzillaData = util_load_data_file(cfg['homedir'] + 'dump/bugzilla_dump.json')
    gerritData = util_load_data_file(cfg['homedir'] + 'dump/gerrit_dump.json')
    gitData = util_load_data_file(cfg['homedir'] + 'dump/git_dump.json')

    xMail = []
    x = report_mentoring(statList, openhubData, gerritData, gitData, bugzillaData, cfg)
    if not x is None:
      xMail.append(x)
    x = report_ui(statList, openhubData, gerritData, gitData, bugzillaData, cfg)
    if not x is None:
      xMail.append(x)
    x = report_qa(statList, openhubData, gerritData, gitData, bugzillaData, cfg)
    if not x is None:
      xMail.append(x)
    x = report_myfunc(statList, openhubData, gerritData, gitData, bugzillaData, cfg)
    if not x is None:
      xMail.append(x)

    fp = open('/tmp/runMail', 'w', encoding='utf-8')
    print("#!/bin/bash", file=fp)
    print("")
    for i in xMail:
      print("mail -s '" + i['title'] + "' " + i['mail'] + " <  " + i['file'], file=fp)
    fp.close()



if __name__ == '__main__':
    runReport(runCfg(sys.platform))
