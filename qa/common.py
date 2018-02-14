#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import sys
import os
import datetime
import json
import requests
from pyshorteners import Shortener

#Path where bugzilla_dump.py is
dataDir = '/home/xisco/dev-tools/esc-reporting/dump/'

#Path where configQA.json and addObsolete.txt are
configDir = '/home/xisco/dev-tools/qa/'

reportPeriodDays = 7

untouchedPeriodDays = 365

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

untouchedPingComment = "** Please read this message in its entirety before responding **\n\nTo make sure we're focusing on the bugs that affect our users today, LibreOffice QA is asking bug reporters and confirmers to retest open, confirmed bugs which have not been touched for over a year.\n\nThere have been thousands of bug fixes and commits since anyone checked on this bug report. During that time, it's possible that the bug has been fixed, or the details of the problem have changed. We'd really appreciate your help in getting confirmation that the bug is still present.\n\nIf you have time, please do the following:\n\nTest to see if the bug is still present with the latest version of LibreOffice from https://www.libreoffice.org/download/\n\nIf the bug is present, please leave a comment that includes the information from Help - About LibreOffice.\n \nIf the bug is NOT present, please set the bug's Status field to RESOLVED-WORKSFORME and leave a comment that includes the information from Help - About LibreOffice.\n\nPlease DO NOT\n\nUpdate the version field\nReply via email (please reply directly on the bug tracker)\nSet the bug's Status field to RESOLVED - FIXED (this status has a particular meaning that is not \nappropriate in this case)\n\n\nIf you want to do more to help you can test to see if your issue is a REGRESSION. To do so:\n1. Download and install oldest version of LibreOffice (usually 3.3 unless your bug pertains to a feature added after 3.3) from http://downloadarchive.documentfoundation.org/libreoffice/old/\n\n2. Test your bug\n3. Leave a comment with your results.\n4a. If the bug was present with 3.3 - set version to 'inherited from OOo';\n4b. If the bug was not present in 3.3 - add 'regression' to keyword\n\n\nFeel free to come ask questions or to say hello in our QA chat: https://kiwiirc.com/nextclient/irc.freenode.net/#libreoffice-qa\n\nThank you for helping us make LibreOffice even better for everyone!\n\nWarm Regards,\nQA Team\n\nMassPing-UntouchedBug"

needInfoPingComment = "Dear Bug Submitter,\n\nThis bug has been in NEEDINFO status with no change for at least"

needInfoFollowUpPingComment = "Dear Bug Submitter,\n\nPlease read this message in its entirety before proceeding."

moveToNeedInfoComment = "I have set the bug's status to 'NEEDINFO'"

reopened6MonthsComment = "This bug has been in RESOLVED FIXED status for more than 6 months."

def util_convert_days_to_datetime(cfg, period):
    cfg['todayDate'] = datetime.datetime.now().replace(hour=0, minute=0,second=0)
    return cfg['todayDate'] - datetime.timedelta(days= period)

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

def util_create_person_bugzilla(email, name):
    return { 'name': name,
             'email': email,
             'oldest': datetime.datetime.now(),
             'newest': datetime.datetime(2001, 1, 1),
             'bugs': set()
        }


def util_create_statList():
    return {
        'massping':
            {
                'needinfo': [],
                'untouched': [],
                '1year': [],
                '2years': [],
                '3years': []
            },
        'tags':
            {
                'addObsolete': set(),
                'removeObsolete': set()
            },
        'stat': {'oldest': datetime.datetime.now(), 'newest': datetime.datetime(2001, 1, 1)}
    }

def util_check_bugzilla_mail(statList, mail, name, date=None, bug=None):
    if mail not in statList['people']:
        statList['people'][mail] = util_create_person_bugzilla(mail, name)

    if name and not statList['people'][mail]['name']:
        statList['people'][mail]['name'] = name

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

def analyze_bugzilla(statList, bugzillaData, cfg):
    print("Analyze bugzilla\n", end="", flush=True)
    statNewDate = statList['stat']['newest']
    statOldDate = statList['stat']['oldest']

    for key, row in bugzillaData['bugs'].items():
        rowId = row['id']

        #Ignore META bugs and deletionrequest bugs.
        if not row['summary'].lower().startswith('[meta]') and row['component'] != 'deletionrequest':
            creationDate = datetime.datetime.strptime(row['creation_time'], "%Y-%m-%dT%H:%M:%SZ")
            if creationDate < statOldDate:
                statOldDate = creationDate
            if creationDate > statNewDate:
                statNewDate = creationDate

            rowStatus = row['status']
            rowResolution = row['resolution']

            if rowStatus == 'VERIFIED' or rowStatus == 'RESOLVED':
                rowStatus += "_" + rowResolution

            rowKeywords = row['keywords']

            creatorMail = row['creator']

            commentMail = None
            comments = row['comments'][1:]
            for idx, comment in enumerate(comments):
                commentMail = comment['creator']
                commentDate = datetime.datetime.strptime(comment['time'], "%Y-%m-%dT%H:%M:%SZ")

                util_check_bugzilla_mail(statList, commentMail, '', commentDate, rowId)

                #Check for duplicated comments
                if idx > 0 and comment['text'] == comments[idx-1]['text']:
                        statList['tags']['addObsolete'].add(comment["id"])

                if rowStatus != 'NEEDINFO' and \
                        "obsolete" not in [x.lower() for x in comment["tags"]] and \
                        (comment["text"].startswith(untouchedPingComment[:250]) or \
                        moveToNeedInfoComment in comment["text"] or \
                        comment["text"].startswith("A polite ping, still working on this bug") or \
                        comment["text"].startswith(needInfoPingComment) or \
                        comment["text"].startswith(needInfoFollowUpPingComment)):
                    statList['tags']['addObsolete'].add(comment["id"])

            if len(comments) > 0:
                if comments[-1]["text"].startswith(untouchedPingComment[:250]):

                    if len(comments) > 1 and comments[-2]["text"].startswith(untouchedPingComment[:250]):
                        if len(comments) > 2 and comments[-3]["text"].startswith(untouchedPingComment[:250]):
                            statList['massping']['3years'].append(rowId)
                        else:
                            statList['massping']['2years'].append(rowId)
                    else:
                        statList['massping']['1year'].append(rowId)

                    if rowStatus != 'NEEDINFO':
                        if "obsolete" not in [x.lower() for x in comments[-1]["tags"]]:
                            statList['tags']['addObsolete'].remove(comments[-1]["id"])
                        else:
                            statList['tags']['removeObsolete'].add(comments[-1]["id"])
                elif comments[-1]["text"].startswith(needInfoPingComment):
                    if rowStatus == 'NEEDINFO':
                        statList['massping']['needinfo'].append(rowId)
                    else:
                        if "obsolete" not in [x.lower() for x in comments[-1]["tags"]]:
                            statList['tags']['addObsolete'].remove(comments[-1]["id"])
                        else:
                            statList['tags']['removeObsolete'].add(comments[-1]["id"])
                elif comments[-1]["text"].startswith(needInfoFollowUpPingComment) or \
                        comments[-1]["text"].startswith("A polite ping, still working on this bug") or \
                        moveToNeedInfoComment in comments[-1]["text"]:
                    if rowStatus != 'NEEDINFO':
                        if "obsolete" not in [x.lower() for x in comments[-1]["tags"]]:
                            statList['tags']['addObsolete'].remove(comments[-1]["id"])
                        else:
                            statList['tags']['removeObsolete'].add(comments[-1]["id"])
                else:
                    if datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ") < cfg['untouchedPeriod'] and \
                            rowStatus == 'NEW' and 'needsUXEval' not in rowKeywords and 'easyHack' not in rowKeywords and \
                            row['component'] != 'Documentation' and (row['product'] == 'LibreOffice' or \
                            row['product'] == 'Impress Remote') and row['severity'] != 'enhancement':
                        statList['massping']['untouched'].append(rowId)

    statList['stat']['newest'] = statNewDate.strftime("%Y-%m-%d")
    statList['stat']['oldest'] = statOldDate.strftime("%Y-%m-%d")
    print(" from " + statList['stat']['oldest'] + " to " + statList['stat']['newest'])


def massping_Report(statList):
    fp = open('/tmp/massping_report.txt', 'w', encoding='utf-8')

    print('* Massping Report from {} to {}'.format(cfg['reportPeriod'].strftime("%Y-%m-%d"), statList['stat']['newest']), file=fp )
    for key, value in sorted(statList['massping'].items()):
        print(file=fp)
        print('* ' + key + ' - ' + str(len(value)) + ' bugs.', file=fp)
        for i in range(0, len(value), 400):
            subList = value[i:i + 400]
            util_create_short_url(fp, subList)

    fp.close()

def automated_massping(statList):

    print('== Massping ==')
    for bugId in statList['massping']['untouched']:
        bugId = str(bugId)
        command = '{"comment" : "' + untouchedPingComment.replace('\n', '\\n') + '", "is_private" : false}'

        urlGet = 'https://bugs.documentfoundation.org/rest/bug/' + bugId + '/comment?api_key=' + cfg['configQA']['api-key']
        rGet = requests.get(urlGet)
        rawData = json.loads(rGet.text)
        rGet.close()

        if rawData['bugs'][bugId]['comments'][-1]['text'][:250] != untouchedPingComment[:250]:
            urlPost = 'https://bugs.documentfoundation.org/rest/bug/' + bugId + '/comment?api_key=' + cfg['configQA']['api-key']
            rPost = requests.post(urlPost, command)
            print('Bug: ' + bugId + ' - Comment: ' + str(json.loads(rPost.text)['id']))
            rPost.close()

def automated_tagging(statList):
    #tags are sometimes not saved in bugzilla_dump.json
    #thus, save those comments automatically tagged as obsolete
    #so we don't tag them again next time

    print('== Obsolete comments ==')
    lAddObsolete = []
    filename = configDir + "addObsolete.txt"
    if os.path.exists(filename):
        f = open(filename, 'r')
        lAddObsolete = f.read().splitlines()
        f.close()

    for comment_id in list(statList['tags']['addObsolete']):
        if str(comment_id) not in lAddObsolete:
            command = '{"comment_id" : ' + str(comment_id) + ', "add" : ["obsolete"]}'
            url = 'https://bugs.documentfoundation.org/rest/bug/comment/' + \
                str(comment_id) + '/tags' + '?api_key=' + cfg['configQA']['api-key']
            r = requests.put(url, command)
            if os.path.exists(filename):
                append_write = 'a'
            else:
                append_write = 'w'
            f = open(filename,append_write)
            f.write(str(comment_id) + '\n')
            f.close()
            print(str(comment_id) + ' - ' +  r.text)
            r.close()

    for comment_id in list(statList['tags']['removeObsolete']):
        command = '{"comment_id" : ' + str(comment_id) + ', "remove" : ["obsolete"]}'
        url = 'https://bugs.documentfoundation.org/rest/bug/comment/' + \
                str(comment_id) + '/tags' + '?api_key=' + cfg['configQA']['api-key']
        r = requests.put(url, command)
        print(str(comment_id) + ' - ' +  r.text)
        r.close()

def runCfg():
    cfg = get_config()
    cfg['reportPeriod'] = util_convert_days_to_datetime(cfg, reportPeriodDays)
    cfg['untouchedPeriod'] = util_convert_days_to_datetime(cfg, untouchedPeriodDays)

    return cfg

if __name__ == '__main__':
    print("Reading and writing data to " + dataDir)

    cfg = runCfg()

    bugzillaData = get_bugzilla()

    statList = util_create_statList()

    analyze_bugzilla(statList, bugzillaData, cfg)

    if len(sys.argv) > 1:
        if sys.argv[1] == 'massping':
            massping_Report(statList)
        elif sys.argv[1] == 'automate':
            automated_tagging(statList)
            automated_massping(statList)
        else:
            print("You must use 'blog', 'target', 'period', 'users', 'massping', 'automate' as parameter.")
            sys.exit(1)

    print('End of report')
