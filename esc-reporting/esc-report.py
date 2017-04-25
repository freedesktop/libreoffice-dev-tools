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

    fp = open('/tmp/esc_qa_report.txt', encoding='utf-8')
    data = fp.read()
    fp.close()
    escPrototype = escPrototype.replace('$<ESC_QA_UPDATE>', data)

    x1 = statList['data']['esc']['QAstat']['opened']
    x2 = statList['diff']['esc']['QAstat']['opened']
    x3 = statList['data']['esc']['QAstat']['closed']
    x4 = statList['diff']['esc']['QAstat']['closed']
    txt =  '      {:+d}({:+d})  {:+d}({:+d})   ({:+d}({:+d}) overall)\n      many thanks to the top bug squashers:\n'.format(
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

    txt = ''
    for i in ['LibreOffice', 'Impress', 'Base', 'Calc', 'Extensions', 'Writer']:
      txt += '     {:<13} - {}({:+d})\n'.format(
             i,
             statList['data']['esc']['component']['high'][i],
             statList['diff']['esc']['component']['high'][i])
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

    fp = open('/tmp/esc_flatODF.fods', 'w', encoding='utf-8')
    print('<?xml version="1.0" encoding="UTF-8"?>' +
          '<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" ' +
          'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" ' +
          'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" ' +
          'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" ' +
          'xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" ' +
          'xmlns:calcext="urn:org:documentfoundation:names:experimental:calc:xmlns:calcext:1.0" ' +
          'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" ' +
          'xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:dc="http://purl.org/dc/elements/1.1/" ' +
          'xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" ' +
          'xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0" ' +
          'xmlns:presentation="urn:oasis:names:tc:opendocument:xmlns:presentation:1.0" ' +
          'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" ' +
          'xmlns:chart="urn:oasis:names:tc:opendocument:xmlns:chart:1.0" ' +
          'xmlns:dr3d="urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0" ' +
          'xmlns:math="http://www.w3.org/1998/Math/MathML" ' +
          'xmlns:form="urn:oasis:names:tc:opendocument:xmlns:form:1.0" ' +
          'xmlns:script="urn:oasis:names:tc:opendocument:xmlns:script:1.0" ' +
          'xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0" ' +
          'xmlns:ooo="http://openoffice.org/2004/office" ' +
          'xmlns:ooow="http://openoffice.org/2004/writer" ' +
          'xmlns:oooc="http://openoffice.org/2004/calc" ' +
          'xmlns:dom="http://www.w3.org/2001/xml-events" ' +
          'xmlns:xforms="http://www.w3.org/2002/xforms" ' +
          'xmlns:xsd="http://www.w3.org/2001/XMLSchema" ' +
          'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' +
          'xmlns:rpt="http://openoffice.org/2005/report" ' +
          'xmlns:of="urn:oasis:names:tc:opendocument:xmlns:of:1.2" ' +
          'xmlns:xhtml="http://www.w3.org/1999/xhtml" ' +
          'xmlns:grddl="http://www.w3.org/2003/g/data-view#" ' +
          'xmlns:tableooo="http://openoffice.org/2009/table" ' +
          'xmlns:field="urn:openoffice:names:experimental:ooo-ms-interop:xmlns:field:1.0" ' +
          'xmlns:formx="urn:openoffice:names:experimental:ooxml-odf-interop:xmlns:form:1.0" ' +
          'xmlns:css3t="http://www.w3.org/TR/css3-text/" ' +
          'office:version="1.2" ' +
          'grddl:transformation="http://docs.oasis-open.org/office/1.2/xslt/odf2rdf.xsl" ' +
          'office:mimetype="application/vnd.oasis.opendocument.spreadsheet">' +
          '\n', file=fp)

    print('<office:styles>' +
          '<style:style style:name="boldheader" style:family="table-cell" style:parent-style-name="Default">' +
          '<style:text-properties fo:font-style="italic" fo:font-weight="bold"/>' +
          '</style:style>' +
          '<number:date-style style:name="isodatenum">' +
          '<number:year number:style="long"/>' +
          '<number:text>-</number:text>' +
          '<number:month number:style="long"/>' +
          '<number:text>-</number:text>' +
          '<number:day number:style="long"/>' +
          '</number:date-style>' +
          '<style:style style:name="isodate" style:family="table-cell" style:parent-style-name="Default" style:data-style-name="isodatenum">' +
          '<style:text-properties style:text-position=""/>' +
          '</style:style>' +
          '</office:styles>' +
          '\n', file=fp)

    print('<office:body>' +
          '<office:spreadsheet>' +
          '<table:table table:name="Data">' +
          '<table:table-row table:style-name="ro2">' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Date</text:p></table:table-cell>' 
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Open Old</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Closed Old</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Open 4.0</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Closed 4.0</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Open 4.1</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Closed 4.1</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Open 4.2</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Closed 4.2</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Open 4.3</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Closed 4.3</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Open 4.4</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Closed 4.4</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Open 5.0</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Closed 5.0</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Open 5.1</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Closed 5.1</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Open 5.2</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Closed 5.2</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Total Old</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Total 4.0</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Total 4.1</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Total 4.2</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Total 4.3</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Total 4.4</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Total 5.0</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Total 5.1</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Total 5.2</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Total Open</text:p></table:table-cell>' +
          '<table:table-cell office:value-type="string" calcext:value-type="string">' +
          '<text:p>Total Closed</text:p></table:table-cell>' +
          '<table:table-cell table:number-columns-repeated="11"/></table:table-row>' +
          '\n', file=fp)

    print('<table:table-row table:style-name="ro1">' +
          '<table:table-cell table:style-name="isodate" office:value-type="date" office:date-value="' +
          statList['addDate'] + '" calcext:value-type="date"><text:p>' +
          statList['addDate'] + '</text:p></table:table-cell>' +
          '\n', file=fp)

    print('<table:table-cell office:value-type="float" office:value="' +
          str(statList['data']['esc']['MAB']['old']['open']) + '" calcext:value-type="float"/>' +
          '<table:table-cell table:formula="of:=[.T2]-[.B2]" office:value-type="float"  calcext:value-type="float"/>' +
          '<table:table-cell office:value-type="float" office:value="' +
          str(statList['data']['esc']['MAB']['4.0']['open']) + '" calcext:value-type="float"/>' +
          '<table:table-cell table:formula="of:=[.U2]-[.D2]" office:value-type="float"  calcext:value-type="float"/>' +
          '<table:table-cell office:value-type="float" office:value="' +
          str(statList['data']['esc']['MAB']['4.1']['open']) + '" calcext:value-type="float"/>' +
          '<table:table-cell table:formula="of:=[.V2]-[.F2]" office:value-type="float"  calcext:value-type="float"/>' +
          '<table:table-cell office:value-type="float" office:value="' +
          str(statList['data']['esc']['MAB']['4.2']['open']) + '" calcext:value-type="float"/>' +
          '<table:table-cell table:formula="of:=[.W2]-[.H2]" office:value-type="float"  calcext:value-type="float"/>' +
          '<table:table-cell office:value-type="float" office:value="' +
          str(statList['data']['esc']['MAB']['4.3']['open']) + '" calcext:value-type="float"/>' +
          '<table:table-cell table:formula="of:=[.X2]-[.J2]" office:value-type="float"  calcext:value-type="float"/>' +
          '<table:table-cell office:value-type="float" office:value="' +
          str(statList['data']['esc']['MAB']['4.4']['open']) + '" calcext:value-type="float"/>' +
          '<table:table-cell table:formula="of:=[.Y2]-[.L2]" office:value-type="float"  calcext:value-type="float"/>' +
          '<table:table-cell office:value-type="float" office:value="' +
          str(statList['data']['esc']['MAB']['5.0']['open']) + '" calcext:value-type="float"/>' +
          '<table:table-cell table:formula="of:=[.Z2]-[.N2]" office:value-type="float"  calcext:value-type="float"/>' +
          '<table:table-cell office:value-type="float" office:value="' +
          str(statList['data']['esc']['MAB']['5.1']['open']) + '" calcext:value-type="float"/>' +
          '<table:table-cell table:formula="of:=[.AA2]-[.P2]" office:value-type="float"  calcext:value-type="float"/>' +
          '<table:table-cell office:value-type="float" office:value="' +
          str(statList['data']['esc']['MAB']['5.2']['open']) + '" calcext:value-type="float"/>' +
          '<table:table-cell table:formula="of:=[.AB2]-[.R2]" office:value-type="float"  calcext:value-type="float"/>' +
          '<table:table-cell office:value-type="float" office:value="' +
          str(statList['data']['esc']['MAB']['old']['total']) + '" calcext:value-type="float"/>' +
          '<table:table-cell office:value-type="float" office:value="' +
          str(statList['data']['esc']['MAB']['4.0']['total']) + '" calcext:value-type="float"/>' +
          '<table:table-cell office:value-type="float" office:value="' +
          str(statList['data']['esc']['MAB']['4.1']['total']) + '" calcext:value-type="float"/>' +
          '<table:table-cell office:value-type="float" office:value="' +
          str(statList['data']['esc']['MAB']['4.2']['total']) + '" calcext:value-type="float"/>' +
          '<table:table-cell office:value-type="float" office:value="' +
          str(statList['data']['esc']['MAB']['4.3']['total']) + '" calcext:value-type="float"/>' +
          '<table:table-cell office:value-type="float" office:value="' +
          str(statList['data']['esc']['MAB']['4.4']['total']) + '" calcext:value-type="float"/>' +
          '<table:table-cell office:value-type="float" office:value="' +
          str(statList['data']['esc']['MAB']['5.0']['total']) + '" calcext:value-type="float"/>' +
          '<table:table-cell office:value-type="float" office:value="' +
          str(statList['data']['esc']['MAB']['5.1']['total']) + '" calcext:value-type="float"/>' +
          '<table:table-cell office:value-type="float" office:value="' +
          str(statList['data']['esc']['MAB']['5.2']['total']) + '" calcext:value-type="float"/>' +
          '<table:table-cell table:style-name="ce3" table:formula="of:=[.B2]+[.D2]+[.F2]+[.H2]+[.J2]+[.L2]+[.N2]+[.P2]+[.R2]" office:value-type="float"/>' +
          '<table:table-cell table:style-name="ce3" table:formula="of:=SUM([.T2:.Z2])-[.AC2]" office:value-type="float"/>' +
          '</table:table-row>' +
          '\n', file=fp)

    print('<table:table-row/>' +
          '<table:table-row>' +
          '<table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">' +
          '<text:p>Date</text:p>' +
          '</table:table-cell>' +
          '<table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">' +
          '<text:p>Open</text:p>' +
          '</table:table-cell>' +
          '<table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">' +
          '<text:p>Closed</text:p>' +
          '</table:table-cell>' +
          '<table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">' +
          '<text:p>Total</text:p>' +
          '</table:table-cell>' +
          '<table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string">' +
          '<text:p>Date</text:p>' +
          '</table:table-cell>' +
          '\n', file=fp)


    myOrder = ['Calc', 'Impress', 'Base', 'Draw', 'LibreOffice', 'Borders', 'Crashes', 'BASIC', 'Writer/RTF', 'Writer',
               'Migration', 'Chart', 'Extensions', 'Formula Editor', 'Impress Remote', 'Installation', 'Linguistic',
               'Printing and PDF export', 'UI', 'filters and storage', 'framework', 'graphics stack', 'sdk']
    for i in myOrder:
        print('<table:table-cell table:style-name="boldheader" office:value-type="string" calcext:value-type="string"><text:p>' +
              i + '</text:p></table:table-cell>' +
              '\n', file=fp)
    print('</table:table-row>' +
          '<table:table-row>' +
          '<table:table-cell table:style-name="isodate" office:value-type="date" office:date-value="' +
          statList['addDate'] +
          '" calcext:value-type="date"><text:p>' +
          statList['addDate'] +
          '</text:p>' +
          '</table:table-cell>' +
          '<table:table-cell office:value-type="float" office:value="' +
          str(statList['data']['esc']['regression']['total']) + '" calcext:value-type="float"/>' +
          '<table:table-cell table:formula="of:=[.D5]-[.B5]" office:value-type="float"/>' +
          '<table:table-cell office:value-type="float" office:value="' +
          str(statList['data']['esc']['regression']['total']) + '" calcext:value-type="float"/>' +
          '<table:table-cell table:style-name="isodate" table:formula="of:=[.A5]" office:value-type="date" />' +
          '\n', file=fp)
    for i in myOrder:
        if i in statList['data']['esc']['component']['all']:
	        print('<table:table-cell office:value-type="float" office:value="' +
                  str(statList['data']['esc']['component']['all'][i]) + '" calcext:value-type="float"/>' +
                  '\n', file = fp)
        else:
            print('<table:table-cell/>',
                  '\n', file = fp)
    print('</table:table-row>' +
          '</table:table>' +
          '</office:spreadsheet>' +
          '</office:body>' +
          '</office:document>' +
          '\n', file=fp)
    fp.close()
    fp = open('/tmp/esc_flatODF_body', 'w', encoding='utf-8')
    print('File to add to series', file=fp)
    fp.close

    data = 'ESC flatODF, based on stats.json from '+statList['addDate']
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

    fp = open('/tmp/esc_qa_report.txt', 'w', encoding='utf-8')
    print('ESC QA report, generated {} based on stats.json from {}'.format(
          datetime.datetime.now().strftime("%Y-%m-%d"), statList['addDate']), file=fp)

    print("copy/paste to esc pad:\n"
          "* qa update (xisco)\n", file=fp)

    print("    + UNCONFIRMED: {} ( )\n"
        "        + enhancements: {}  ( )\n"
        "        + needsUXEval: {} ( )\n"
        "        + haveBackTrace: {} ( )\n"
        "        + needsDevAdvice: {} ( )\n"
        "        + documentation:  {} ( )\n".format(
                    statList['data']['qa']['unconfirmed']['count'],
                    statList['data']['qa']['unconfirmed']['enhancement'],
                    statList['data']['qa']['unconfirmed']['needsUXEval'],
                    statList['data']['qa']['unconfirmed']['haveBacktrace'],
                    statList['data']['qa']['unconfirmed']['needsDevAdvice'],
                    statList['data']['qa']['unconfirmed']['documentation'],), file=fp)

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
