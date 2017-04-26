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



def util_check_mail(xmail):
    global statList
    mail = xmail.lower()
    if mail in statList['aliases']:
      mail = statList['aliases'][mail]
    if not mail in statList['people']:
      return None
    else:
      return mail



def util_formatBugzilla(id, reporter, title):
    return 'https://bugs.documentfoundation.org/show_bug.cgi?id={} reporter:{} -> "{}"'.format(id, reporter, title)



def util_formatGerrit(id, owner, title):
    return 'https://gerrit.libreoffice.org/#/c/{}/ author:{} -> "{}"'.format(id, owner, title)



def util_print_line(fp, loopList, title, doGerrit=False, doBugzilla=False):
    print("\n\n" + title + ':', file=fp)
    for row in loopList:
      if doGerrit:
        x = 'https://gerrit.libreoffice.org/#/c/{}   {} -> "{}"'.format(row['id'], row['email'], row['title'])
      elif doBugzilla:
        x = 'https://bugs.documentfoundation.org/show_bug.cgi?id=' + row
      elif 'id' in row:
        x = '{} {} {} {}'.format(row['name'], row['email'], row['license'], row['id'])
      else:
        x = '{} {} {}'.format(row['name'], row['email'], row['license'])
      print('    ' + x, file=fp)



def util_build_escNumber(db, tag):
    global statList
    return str(statList['data'][db][tag]) + '(' + str(statList['data'][db][tag]) + ')'



def util_build_matrix(title, lineDesc, index):
    global statList
    xValue = [[title, '1 week', '', '1 month', '', '3 months', '', '12 months', '']]
    xLen = [len(xValue[0][0]), 0, 0, 0, 0, 0, 0, 0, 0]
    for row in lineDesc:
      xLine = [row['text']]
      for i in '1week', '1month', '3month', '1year':
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



def report_day_mentoring():
    global statList, openhubData, gerritData, gitData, bugzillaData, cfg
    myStatList = {'needsDevEval': [],
                  'needsUXEval': [],
                  'missing_ui_cc': [],
                  'needinfo': [],
                  'to_be_closed': [],
                  'easyhacks_new': [],
                  'to_unassign': [],
                  'too_many_comments': [],
                  'missing_cc': [],
                  'assign_problem': [],
                  'we_miss_you_email': [],
                  'award_1st_email': [],
                  'pending_license': [],
                  'missing_license': [],
                  'to_abandon' : [],
                  'to_review': [],
                  'remove_cc': []
                  }
    mailedDate = datetime.datetime.strptime(cfg['git']['last-mail-run'], '%Y-%m-%d') - datetime.timedelta(days=90)
    zeroDate = datetime.datetime(year=2001, month=1, day=1)
    for id, row in statList['people'].items():
      entry = {'name': row['name'], 'email': id, 'license': row['licenseText']}
      newestCommitDate = datetime.datetime.strptime(row['newestCommit'], '%Y-%m-%d')
      if newestCommitDate > mailedDate and newestCommitDate < cfg['3monthDate']:
        myStatList['we_miss_you_email'].append(entry)
      x = row['commits']['1month']['owner']
      if x != 0 and row['commits']['total'] == x and not id in cfg['award-mailed']:
        myStatList['award_1st_email'].append(entry)
      if row['licenseText'].startswith('PENDING'):
        myStatList['pending_license'].append(entry)

    for key,row in gerritData['patch'].items():
      if row['status'] == 'SUBMITTED' or row['status'] == 'DRAFT':
        row['status'] = 'NEW'
      xDate = datetime.datetime.strptime(row['updated'], '%Y-%m-%d %H:%M:%S.%f000')
      ownerEmail = util_check_mail(row['owner']['email'])
      entry = {'id': key, 'name': row['owner']['name'], 'email': ownerEmail, 'title': row['subject']}
      if row['status'] != 'ABANDONED':
        if ownerEmail is None:
          ownerEmail = row['owner']['email']
          entry['email'] = ownerEmail
          entry['license'] = 'GERRIT NO LICENSE'
          myStatList['missing_license'].append(entry)
        elif not statList['people'][ownerEmail]['licenseOK']:
          entry['license'] = 'GERRIT: ' + statList['people'][ownerEmail]['licenseText']
          myStatList['missing_license'].append(entry)

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
            myStatList['to_abandon'].append(entry)
        if cntReview == 0 and not statList['people'][ownerEmail]['isCommitter']:
          myStatList['to_review'].append(entry)

    for key,row in gitData['commits'].items():
      for i in 'author', 'committer':
        email = util_check_mail(row[i+'-email'])
        entry = {'id': key, 'name': row[i], 'email': email}
        if email is None:
          entry['email'] = row['author-email']
          entry['license'] = 'GIT AUTHOR NO LICENSE'
          myStatList['missing_license'].append(entry)
        elif not statList['people'][email]['licenseOK']:
          entry['license'] = 'GIT: ' + statList['people'][email]['licenseText']
          myStatList['missing_license'].append(entry)

    for key, row in bugzillaData['bugs'].items():
      if not 'cc' in row:
        row['cc'] = []
      if not 'keywords' in row:
        row['keywords'] = []

      if row['status'] == 'RESOLVED' or row['status'] == 'VERIFIED':
        continue

      if not 'easyHack' in row['keywords']:
        if 'mentoring' in row['cc']:
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
      if (row['status'] == 'ASSIGNED' and (row['assigned_to'] == '' or row['assigned_to'] == 'libreoffice-bugs@lists.freedesktop.org')) or \
         (row['status'] != 'ASSIGNED' and row['assigned_to'] != '' and row['assigned_to'] != 'libreoffice-bugs@lists.freedesktop.org') :
        myStatList['assign_problem'].append(key)
      if len(row['comments']) >= 5:
        myStatList['too_many_comments'].append(key)
      if not 'mentoring@documentfoundation.org' in row['cc']:
        myStatList['missing_cc'].append(key)
      if row['comments'][-1]['creator'] == 'libreoffice-commits@lists.freedesktop.org' and not key in cfg['bugzilla']['close_except']:
        myStatList['to_be_closed'].append(key)
      cDate = datetime.datetime.strptime(row['creation_time'], "%Y-%m-%dT%H:%M:%SZ")
      if cDate >= cfg['1weekDate'] or 'easyhack' in row['history'][-1]['changes'][0]['added']:
        myStatList['easyhacks_new'].append(key)

    fp = open('/tmp/esc_day_mentoring_report.txt', 'w', encoding='utf-8')
    print('Day mentoring report, generated {} based on stats.json from {}'.format(
          datetime.datetime.now().strftime("%Y-%m-%d"), statList['addDate']), file=fp)

    print(">> mail award pdf, and update award.json", file=fp)
    for row in myStatList['award_1st_email'] :
        print('        {} {} {}'.format(row['name'],row['email'],row['license']), file=fp)

    util_print_line(fp, myStatList['missing_license'],    'missing license statement'  )
    util_print_line(fp, myStatList['to_abandon'],         'gerrit to abandon',         doGerrit=True)
    util_print_line(fp, myStatList['to_review'],          'gerrit to review',          doGerrit=True)
    util_print_line(fp, myStatList['to_unassign'],        'easyhacks to unassign',     doBugzilla=True)
    util_print_line(fp, myStatList['needinfo'],           'easyhacks with NEEDINFO',   doBugzilla=True)
    util_print_line(fp, myStatList['easyhacks_new'],      'easyhacks new',             doBugzilla=True)
    util_print_line(fp, myStatList['missing_cc'],         'easyhacks missing cc',      doBugzilla=True)
    util_print_line(fp, myStatList['remove_cc'],          'easyhacks remove cc',       doBugzilla=True)
    util_print_line(fp, myStatList['missing_ui_cc'],      'easyhacks missing ui cc',   doBugzilla=True)
    util_print_line(fp, myStatList['assign_problem'],     'easyhacks assign problem',  doBugzilla=True)
    util_print_line(fp, myStatList['to_be_closed'],       'easyhacks to be closed',    doBugzilla=True)
    util_print_line(fp, myStatList['needsDevEval'],       'easyhacks needsDevEval',    doBugzilla=True)
    util_print_line(fp, myStatList['needsUXEval'],        'easyhacks needsUXEval',     doBugzilla=True)
    util_print_line(fp, myStatList['we_miss_you_email'],  'we miss you email'          )
    util_print_line(fp, myStatList['too_many_comments'],  'easyhacks reduce comments', doBugzilla=True)
    util_print_line(fp, myStatList['pending_license'],    'pending license statement'  )
    fp.close()
    return {'title': 'esc_mentoring, Daily work', 'mail': 'mentoring@documentfoundation.org', 'file': '/tmp/esc_day_mentoring_report.txt'}



def report_mentoring():
    global statList, openhubData, gerritData, gitData, bugzillaData, cfg
    myStatList = {'award_1st_email': [],
                  'top10commit': [],
                  'top10review': [],
                  }
    mailedDate = datetime.datetime.strptime(cfg['git']['last-mail-run'], '%Y-%m-%d') - datetime.timedelta(days=90)
    zeroDate = datetime.datetime(year=2001, month=1, day=1)
    for id, row in statList['people'].items():
      entry = {'name': row['name'], 'email': id, 'license': row['licenseText']}
      newestCommitDate = datetime.datetime.strptime(row['newestCommit'], '%Y-%m-%d')
      x = row['commits']['1month']['owner']
      if x != 0 and row['commits']['total'] == x and not id in cfg['award-mailed']:
        myStatList['award_1st_email'].append(entry)

    tmpClist = sorted(statList['people'], key=lambda k: (statList['people'][k]['commits']['1month']['owner']),reverse=True)
    for i in tmpClist:
        if not statList['people'][i]['isCommitter']:
            x = {'mail': i, 'name': statList['people'][i]['name'],
                 'month': statList['people'][i]['commits']['1month']['owner'],
                 'year': statList['people'][i]['commits']['1year']['owner']}
            myStatList['top10commit'].append(x)
            if len(myStatList['top10commit']) >= 10:
                break
    tmpRlist = sorted(statList['people'], key=lambda k: (statList['people'][k]['gerrit']['1month']['reviewer']),reverse=True)
    for i in tmpRlist:
        if i != 'ci@libreoffice.org':
            x = {'mail': i, 'name': statList['people'][i]['name'],
                 'month': statList['people'][i]['gerrit']['1month']['reviewer'],
                 'year': statList['people'][i]['gerrit']['1year']['reviewer']}
            myStatList['top10review'].append(x)
            if len(myStatList['top10review']) >= 10:
                break

    fp = open('/tmp/esc_mentoring_report.txt', 'w', encoding='utf-8')
    print("    + openhub statistics ({}), {} people did {} commits in 12 month in {} lines of code\n"
          "    + gerrit/git statistics:".format(
          statList['stat']['openhub_last_analyse'],
          util_build_escNumber('openhub', 'year_contributors'),
          util_build_escNumber('openhub', 'year_commits'),
          util_build_escNumber('openhub', 'lines_of_code')), file=fp)
    xRow = [{'db': 'gerrit',  'tag': 'NEW',          'text': 'open'},
            {'db': 'gerrit',  'tag': 'reviewed',     'text': 'reviews'},
            {'db': 'gerrit',  'tag': 'MERGED',       'text': 'merged'},
            {'db': 'gerrit',  'tag': 'ABANDONED',    'text': 'abandoned'},
            {'db': 'commits', 'tag': 'owner',        'text': 'own commits'},
            {'db': 'commits', 'tag': 'reviewMerged', 'text': 'review commits'}]
    print(util_build_matrix('committer...', xRow, 'committer'), end='', file=fp)
    print(util_build_matrix('contributor...', xRow, 'contributor'), end='', file=fp)
    print("    + easyHack statistics:\n       ", end='', file=fp)
    for i1 in 'needsDevEval', 'needsUXEval', 'cleanup_comments', 'total', 'assigned', 'open':
      print(i1 + ' ' + util_build_escNumber('easyhacks', i1) + '   ', end="", file=fp)
      if i1 == 'cleanup_comments':
        print('\n       ', end='', file=fp)
    print("\n    + top 5 contributors:", file=fp)
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
    for row in myStatList['award_1st_email']:
        print('          {} {} {}'.format(row['name'],row['email'],row['license']), file=fp)
    fp.close()
    return



def report_esc_prototype():
    global statList, cfg
    global text_bisected, text_bibisected, text_regression

    fp = open(cfg['homedir'] + '/esc-prototype.txt', encoding='utf-8')
    escPrototype = fp.read()
    fp.close()

    fp = open('/tmp/esc_ui_report.txt', encoding='utf-8')
    data = fp.read()
    fp.close()
    escPrototype = escPrototype.replace('$<ESC_UX_UPDATE>', data)

    fp = open('/tmp/esc_mentoring_report.txt', encoding='utf-8')
    data = fp.read()
    fp.close()
    escPrototype = escPrototype.replace('$<ESC_MENTORING_UPDATE>', data)

    fp = open('/tmp/esc_qa_ESC_report.txt', encoding='utf-8')
    data = fp.read()
    fp.close()
    escPrototype = escPrototype.replace('$<ESC_QA_UPDATE>', data)

    x1 = statList['data']['esc']['QAstat']['opened']
    x2 = statList['diff']['esc']['QAstat']['opened']
    x3 = statList['data']['esc']['QAstat']['closed']
    x4 = statList['diff']['esc']['QAstat']['closed']
    txt =  '      {:+d}  {:+d} ({:+d}) overall)\n      many thanks to the top bug squashers:\n'.format(
            x1, -x2, -x3, x4, x1 - x3, x2 - x4)
    x = statList['escList']['QAstat']['top15_squashers']
    for name, count in [(k, x[k]) for k in sorted(x, key=x.get, reverse=True)]:
      txt += '       {:<23} {}\n'.format(name, count)
    txt += '\n    + top 10 bugs reporters:\n'
    x = statList['escList']['QAstat']['top15_reporters']
    for name, count in [(k, x[k]) for k in sorted(x, key=x.get, reverse=True)]:
      txt += '       {:<23} {}\n'.format(name, count)
    txt += '\n    + top 10 bugs fixers:\n'
    x = statList['escList']['QAstat']['top15_reporters']
    for name, count in [(k, x[k]) for k in sorted(x, key=x.get, reverse=True)]:
      txt += '       {:<23} {}\n'.format(name, count)
    escPrototype = escPrototype.replace('$<ESC_QA_STATS_UPDATE>', txt)

    txt = ''
    oldRow = statList['data']['esc']['MAB']['old']
    del statList['data']['esc']['MAB']['old']
    keyList = sorted(statList['data']['esc']['MAB'], reverse=True)
    keyList.append('old')
    statList['data']['esc']['MAB']['old'] = oldRow
    for id in keyList:
      row = statList['data']['esc']['MAB'][id]
      diff = statList['diff']['esc']['MAB'][id]
      mab = '{} : {}/{} -'.format(id, row['open'], row['total'])
      txt += '     {:<16} {} %  ({:+d})\n'.format(mab, row['%'], diff['%'])
    escPrototype = escPrototype.replace('$<ESC_MAB_UPDATE>', txt)

    txt = '   + '
    for row in statList['escList']['bisect']:
      txt += str(row[0]) + '/' + str(row[1]) + ' '
    txt += '\n\n     done by:\n' + text_bisected
    escPrototype = escPrototype.replace('$<ESC_BISECTED_UPDATE>', txt)

    txt = '   + '
    for row in statList['escList']['bibisect']:
      txt += str(row[0]) + '/' + str(row[1]) + ' '
    txt += '\n\n     done by:\n' + text_bibisected
    escPrototype = escPrototype.replace('$<ESC_BIBISECTED_UPDATE>', txt)

    txt = '   + {}({:+d}) bugs open of {}({:+d}) total {}({:+d}) high prio.\n'.format(
        statList['data']['esc']['regression']['open'], statList['diff']['esc']['regression']['open'],
        statList['data']['esc']['regression']['total'], statList['diff']['esc']['regression']['total'],
        statList['data']['esc']['regression']['high'], statList['diff']['esc']['regression']['high'])
    txt += '\n     done by:\n' + text_regression
    escPrototype = escPrototype.replace('$<ESC_REGRESSION_UPDATE>', txt)

    x = statList['data']['esc']['component']['high']
    txt = ''
    for name, count in [(k, x[k]) for k in sorted(x, key=x.get, reverse=True)]:
      if name in ['LibreOffice', 'Impress', 'Base', 'Calc', 'Extensions', 'Writer']:
        txt += '     {:<13} - {}({:+d})\n'.format(
             name,
             count,
             statList['diff']['esc']['component']['high'][name])
    txt += '\n   by OS:\n'
    for id,row in statList['data']['esc']['component']['os'].items():
      idx = id.replace(' (All)', '')
      txt += '     {:<13} - {}({:+d})\n'.format(idx, row, statList['diff']['esc']['component']['os'][id])
    escPrototype = escPrototype.replace('$<ESC_COMPONENT_REGRESSION_HIGH_UPDATE>', txt)

    txt = ''
    x = statList['data']['esc']['component']['all']
    for id, row in [(k, x[k]) for k in sorted(x, key=x.get, reverse=True)]:
        if id != 'Writer':
          xDiff = statList['diff']['esc']['component']['all'][id]
          if row != 0 or xDiff != 0:
            txt += '     {:<24} - {}({:+d})\n'.format(id, row, xDiff)
    escPrototype = escPrototype.replace('$<ESC_COMPONENT_REGRESSION_ALL_UPDATE>', txt)

    fp = open('/tmp/esc_prototype_report.txt', 'w', encoding='utf-8')
    print('ESC prototype report, generated {} based on stats.json from {}\n\n\n'.format(
          datetime.datetime.now().strftime("%Y-%m-%d"), statList['addDate']), file=fp)
    print(escPrototype, file=fp)
    fp.close()

    data = 'ESC prototype, based on stats.json from '+statList['addDate']
    return {'title': data, 'mail': 'mentoring@documentfoundation.org', 'file': '/tmp/esc_prototype_report.txt'}



def report_flatODF():
    global statList, cfg

    filename = cfg['homedir'] + 'bug-metrics.fods'
    fp = open(filename, encoding='utf-8')
    text = fp.read()
    fp.close()


    rowHighPriority = \
       '<table:table-row table:style-name="ro2">\n' \
       '<table:table-cell table:style-name="isodate" office:value-type="date" office:date-value="{vDate}" calcext:value-type="date">\n' \
            '<text:p>{vDate}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vO_old}" calcext:value-type="float">\n' \
            '<text:p>{vO_old}</text:p></table:table-cell>\n' \
       '<table:table-cell table:style-name="Default" table:formula="of:=[.T74]-[.B74]" office:value-type="float" office:value="-1" calcext:value-type="float">\n' \
            '<text:p>-1</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vO_40}" calcext:value-type="float">\n' \
            '<text:p>{vO_40}</text:p></table:table-cell>\n' \
       '<table:table-cell table:style-name="Default" table:formula="of:=[.U74]-[.D74]" office:value-type="float" office:value="-1" calcext:value-type="float">\n' \
            '<text:p>-1</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vO_41}" calcext:value-type="float">\n' \
            '<text:p>{vO_41}</text:p></table:table-cell>\n' \
       '<table:table-cell table:style-name="Default" table:formula="of:=[.V74]-[.F74]" office:value-type="float" office:value="-1" calcext:value-type="float">\n' \
            '<text:p>-1</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vO_42}" calcext:value-type="float">\n' \
            '<text:p>{vO_42}</text:p></table:table-cell>\n' \
       '<table:table-cell table:style-name="Default" table:formula="of:=[.W74]-[.H74]" office:value-type="float" office:value="-1" calcext:value-type="float">\n' \
            '<text:p>-1</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vO_43}" calcext:value-type="float">\n' \
            '<text:p>{vO_43}</text:p></table:table-cell>\n' \
       '<table:table-cell table:style-name="Default" table:formula="of:=[.X74]-[.J74]" office:value-type="float" office:value="-1" calcext:value-type="float">\n' \
            '<text:p>-1</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vO_44}" calcext:value-type="float">\n' \
            '<text:p>{vO_44}</text:p></table:table-cell>\n' \
       '<table:table-cell table:style-name="Default" table:formula="of:=[.Y74]-[.L74]" office:value-type="float" office:value="-1" calcext:value-type="float">\n' \
            '<text:p>-1</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vO_50}" calcext:value-type="float">\n' \
            '<text:p>{vO_50}</text:p></table:table-cell>\n' \
       '<table:table-cell table:style-name="Default" table:formula="of:=[.Z74]-[.N74]" office:value-type="float" office:value="-1" calcext:value-type="float">\n' \
            '<text:p>-1</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vO_51}" calcext:value-type="float">\n' \
            '<text:p>{vO_51}</text:p></table:table-cell>\n' \
       '<table:table-cell table:style-name="Default" table:formula="of:=[.AA74]-[.P74]" office:value-type="float" office:value="-1" calcext:value-type="float">\n' \
            '<text:p>-1</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vO_52}" calcext:value-type="float">\n' \
            '<text:p>{vO_52}</text:p></table:table-cell>\n' \
       '<table:table-cell table:style-name="Default" table:formula="of:=[.AB74]-[.R74]" office:value-type="float" office:value="-1" calcext:value-type="float">\n' \
            '<text:p>-1</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vO_53}" calcext:value-type="float">\n' \
            '<text:p>{vO_53}</text:p></table:table-cell>\n' \
       '<table:table-cell table:style-name="Default" table:formula="of:=[.AI74]-[.T74]" office:value-type="float" office:value="-1" calcext:value-type="float">\n' \
            '<text:p>-1</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vO_54}" calcext:value-type="float">\n' \
            '<text:p>{vO_54}</text:p></table:table-cell>\n' \
       '<table:table-cell table:style-name="Default" table:formula="of:=[.AJ74]-[.V74]" office:value-type="float" office:value="-1" calcext:value-type="float">\n' \
            '<text:p>-1</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vO_55}" calcext:value-type="float">\n' \
            '<text:p>{vO_55}</text:p></table:table-cell>\n' \
       '<table:table-cell table:style-name="Default" table:formula="of:=[.AK74]-[.X74]" office:value-type="float" office:value="-1" calcext:value-type="float">\n' \
            '<text:p>-1</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vT_old}" calcext:value-type="float">\n' \
            '<text:p>{vT_old}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vT_40}" calcext:value-type="float">\n' \
            '<text:p>{vT_40}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vT_41}" calcext:value-type="float">\n' \
            '<text:p>{vT_41}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vT_42}" calcext:value-type="float">\n' \
            '<text:p>{vT_42}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vT_43}" calcext:value-type="float">\n' \
            '<text:p>{vT_43}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vT_44}" calcext:value-type="float">\n' \
            '<text:p>{vT_44}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vT_50}" calcext:value-type="float">\n' \
            '<text:p>{vT_50}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vT_51}" calcext:value-type="float">\n' \
            '<text:p>{vT_51}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vT_52}" calcext:value-type="float">\n' \
            '<text:p>{vT_52}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vT_53}" calcext:value-type="float">\n' \
       '<text:p>{vT_53}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vT_54}" calcext:value-type="float">\n' \
       '<text:p>{vT_54}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vT_55}" calcext:value-type="float">\n' \
       '<text:p>{vT_55}</text:p></table:table-cell>\n' \
       '<table:table-cell table:formula="of:=[.B74]+[.D74]+[.F74]+[.H74]+[.J74]+[.L74]+[.N74]+[.P74]+[.R74]+[.T74]+[.V74]+[.X74]" ' \
            'office:value-type="float" office:value="-1" calcext:value-type="float">' \
            '<text:p>-1</text:p></table:table-cell>' \
       '<table:table-cell table:style-name="ce24" table:formula="of:=SUM([.Z74:.AK74])-[.AL74]" ' \
            'office:value-type="float" office:value="-1" calcext:value-type="float">' \
            '<text:p>-1</text:p></table:table-cell>' \
       '</table:table-row>\n'.format(
              vDate  = statList['addDate'],
              vO_old = statList['data']['esc']['MAB']['old']['open'],
              vT_old = statList['data']['esc']['MAB']['old']['total'],
              vO_40  = statList['data']['esc']['MAB']['4.0']['open'],
              vT_40  = statList['data']['esc']['MAB']['4.0']['total'],
              vO_41  = statList['data']['esc']['MAB']['4.1']['open'],
              vT_41  = statList['data']['esc']['MAB']['4.1']['total'],
              vO_42  = statList['data']['esc']['MAB']['4.2']['open'],
              vT_42  = statList['data']['esc']['MAB']['4.2']['total'],
              vO_43  = statList['data']['esc']['MAB']['4.3']['open'],
              vT_43  = statList['data']['esc']['MAB']['4.3']['total'],
              vO_44  = statList['data']['esc']['MAB']['4.4']['open'],
              vT_44  = statList['data']['esc']['MAB']['4.4']['total'],
              vO_50  = statList['data']['esc']['MAB']['5.0']['open'],
              vT_50  = statList['data']['esc']['MAB']['5.0']['total'],
              vO_51  = statList['data']['esc']['MAB']['5.1']['open'],
              vT_51  = statList['data']['esc']['MAB']['5.1']['total'],
              vO_52  = statList['data']['esc']['MAB']['5.2']['open'],
              vT_52  = statList['data']['esc']['MAB']['5.2']['total'],
              vO_53  = statList['data']['esc']['MAB']['5.3']['open'],
              vT_53  = statList['data']['esc']['MAB']['5.3']['total'],
              vO_54  = 0,
              vT_54  = 0,
              vO_55  = 0,
              vT_55  = 0)

    rowRegressions = \
       '<table:table-row table:style-name="ro2">\n' \
       '<table:table-cell office:value-type="date" office:date-value="{vDate}" calcext:value-type="date">\n' \
            '<text:p>{vDate}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vOpen}" calcext:value-type="float">\n' \
            '<text:p>{vOpen}</text:p></table:table-cell>\n' \
       '<table:table-cell table:style-name="Default" table:formula="of:=[.D258]-[.B258]" office:value-type="float" ' \
            'office:value="-1" calcext:value-type="float">\n' \
            '<text:p>-1</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vTotal}" calcext:value-type="float">\n' \
            '<text:p>{vTotal}</text:p></table:table-cell>\n' \
       '<table:table-cell table:style-name="isodate" table:formula="of:=[.A258]" office:value-type="date" ' \
            'office:date-value="2001-01-01" calcext:value-type="date">\n' \
            '<text:p>2001-01-01</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vSpreadsheet}" calcext:value-type="float">\n' \
            '<text:p>{vSpreadsheet}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vPresentation}" calcext:value-type="float">\n' \
            '<text:p>{vPresentation}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vDatabase}" calcext:value-type="float">\n' \
            '<text:p>{vDatabase}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vDrawing}" calcext:value-type="float">\n' \
            '<text:p>{vDrawing}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vLibreOffice}" calcext:value-type="float">\n' \
            '<text:p>{vLibreOffice}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vBorders}" calcext:value-type="float">\n' \
            '<text:p>{vBorders}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vCrashes}" calcext:value-type="float">\n' \
            '<text:p>{vCrashes}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vBasic}" calcext:value-type="float">\n' \
            '<text:p>{vBasic}</text:p></table:table-cell>\n' \
       '<table:table-cell/>\n' \
       '<table:table-cell office:value-type="float" office:value="{vWriter}" calcext:value-type="float">\n' \
            '<text:p>{vWriter}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vMigration}" calcext:value-type="float">\n' \
            '<text:p>{vMigration}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vChart}" calcext:value-type="float">\n' \
            '<text:p>{vChart}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vExtensions}" calcext:value-type="float">\n' \
            '<text:p>{vExtensions}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vFormula}" calcext:value-type="float">\n' \
            '<text:p>{vFormula}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vImpressRemote}" calcext:value-type="float">\n' \
            '<text:p>{vImpressRemote}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vInstallation}" calcext:value-type="float">\n' \
            '<text:p>"{vInstallation}"</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vLinguistic}" calcext:value-type="float">\n' \
            '<text:p>{vLinguistic}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vPrinting}" calcext:value-type="float">\n' \
            '<text:p>{vPrinting}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vUI}" calcext:value-type="float">\n' \
            '<text:p>{vUI}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vFilters}" calcext:value-type="float">\n' \
            '<text:p>{vFilters}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vFramework}" calcext:value-type="float">\n' \
            '<text:p>{vFramework}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vGraphics}" calcext:value-type="float">\n' \
            '<text:p>{vGraphics}</text:p></table:table-cell>\n' \
       '<table:table-cell office:value-type="float" office:value="{vSdk}" calcext:value-type="float">\n' \
            '<text:p>{vSdk}</text:p></table:table-cell>\n' \
       '<table:table-cell table:formula="of:=[.A258]" office:value-type="date" ' \
            'office:date-value="2001-01-01" calcext:value-type="date">\n' \
            '<text:p>2001-01-01</text:p></table:table-cell>\n' \
       '<table:table-cell table:formula="of:=[.B258]-[.B257]" office:value-type="float" ' \
            'office:value="-1" calcext:value-type="float">\n' \
            '<text:p>-1</text:p></table:table-cell>\n' \
       '<table:table-cell table:formula="of:=[.D258]-[.D257]" office:value-type="float" ' \
            'office:value="-1" calcext:value-type="float">\n' \
            '<text:p>-1</text:p></table:table-cell>\n' \
       '<table:table-cell table:formula="of:=[.AE258]-[.AD258]" office:value-type="float" ' \
            'office:value="-1" calcext:value-type="float">\n' \
            '<text:p>-1</text:p></table:table-cell>\n' \
       '<table:table-cell table:number-columns-repeated="24"/>\n' \
       '</table:table-row>\n'.format(
              vDate  = statList['addDate'],
              vOpen  = 0,
              vTotal = 0,
              vSpreadsheet = 0,
              vPresentation = 0,
              vDatabase = 0,
              vDrawing = 0,
              vLibreOffice = 0,
              vBorders = 0,
              vCrashes = 0,
              vBasic = 0,
              vWriter = 0,
              vMigration = 0,
              vChart = 0,
              vExtensions = 0,
              vFormula = 0,
              vImpressRemote = 0,
              vInstallation = 0,
              vLinguistic = 0,
              vPrinting = 0,
              vUI = 0,
              vFilters = 0,
              vFramework = 0,
              vGraphics = 0,
              vSdk = 0
    )


    rowHighPrioRegressions = ''
#    <table:table-row table:style-name="ro2">
#     <table:table-cell table:style-name="ce14" office:value-type="date" office:date-value="2017-04-18" calcext:value-type="date">
#      <text:p>2017-04-18</text:p>
#     </table:table-cell>
#     <table:table-cell office:value-type="float" office:value="1" calcext:value-type="float">
#      <text:p>1</text:p>
#     </table:table-cell>
#     <table:table-cell table:number-columns-repeated="2" office:value-type="float" office:value="2" calcext:value-type="float">
#      <text:p>2</text:p>
#     </table:table-cell>
#     <table:table-cell/>
#     <table:table-cell office:value-type="float" office:value="4" calcext:value-type="float">
#      <text:p>4</text:p>
#     </table:table-cell>
#     <table:table-cell table:number-columns-repeated="4"/>
#     <table:table-cell office:value-type="float" office:value="1" calcext:value-type="float">
#      <text:p>1</text:p>
#     </table:table-cell>
#     <table:table-cell table:number-columns-repeated="2"/>
#     <table:table-cell office:value-type="float" office:value="1" calcext:value-type="float">
#      <text:p>1</text:p>
#     </table:table-cell>
#     <table:table-cell table:number-columns-repeated="10"/>
#    </table:table-row>

    endIndex = 0
    searchStartSheet = '<table:table table:name='
    lenStartSheet = len(searchStartSheet)
    while True:
      startIndex = text.find(searchStartSheet, endIndex) + lenStartSheet
      if startIndex <= lenStartSheet:
        break
      endIndex = text.find('</table:table>', startIndex)

      if text[startIndex:].startswith('"local-table"'):
        # no handling
        continue
      elif text[startIndex:].startswith('"Charts"'):
        # no handling
        continue
      elif text[startIndex:].startswith('"Legacy"'):
        # no handling
        continue
      elif text[startIndex:].startswith('"HighPriority"'):
        inx  = text.rfind('<table:table-row table:style-name="ro2" table:number-rows-repeated="39">', startIndex, endIndex)
        text = text[:inx] + '\n\n' + rowHighPriority + '\n\n' + text[inx:]
      elif text[startIndex:].startswith('"Regressions"'):
        print("handling Regressions")
      elif text[startIndex:].startswith('"HighPrioRegressions"'):
        print("handling HighPrioRegressions")
      else:
        raise Exception("unknown sheet in bug-metrics: " + text[startIndex:startIndex+20])

    fp = open(cfg['homedir'] + 'bug-test.fods', 'w', encoding='utf-8')
    print(text, file=fp)
    fp.close()
    data = 'ESC bug_metric.fods, based on stats.json from '+statList['addDate']
    return {'title': data, 'mail': 'mentoring@documentfoundation.org', 'attach': '/tmp/esc_flatODF.fods', 'file' : '/tmp/esc_flatODF_body'}


def report_ui():
    global statList, openhubData, gerritData, gitData, bugzillaData, cfg
    tmpClist = sorted(statList['people'], key=lambda k: (statList['people'][k]['ui']['1month']['history']+statList['people'][k]['ui']['1month']['commented']), reverse=True)
    top10list = []
    for i in tmpClist:
      if i != 'qa-admin@libreoffice.org' and i != 'libreoffice-commits@lists.freedesktop.org':
        xYear = statList['people'][i]['ui']['1year']['history'] + statList['people'][i]['ui']['1year']['commented']
        xMonth = statList['people'][i]['ui']['1month']['history'] + statList['people'][i]['ui']['1month']['commented']
        x = {'mail': i, 'name': statList['people'][i]['name'],
             'month' : xMonth,
             'year': xYear}
        top10list.append(x)
        if len(top10list) >= 10:
          break

    fp = open('/tmp/esc_ui_report.txt', 'w', encoding='utf-8')
    print("    + Bugzilla (topicUI) statistics\n"
          "        {} (topicUI) bugs open, {} (needsUXEval) needs to be evaluated by the UXteam\n"
          "    + Updates:".format(
          util_build_escNumber('ui', 'topicUI'),
          util_build_escNumber('ui', 'needsUXEval')), file=fp)

    xRow = [{'db': 'ui', 'tag': 'added',     'text': 'added'},
            {'db': 'ui', 'tag': 'commented', 'text': 'commented'},
            {'db': 'ui', 'tag': 'removed',   'text': 'removed'},
            {'db': 'ui', 'tag': 'resolved',  'text': 'resolved'}]
    print(util_build_matrix('BZ changes', xRow, 'contributor'), end='', file=fp)
    print("    + top 10 contributors:", file=fp)
    for i in range(0, 10):
      print('          {} made {} changes in 1 month, and {} changes in 1 year'.format(
            top10list[i]['name'], top10list[i]['month'], top10list[i]['year']), file=fp)
    fp.close()
    return {'title': 'ESC UI report', 'mail': 'tietze.heiko@gmail.com', 'file': '/tmp/esc_prototype_report.txt'}



def report_qa():
    global statList, openhubData, gerritData, gitData, bugzillaData, cfg
    global text_bisected, text_bibisected, text_regression


    fpESC = open('/tmp/esc_qa_ESC_report.txt', 'w', encoding='utf-8')
    fp = open('/tmp/esc_qa_report.txt', 'w', encoding='utf-8')
    print('ESC QA report, generated {} based on stats.json from {}'.format(
          datetime.datetime.now().strftime("%Y-%m-%d"), statList['addDate']), file=fp)

    print("copy/paste to esc pad:\n"
          "* qa update (xisco)\n", file=fp)

    text = "    + UNCONFIRMED: {} ({:+d})\n" \
        "        + enhancements: {}  ({:+d})\n" \
        "        + needsUXEval: {} ({:+d})\n" \
        "        + haveBackTrace: {} ({:+d})\n" \
        "        + needsDevAdvice: {} ({:+d})\n" \
        "        + documentation:  {} ({:+d})\n".format(
                    statList['data']['qa']['unconfirmed']['count'],
                    statList['diff']['qa']['unconfirmed']['count'],
                    statList['data']['qa']['unconfirmed']['enhancement'],
                    statList['diff']['qa']['unconfirmed']['enhancement'],
                    statList['data']['qa']['unconfirmed']['needsUXEval'],
                    statList['diff']['qa']['unconfirmed']['needsUXEval'],
                    statList['data']['qa']['unconfirmed']['haveBacktrace'],
                    statList['diff']['qa']['unconfirmed']['haveBacktrace'],
                    statList['data']['qa']['unconfirmed']['needsDevAdvice'],
                    statList['diff']['qa']['unconfirmed']['needsDevAdvice'],
                    statList['data']['qa']['unconfirmed']['documentation'],
                    statList['diff']['qa']['unconfirmed']['documentation'])
    print(text, file=fp)
    print(text, file=fpESC)

    reporters = sorted(statList['people'], key=lambda k: (statList['people'][k]['qa']['1week']['owner']), reverse=True)

    print("\n  + top 10 bugs reporters:", file=fp)
    top10reporters = reporters[0:10]
    max_width = 20
    for i in top10reporters:
      if statList['people'][i]['qa']['1week']['owner'] == 0:
        break
      max_width = max(max_width, len(statList['people'][i]['name']))

    for item in top10reporters:
      if statList['people'][item]['qa']['1week']['owner'] == 0:
        break
      if not statList['people'][item]['name'] or statList['people'][item]['name'] == '*UNKNOWN*':
        statList['people'][item]['name'] = statList['people'][item]['email'].split('@')[0]
      print('        {0:{2}s} {1:3d}'.format(
            statList['people'][item]['name'], statList['people'][item]['qa']['1week']['owner'],
            max_width), file=fp)

    fixers = sorted(statList['people'], key=lambda k: (statList['people'][k]['qa']['1week']['fixed']), reverse=True)

    print("\n  + top 10 bugs fixers:", file=fp)
    top10fixers = fixers[0:10]
    max_width = 20
    for i in top10fixers:
      if statList['people'][i]['qa']['1week']['fixed'] == 0:
        break
      max_width = max(max_width, len(statList['people'][i]['name']))

    for item in top10fixers:
      if statList['people'][item]['qa']['1week']['fixed'] == 0:
        break
      if not statList['people'][item]['name'] or statList['people'][item]['name'] == '*UNKNOWN*':
        statList['people'][item]['name'] = statList['people'][item]['email'].split('@')[0]
      print('        {0:{2}s} {1:3d}'.format(
            statList['people'][item]['name'], statList['people'][item]['qa']['1week']['fixed'],
            max_width), file=fp)


    bisected = sorted(statList['people'], key=lambda k: (statList['people'][k]['qa']['1week']['bisected']), reverse=True)

    print("\nBisected", file=fp)
    print("\n  + Done by:", file=fp)
    top10bisected = bisected[0:10]
    max_width = 20
    for i in top10bisected:
      if statList['people'][i]['qa']['1week']['bisected'] == 0:
        break
      max_width = max(max_width, len(statList['people'][i]['name']))

    text_bisected = ''
    for item in top10bisected:
      if statList['people'][item]['qa']['1week']['bisected'] == 0:
        break
      if not statList['people'][item]['name'] or statList['people'][item]['name'] == '*UNKNOWN*':
        statList['people'][item]['name'] = statList['people'][item]['email'].split('@')[0]
      text_bisected += '        {0:{2}s} {1:3d}\n'.format(
            statList['people'][item]['name'], statList['people'][item]['qa']['1week']['bisected'],
            max_width)
    print(text_bisected, file=fp)

    bibisected = sorted(statList['people'], key=lambda k: (statList['people'][k]['qa']['1week']['bibisected']), reverse=True)

    print("\nBibisected", file=fp)
    print("\n  + Done by:", file=fp)
    top10bibisected = bibisected[0:10]
    max_width = 20
    for i in top10bibisected:
      if statList['people'][i]['qa']['1week']['bibisected'] == 0:
        break
      max_width = max(max_width, len(statList['people'][i]['name']))

    text_bibisected = ''
    for item in top10bibisected:
      if statList['people'][item]['qa']['1week']['bibisected'] == 0:
        break
      if not statList['people'][item]['name'] or statList['people'][item]['name'] == '*UNKNOWN*':
        statList['people'][item]['name'] = statList['people'][item]['email'].split('@')[0]
      text_bibisected += '        {0:{2}s} {1:3d}\n'.format(
            statList['people'][item]['name'], statList['people'][item]['qa']['1week']['bibisected'],
            max_width)
    print(text_bibisected, file=fp)

    regression = sorted(statList['people'], key=lambda k: (statList['people'][k]['qa']['1week']['regression']), reverse=True)

    print("\nRegressions", file=fp)
    print("\n  + Done by:", file=fp)
    top10regression = regression[0:10]
    max_width = 20
    for i in top10regression:
      if statList['people'][i]['qa']['1week']['regression'] == 0:
        break
      max_width = max(max_width, len(statList['people'][i]['name']))

    text_regression = ''
    for item in top10regression:
      if statList['people'][item]['qa']['1week']['regression'] == 0:
        break
      if not statList['people'][item]['name'] or statList['people'][item]['name'] == '*UNKNOWN*':
        statList['people'][item]['name'] = statList['people'][item]['email'].split('@')[0]
      text_regression += '        {0:{2}s} {1:3d}\n'.format(
            statList['people'][item]['name'], statList['people'][item]['qa']['1week']['regression'],
            max_width)
    print(text_regression, file=fp)

    backtrace = sorted(statList['people'], key=lambda k: (statList['people'][k]['qa']['1week']['backtrace']), reverse=True)

    print("\nBacktrace", file=fp)
    print("\n  + Done by:", file=fp)
    top10backtrace = backtrace[0:10]
    max_width = 20
    for i in top10backtrace:
      if statList['people'][i]['qa']['1week']['backtrace'] == 0:
        break
      max_width = max(max_width, len(statList['people'][i]['name']))

    for item in top10backtrace:
      if statList['people'][item]['qa']['1week']['backtrace'] == 0:
        break
      if not statList['people'][item]['name'] or statList['people'][item]['name'] == '*UNKNOWN*':
        statList['people'][item]['name'] = statList['people'][item]['email'].split('@')[0]
      print('        {0:{2}s} {1:3d}'.format(
            statList['people'][item]['name'], statList['people'][item]['qa']['1week']['backtrace'],
            max_width), file=fp)

    fp.close()
    fpESC.close()
    return {'title': 'esc_report, QA', 'mail': 'xiscofauli@libreoffice.org',
            'file': '/tmp/esc_qa_report.txt'}


def report_myfunc():
   global statList, openhubData, gerritData, gitData, bugzillaData, cfg

   # {'title': 'mail from me', 'addr': 'my@own.home', 'file': '/tmp/myfile.txt'}
   return None



def DUMP_report() :
  global cfg, statList
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
    global cfg
    if 'esc_homedir' in os.environ:
      homeDir = os.environ['esc_homedir']
    else:
      homeDir = '/home/esc-mentoring/esc'

    cfg = util_load_data_file(homeDir + '/config.json')
    cfg['homedir'] = homeDir + '/'
    cfg['platform'] = platform
    print("Reading and writing data to " + cfg['homedir'])

    cfg['award-mailed'] = util_load_data_file(cfg['homedir'] + 'award.json')['award-mailed']
    cfg['nowDate'] = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    cfg['cutDate'] = cfg['nowDate'] - datetime.timedelta(days=365)
    cfg['1weekDate'] = cfg['nowDate'] - datetime.timedelta(days=7)
    cfg['1monthDate'] = cfg['nowDate'] - datetime.timedelta(days=30)
    cfg['3monthDate'] = cfg['nowDate'] - datetime.timedelta(days=90)
    cfg['1yearDate'] = cfg['nowDate'] - datetime.timedelta(days=365)
    return cfg



def runReport():
    global cfg, statList, openhubData, bugzillaData, gerritData, gitData

    statList = util_load_data_file(cfg['homedir'] + 'stats.json')
    openhubData = util_load_data_file(cfg['homedir'] + 'dump/openhub_dump.json')
    bugzillaData = util_load_data_file(cfg['homedir'] + 'dump/bugzilla_dump.json')
    gerritData = util_load_data_file(cfg['homedir'] + 'dump/gerrit_dump.json')
    gitData = util_load_data_file(cfg['homedir'] + 'dump/git_dump.json')

    xMail = []
    x = report_day_mentoring()
    if not x is None:
      xMail.append(x)
    x = report_mentoring()
    if not x is None:
      xMail.append(x)
    x = report_ui()
    if not x is None:
      xMail.append(x)
    x = report_qa()
    if not x is None:
      xMail.append(x)
    x = report_myfunc()
    if not x is None:
      xMail.append(x)
    x = report_esc_prototype()
    if not x is None:
      xMail.append(x)
    x = report_flatODF()
    if not x is None:
      xMail.append(x)

    fp = open('/tmp/runMail', 'w', encoding='utf-8')
    print("#!/bin/bash", file=fp)
    print("")
    for i in xMail:
      if 'attach' in i:
        attach = '-a ' + i['attach'] + ' '
      else:
        attach = ''
      print("mail -s '" + i['title'] + "' " + attach + i['mail'] + " <  " + i['file'], file=fp)
    fp.close()



if __name__ == '__main__':
    runCfg(sys.platform)
    runReport()
