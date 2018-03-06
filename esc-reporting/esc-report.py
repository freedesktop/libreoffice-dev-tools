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



import common
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



def util_dump_file(fileName, rawList):
    try:
      fp = open(fileName, 'w', encoding='utf-8')
      json.dump(rawList, fp, ensure_ascii=False, indent=4, sort_keys=True)
      fp.close()
    except Exception as e:
      print('Error dump file ' + fileName + ' due to ' + str(e))
      os.remove(fileName)
      exit(-1)



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
    global statList, cfg

    fp = open('/tmp/esc_day_mentoring_report.txt', 'w', encoding='utf-8')
    print('Day mentoring report, generated {} based on stats.json from {}'.format(
          datetime.datetime.now().strftime("%Y-%m-%d"), statList['addDate']), file=fp)

    util_print_line(fp, statList['reportList']['missing_license'],    'missing license statement'  )
    util_print_line(fp, statList['reportList']['needinfo'],           'easyhacks with NEEDINFO',   doBugzilla=True)
    util_print_line(fp, statList['reportList']['easyhacks_new'],      'easyhacks new',             doBugzilla=True)
    util_print_line(fp, statList['reportList']['to_be_closed'],       'easyhacks to be closed',    doBugzilla=True)
    util_print_line(fp, statList['reportList']['needsDevEval'],       'easyhacks needsDevEval',    doBugzilla=True)
    util_print_line(fp, statList['reportList']['needsUXEval'],        'easyhacks needsUXEval',     doBugzilla=True)
    util_print_line(fp, statList['reportList']['too_many_comments'],  'easyhacks reduce comments', doBugzilla=True)
    util_print_line(fp, statList['reportList']['pending_license'],    'pending license statement'  )
    fp.close()
    return {'title': 'esc_mentoring, Daily work', 'mail': 'mentoring@documentfoundation.org', 'file': '/tmp/esc_day_mentoring_report.txt'}



def report_mentoring():
    global statList, cfg

    fp = open('/tmp/esc_mentoring_report.txt', 'w', encoding='utf-8')
    #temp print("    + openhub statistics ({}), {} people did {} commits in 12 month in {} lines of code\n"
    #temp       "    + gerrit/git statistics:".format(
    #temp       statList['stat']['openhub_last_analyse'],
    #temp       util_build_escNumber('openhub', 'year_contributors'),
    #temp       util_build_escNumber('openhub', 'year_commits'),
    #temp       util_build_escNumber('openhub', 'lines_of_code')), file=fp)
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
    print(statList['reportList']['top10commit'])
    for i in range(0, len(statList['reportList']['top10commit'])):
      if i == 5:
          break
      print('          {} made {} patches in 1 month, and {} patches in 1 year'.format(
          statList['reportList']['top10commit'][i]['name'],
          statList['reportList']['top10commit'][i]['month'],
          statList['reportList']['top10commit'][i]['year']), file=fp)
    print("    + top 5 reviewers:", file=fp)
    for i in range(0, len(statList['reportList']['top10review'])):
      if i == 5:
          break
      print('          {} made {} review comments in 1 month, and {} in 1 year'.format(
          statList['reportList']['top10review'][i]['name'],
          statList['reportList']['top10review'][i]['month'],
          statList['reportList']['top10review'][i]['year']), file=fp)

    print("    + big CONGRATULATIONS to contributors who have at least 1 merged patch, since last report:", file=fp)
    for row in statList['reportList']['award_1st_email']:
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
    for name, count in [(k, x[k]) for k in sorted(x, key=x.get, reverse=True)][0:10]:
      txt += '       {:<23} {}\n'.format(name, count)
    txt += '\n    + top 10 bugs reporters:\n'
    x = statList['escList']['QAstat']['top15_reporters']
    for name, count in [(k, x[k]) for k in sorted(x, key=x.get, reverse=True)][0:10]:
      txt += '       {:<23} {}\n'.format(name, count)
    txt += '\n    + top 10 bugs fixers:\n'
    x = statList['escList']['QAstat']['top15_fixers']
    for name, count in [(k, x[k]) for k in sorted(x, key=x.get, reverse=True)][0:10]:
      txt += '       {:<23} {}\n'.format(name, count)
    txt += '\n    + top 10 bugs confirmers:\n'
    x = statList['escList']['QAstat']['top15_confirmers']
    for name, count in [(k, x[k]) for k in sorted(x, key=x.get, reverse=True)][0:10]:
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
      lastCount = statList['diff']['esc']['component']['high'][name]
      if count != 0 or lastCount != 0:
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

    txt = '     open:\n'
    for id, title in statList['escList']['MostPressingBugs']['open']['list'].items():
        txt += '        + {}\n'.format(title)
        txt += '            + https://bugs.documentfoundation.org/show_bug.cgi?id={}\n'.format(id)
    txt += '     closed:\n'
    for id, title in statList['escList']['MostPressingBugs']['closed']['list'].items():
        txt += '        + {}\n'.format(title)
        txt += '            + https://bugs.documentfoundation.org/show_bug.cgi?id={}\n'.format(id)
    escPrototype = escPrototype.replace('$<ESC_MOST_PRESSING_BUGS>', txt)

    txt = '    + {}({:+d}) import failure, {}({:+d}) export failures'.format(
          statList['data']['esc']['crashtest']['import'], statList['diff']['esc']['crashtest']['import'],
          statList['data']['esc']['crashtest']['export'], statList['diff']['esc']['crashtest']['export'])
    escPrototype = escPrototype.replace('$<ESC_CRASHTEST_UPDATE>', txt)

    txt = ''
    for id in sorted(statList['data']['esc']['crashreport']):
        txt += '    + {}    {}({:+d})\n'.format(id,
            statList['data']['esc']['crashreport'][id],
            statList['diff']['esc']['crashreport'][id])
    escPrototype = escPrototype.replace('$<ESC_CRASHREPORT_UPDATE>', txt)

    fp = open('/tmp/esc_prototype_report.txt', 'w', encoding='utf-8')
    print('ESC prototype report, generated {} based on stats.json from {}\n\n\n'.format(
          datetime.datetime.now().strftime("%Y-%m-%d"), statList['addDate']), file=fp)
    print(escPrototype, file=fp)
    fp.close()

    data = 'ESC prototype, based on stats.json from '+statList['addDate']
    return {'title': data, 'mail': 'mentoring@documentfoundation.org', 'file': '/tmp/esc_prototype_report.txt'}



def gen_rowHighPriority():
    global statList

    txt1 = ''
    txt2 = ''
    vSumOpen = 0
    vSumTotal = 0
    for i in ['old', '4.0', '4.1', '4.2', '4.3', '4.4', '5.0', '5.1', '5.2', '5.3', '5.4', '5.5']:
        if i in statList['data']['esc']['MAB']:
            vOpen = statList['data']['esc']['MAB'][i]['open']
            vTotal = statList['data']['esc']['MAB'][i]['total']
        else :
            vOpen = 0
            vTotal = 0
        vClosed = vTotal - vOpen
        vSumOpen += vOpen
        vSumTotal += vTotal

        txt1 += '<table:table-cell office:value-type="float" office:value="{xOpen}" calcext:value-type="float">' \
                '<text:p>{xOpen}</text:p></table:table-cell>' \
                '<table:table-cell office:value-type="float" office:value="{xClosed}" calcext:value-type="float">' \
                '<text:p>{xClosed}</text:p></table:table-cell>\n'.format(xOpen=vOpen, xClosed=vClosed)
        txt2 += '<table:table-cell office:value-type="float" office:value="{xTotal}" calcext:value-type="float">' \
                '<text:p>{xTotal}</text:p></table:table-cell>\n'.format(xTotal=vTotal)

    vSumTotal -= vSumOpen
    text = '<table:table-row table:style-name="ro2">' \
           '<table:table-cell table:style-name="isodate" office:value-type="date" ' \
                'office:date-value="{xDate}" calcext:value-type="date">' \
                '<text:p>{xDate}</text:p></table:table-cell>\n'.format(xDate=statList['addDate']) + txt1 + txt2
    text += '<table:table-cell office:value-type="float" office:value="{xSumOpen}" calcext:value-type="float">' \
                '<text:p>{xSumOpen}</text:p></table:table-cell>\n' \
            '<table:table-cell office:value-type="float" office:value="{xSumClosed}" calcext:value-type="float">' \
            '<text:p>{xSumClosed}</text:p></table:table-cell>\n' \
            '</table:table-row>\n'.format(xSumOpen=vSumOpen, xSumClosed=vSumTotal)
    return text



def gen_rowRegression(useHigh=False):
    global statList

    textDate = '<table:table-cell office:value-type="date" office:date-value="{xD}" calcext:value-type="date">\n' \
               '<text:p>{xD}</text:p></table:table-cell>\n'.format(xD=statList['addDate'])

    text = '<table:table-row table:style-name="ro2">\n' + textDate

    if not useHigh:
        vType = 'all'
        vOpen = statList['data']['esc']['regression']['open']
        vTotal = statList['data']['esc']['regression']['total']
        vClosed = vTotal - vOpen
        vDiffO = vOpen - statList['data']['esc']['regression']['open-1']
        vDiffT = vTotal - statList['data']['esc']['regression']['total-1']
        vDelta = vDiffT - vDiffO
        text += '<table:table-cell office:value-type="float" office:value="{xO}" calcext:value-type="float">\n' \
                '<text:p>{xO}</text:p></table:table-cell>\n' \
                '<table:table-cell office:value-type="float" office:value="{xC}" calcext:value-type="float">\n' \
                '<text:p>{xC}</text:p></table:table-cell>\n' \
                '<table:table-cell office:value-type="float" office:value="{xT}" calcext:value-type="float">\n' \
                '<text:p>{xT}</text:p></table:table-cell>\n'.format(xO=vOpen,xC=vClosed,xT=vTotal) + textDate
        endText = textDate + \
                  '<table:table-cell office:value-type="float" office:value="{xDO}" calcext:value-type="float">\n' \
                  '<text:p>{xDO}</text:p></table:table-cell>\n' \
                  '<table:table-cell office:value-type="float" office:value="{xDT}" calcext:value-type="float">\n' \
                  '<text:p>{xDT}</text:p></table:table-cell>\n' \
                  '<table:table-cell office:value-type="float" office:value="{xDD}" calcext:value-type="float">\n' \
                  '<text:p>{xDD}</text:p></table:table-cell>\n' \
                  '<table:table-cell table:number-columns-repeated="24"/>\n'.format(xDO=vDiffO, xDT=vDiffT, xDD=vDelta)
    else:
        vType = 'high'
        endText = ''

    buildText = ''
    for id in ['Calc', 'Impress', 'Base', 'Draw', 'LibreOffice', 'Borders', 'Crashes',
               'BASIC', 'Writer/RTF', 'Writer', '', 'Chart', 'Extensions', 'Formula Editor',
               'Impress Remote', 'Installation', 'Linguistic', 'Printing and PDF export',
               'UI', 'filters and storage', 'framework', 'graphics stack', 'sdk']:
        if id is '' or id not in statList['data']['esc']['component'][vType]:
          vOpen = 0
        else:
          vOpen = statList['data']['esc']['component'][vType][id]

        if vOpen == 0 and useHigh:
            buildText += '<table:table-cell/>\n'
        else:
            buildText += '<table:table-cell office:value-type="float" office:value="{xO}" calcext:value-type="float">\n' \
                         '<text:p>{xO}</text:p></table:table-cell>\n'.format(xO=vOpen)

    return text + buildText + endText + '</table:table-row>\n'


def report_bug_metrics():
    global statList, cfg

    if cfg['nowDate'].strftime('%w') != '2':
      # only generate un tuesdays
      return

    fileName = 'bug-metrics/bug-metrics.ods'
    filePath = cfg['homedir'] + fileName
    fileContent = '/tmp/bugs/content.xml'

    os.system('rm -rf /tmp/bugs')
    os.system('unzip -d /tmp/bugs ' + filePath)
    fp = open(fileContent, encoding='utf-8')
    text = fp.read()
    fp.close()

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
        text = text[:endIndex] + gen_rowHighPriority() + text[endIndex:]
      elif text[startIndex:].startswith('"Regressions"'):
        text = text[:endIndex] + gen_rowRegression() + text[endIndex:]
      elif text[startIndex:].startswith('"HighPrioRegressions"'):
        text = text[:endIndex] + gen_rowRegression(useHigh=True) + text[endIndex:]
      else:
        raise Exception("unknown sheet in bug-metrics: " + text[startIndex:startIndex+20])

    fp = open(fileContent, 'w', encoding='utf-8')
    print(text, file=fp)
    fp.close()
    os.system('cd /tmp/bugs; zip ' + filePath + ' *')
    os.system('cd ' + cfg['homedir'] + 'bug-metrics; git add *; git commit -m \'new version ' + statList['addDate'] + '\'')

    fileBody='/tmp/esc_odf.txt'
    fp = open(fileBody, 'w', encoding='utf-8')
    print('the weekly bug-metrics.odf\nhave fun', file=fp)
    fp.close()

    data = 'ESC bug_metric.fods, based on stats.json from '+statList['addDate']
    return {'title': data, 'mail': 'mentoring@documentfoundation.org',
            'attach': {'name': fileName, 'path': filePath, 'extension': 'ods'}, 'file' : fileBody}



def report_ui():
    global statList, cfg
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
    return None



def report_qa():
    global statList, cfg
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
        "        + documentation:  {} ({:+d})\n" \
        "        + android:  {} ({:+d})\n".format(
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
                    statList['diff']['qa']['unconfirmed']['documentation'],
                    statList['data']['qa']['unconfirmed']['android'],
                    statList['diff']['qa']['unconfirmed']['android'])
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
   global statList, cfg

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

    cfg['nowDate'] = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    cfg['cutDate'] = cfg['nowDate'] - datetime.timedelta(days=365)
    cfg['1weekDate'] = cfg['nowDate'] - datetime.timedelta(days=7)
    cfg['1monthDate'] = cfg['nowDate'] - datetime.timedelta(days=30)
    cfg['3monthDate'] = cfg['nowDate'] - datetime.timedelta(days=90)
    cfg['1yearDate'] = cfg['nowDate'] - datetime.timedelta(days=365)
    return cfg



def runReport():
    global cfg, statList

    statList = util_load_data_file(cfg['homedir'] + 'stats.json')

    xMail = []
    try:
      x = report_bug_metrics()
      if not x is None:
        xMail.append(x)
    except Exception as e:
      common.util_errorMail(cfg, 'esc-report', 'ERROR: report_bug_metrics failed with ' + str(e))
      pass
    try:
      x = report_day_mentoring()
      if not x is None:
        xMail.append(x)
    except Exception as e:
      common.util_errorMail(cfg, 'esc-report', 'ERROR: report_day_mentoring failed with ' + str(e))
      pass
    try:
      x = report_mentoring()
      if not x is None:
        xMail.append(x)
    except Exception as e:
      common.util_errorMail(cfg, 'esc-report', 'ERROR: report_mentoring failed with ' + str(e))
      pass
    try:
      x = report_ui()
      if not x is None:
        xMail.append(x)
    except Exception as e:
      common.util_errorMail(cfg, 'esc-report', 'ERROR: report_ui failed with ' + str(e))
      pass
    try:
      x = report_qa()
      if not x is None:
        xMail.append(x)
    except Exception as e:
      common.util_errorMail(cfg, 'esc-report', 'ERROR: report_qa failed with ' + str(e))
      pass
    try:
      x = report_myfunc()
      if not x is None:
        xMail.append(x)
    except Exception as e:
      common.util_errorMail(cfg, 'esc-report', 'ERROR: report_myfunc failed with ' + str(e))
      pass
    try:
      x = report_esc_prototype()
      if not x is None:
        xMail.append(x)
    except Exception as e:
      common.util_errorMail(cfg, 'esc-report', 'ERROR: report_esc_prototype failed with ' + str(e))
      pass

    for i in xMail:
      with open(i['file'], 'r') as content_file:
        text = content_file.read()

      if 'attach' not in i:
        i['attach'] = None

      error = common.sendMail(cfg, i['mail'], i['title'], text, i['attach'])
      if error:
        common.util_errorMail(cfg, 'esc-report', 'ERROR: mailing failed with ' + str(e))


if __name__ == '__main__':
    runCfg(sys.platform)
    runReport()
