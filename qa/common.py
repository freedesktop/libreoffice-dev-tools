#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import os
import datetime
import json
import argparse
from pyshorteners import Shortener

#Path where bugzilla_dump.py is
dataDir = '/home/xisco/dev-tools/esc-reporting/dump/'

#Path where configQA.json and addObsolete.txt are
configDir = '/home/xisco/dev-tools/qa/'

priorities_list = ['highest','high','medium','low','lowest']

severities_list = ['blocker', 'critical', 'major', 'normal', 'minor', 'trivial','enhancement']

product_list = ['cppunit', 'LibreOffice', 'LibreOffice Online', 'Document Liberation Project', 'Impress Remote',
        'libexttextcat', 'QA Tools']

statutes_list = ['UNCONFIRMED', 'NEW', 'CLOSED', 'NEEDINFO', 'REOPENED', 'ASSIGNED', 'RESOLVED_FIXED',
        'RESOLVED_DUPLICATE', 'RESOLVED_WORKSFORME', 'RESOLVED_NOTABUG', 'RESOLVED_NOTOURBUG', 'RESOLVED_WONTFIX',
        'RESOLVED_INVALID', 'RESOLVED_MOVED', 'RESOLVED_INSUFFICIENTDATA', 'VERIFIED_FIXED', 'VERIFIED_DUPLICATE',
        'VERIFIED_WORKSFORME', 'VERIFIED_NOTABUG', 'VERIFIED_NOTOURBUG', 'VERIFIED_WONTFIX', 'VERIFIED_INVALID',
        'VERIFIED_MOVED', 'VERIFIED_INSUFFICIENTDATA']

keywords_list = ['accessibility', 'bibisected', 'bibisectNotNeeded', 'bibisectRequest', 'bisected', 'corruptProfile',
        'dataLoss', 'easyHack', 'filter:doc', 'filter:docx', 'filter:emf', 'filter:fodp', 'filter:fodt', 'filter:html',
        'filter:odf', 'filter:odp', 'filter:ods', 'filter:odt', 'filter:ooxml', 'filter:pdf', 'filter:ppt',
        'filter:pptx', 'filter:rtf', 'filter:svgInsert', 'filter:svgOpen', 'filter:visio', 'filter:xls', 'filter:xlsx',
        'haveBacktrace', 'implementationError', 'needsConfirmationAdvice', 'needsDevAdvice', 'needsDevEval',
        'needsUXEval', 'needUITest', 'notBibisectable', 'patch', 'perf', 'possibleRegression', 'preBibisect',
        'regression', 'security', 'text:cjk', 'text:ctl', 'text:rtl', 'wantBacktrace']

system_list = ['All', 'Linux (All)', 'Android', 'Windows (All)', 'Mac OS X (All)', 'iOS', 'FreeBSD', 'NetBSD', 'OpenBSD',
        'BSD (Others)', 'Solaris', 'Cygwin', 'AIX', 'HP-UX', 'IRIX', 'Interix', 'other']

urlShowBug = "https://bugs.documentfoundation.org/show_bug.cgi?id="

def util_convert_days_to_datetime(period):
    todayDate = datetime.datetime.now().replace(hour=0, minute=0,second=0)
    return todayDate - datetime.timedelta(days= period)

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

def util_dump_config(rawList):
    try:
        fileName = configDir + 'configQA.json'
        fp = open(fileName, 'w', encoding='utf-8')
        json.dump(rawList, fp, ensure_ascii=False, indent=4, sort_keys=True)
        fp.close()
    except Exception as e:
        print('Error dump file ' + fileName + ' due to ' + str(e))
        os.remove(fileName)
        exit(-1)

def util_create_person_bugzilla(email, name):
    return { 'name': name,
             'email': email,
             'oldest': datetime.datetime.now(),
             'newest': datetime.datetime(2001, 1, 1),
             'newestName': datetime.datetime(2001, 1, 1),
             'bugs': set()
        }

def util_check_bugzilla_mail(statList, mail, name, date=None, bug=None):
    if mail not in statList['people']:
        statList['people'][mail] = util_create_person_bugzilla(mail, name)

    if name:
        if not statList['people'][mail]['name']:
            statList['people'][mail]['name'] = name
            if date:
                statList['people'][mail]['newestName'] = date
        else:
            if name != statList['people'][mail]['name'] and date and \
                    date > statList['people'][mail]['newestName']:
                statList['people'][mail]['name'] = name
                statList['people'][mail]['newestName'] = date

    if date:
        if date < statList['people'][mail]['oldest']:
            statList['people'][mail]['oldest'] = date
        if date > statList['people'][mail]['newest']:
            statList['people'][mail]['newest'] = date

    if bug:
       statList['people'][mail]['bugs'].add(bug)

def util_create_short_url(fp, lBugs, text='Link'):
    url = "https://bugs.documentfoundation.org/buglist.cgi?bug_id="
    for bug in lBugs:
        url += str(bug) + "%2C"

    url = url[:-3]
    shortener = Shortener('Tinyurl', timeout=9000)
    print('\t\t+ ' + text + ': ' + shortener.short(url), file=fp)

def mkdate(datestr):
      try:
        return datetime.datetime.strptime(datestr, '%Y-%m-%d')
      except ValueError:
        raise argparse.ArgumentTypeError(datestr + ' is not a proper date string')

def util_parse_date_args():
    parser=argparse.ArgumentParser()
    parser.add_argument('Date',type=mkdate, nargs=2, help="Introduce the starting date as first" + \
            " argument and the ending date as second argument. FORMAT: YYYY-MM-DD")
    args=parser.parse_args()

    if args.Date[0] >= args.Date[1]:
        print('Argument 1 must be older than argument 2... Closing!!')
        exit()

    return parser.parse_args()

def util_check_range_time(xDate, cfg):
    if xDate >= cfg.Date[0] and xDate < cfg.Date[1]:
        return True
    else:
        return False

def get_bugzilla():
    fileName = dataDir + 'bugzilla_dump.json'
    return util_load_file(fileName)

def get_config():
    fileName = configDir + 'configQA.json'
    return util_load_file(fileName)

def isOpen(status):
    return status == 'NEW' or status == 'ASSIGNED' or status == 'REOPENED'

def isClosed(status):
    #Use row['status'], not rowStatus
    return status == 'VERIFIED' or status == 'RESOLVED' or status == 'CLOSED'
