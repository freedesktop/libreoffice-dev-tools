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
        'bugs':
        {
            'all':
                {
                    'status': {s:0 for s in statutes_list},
                },
            'created':
                {
                    'id': [],
                    'author': [],
                    'enhancement_count': 0,
                    'no_enhancement_count': 0,
                    'split_week': {},
                    'split_month': {},
                    'component': {},
                    'system': {p:0 for p in system_list},
                    'platform': {},
                    'status': {s:0 for s in statutes_list},
                    'resolution': {},
                    'unconfirmed': []
                },
            'closed':
                {
                    'status': {s:0 for s in statutes_list},
                    'split_week': {}
                },
            'confirmed':
                {
                    'id': [],
                    'author': [],
                    'status': {s:0 for s in statutes_list},
                    'difftime': []
                },
            'fixed':
                {
                    'id': [],
                    'author': [],
                    'difftime': []
                },
        },
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
        'people': {},
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

    statList['addDate'] = datetime.date.today().strftime('%Y-%m-%d')

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

            statList['bugs']['all']['status'][rowStatus] += 1

            rowKeywords = row['keywords']

            creatorMail = row['creator']

            #get information about created bugs in reportPeriod
            if creationDate >= cfg['reportPeriod']:
                if row['severity'] == 'enhancement':
                    statList['bugs']['created']['enhancement_count'] += 1
                else:
                    statList['bugs']['created']['no_enhancement_count'] += 1

                component = row['component']
                if component not in statList['bugs']['created']['component']:
                    statList['bugs']['created']['component'][component] = 0
                statList['bugs']['created']['component'][component] += 1

                statList['bugs']['created']['status'][rowStatus] += 1

                if isClosed(row['status']):
                    if rowResolution not in statList['bugs']['created']['resolution']:
                        statList['bugs']['created']['resolution'][rowResolution] = 0
                    statList['bugs']['created']['resolution'][rowResolution] += 1

                platform = row['platform']
                if platform not in statList['bugs']['created']['platform']:
                    statList['bugs']['created']['platform'][platform] = 0
                statList['bugs']['created']['platform'][platform] += 1

                system = row['op_sys']
                if system not in statList['bugs']['created']['system']:
                    statList['bugs']['created']['system'][system] = 0
                statList['bugs']['created']['system'][system] += 1

                statList['bugs']['created']['id'].append(rowId)
                statList['bugs']['created']['author'].append(creatorMail)

                if rowStatus == 'UNCONFIRMED':
                    statList['bugs']['created']['unconfirmed'].append(rowId)

                week = str(creationDate.year) + '-' + str(creationDate.strftime("%V"))
                if week not in statList['bugs']['created']['split_week']:
                    statList['bugs']['created']['split_week'][week] = 0
                statList['bugs']['created']['split_week'][week] += 1

                month = str(creationDate.year) + '-' + str(creationDate.strftime("%m"))
                if month not in statList['bugs']['created']['split_month']:
                    statList['bugs']['created']['split_month'][month] = 0
                statList['bugs']['created']['split_month'][month] += 1


            whiteboard_list = row['whiteboard'].split(' ')
            bugTargets = []
            for whiteboard in whiteboard_list:
                if whiteboard.startswith("target:"):
                    bugVersion = whiteboard.split(':')[1][:5]
                    if bugVersion in targets_list:
                        bugTargets.append(bugVersion)
                        statList['targets'][bugVersion]['count'] += 1

            for period in periods_list:
                if creationDate >= cfg[period]:
                    statList['period'][period]['count'] += 1

            util_check_bugzilla_mail(statList, creatorMail, row['creator_detail']['real_name'], creationDate, rowId)

            if isOpen(rowStatus) and len(row['cc']) >= 10:
                statList['MostCCBugs'][rowId] = util_create_bug(
                        row['summary'], row['component'], row['version'], rowKeywords, creationDate, len(row['cc']))

            isFixed = False
            bResolved = False
            isConfirmed = False

            for action in row['history']:
                actionMail = action['who']
                actionDate = datetime.datetime.strptime(action['when'], "%Y-%m-%dT%H:%M:%SZ")
                util_check_bugzilla_mail(statList, actionMail, '', actionDate, rowId)

                # Use this variable in case the status is set before the resolution
                newStatus = None
                for change in action['changes']:
                    if change['field_name'] == 'is_confirmed':
                        if actionDate >= cfg['reportPeriod']:
                            if change['added'] == "1":
                                statList['bugs']['confirmed']['id'].append(rowId)
                                statList['bugs']['confirmed']['author'].append(actionMail)
                                statList['bugs']['confirmed']['status'][rowStatus] += 1
                                isConfirmed = True
                                statList['bugs']['confirmed']['difftime'].append((actionDate - creationDate).days)
                            elif isConfirmed:
                                statList['bugs']['confirmed']['id'].pop()
                                statList['bugs']['confirmed']['author'].pop()
                                statList['bugs']['confirmed']['status'][rowStatus] -= 1
                                isConfirmed = False
                                statList['bugs']['confirmed']['difftime'].pop()

                    if change['field_name'] == 'status':
                        addedStatus = change['added']
                        removedStatus = change['removed']

                        if actionDate >= cfg['reportPeriod'] and not bResolved and isClosed(addedStatus) and isClosed(row['status']):
                            bResolved = True
                            week = str(actionDate.year) + '-' + str(actionDate.strftime("%V"))
                            if week not in statList['bugs']['closed']['split_week']:
                                statList['bugs']['closed']['split_week'][week] = 0
                            statList['bugs']['closed']['split_week'][week] += 1

                            statList['bugs']['closed']['status'][rowStatus] += 1

                        if  addedStatus == 'RESOLVED' or addedStatus == 'VERIFIED':
                            if(rowResolution):
                                addedStatus = addedStatus + "_" + rowResolution
                            else:
                                newStatus = addedStatus

                        if actionDate >= cfg['reportPeriod'] and addedStatus == 'RESOLVED_FIXED' and \
                                removedStatus != 'REOPENED' and row['resolution'] == 'FIXED':
                            if isFixed:
                                statList['bugs']['fixed']['id'].pop()
                                statList['bugs']['fixed']['author'].pop()
                                statList['bugs']['fixed']['difftime'].pop()

                            statList['bugs']['fixed']['id'].append(rowId)
                            statList['bugs']['fixed']['author'].append(actionMail)
                            statList['bugs']['fixed']['difftime'].append((actionDate - creationDate).days)
                            isFixed = True

                    elif change['field_name'] == 'resolution':
                        if newStatus:
                            addedStatus = newStatus + "_" + change['added']

                            newStatus = None

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

            for person in row['cc_detail']:
                email = person['email']
                if commentMail == email or actionMail == email:
                    util_check_bugzilla_mail(statList, email, person['real_name'])

    for k, v in statList['people'].items():
        if not statList['people'][k]['name']:
            statList['people'][k]['name'] = statList['people'][k]['email'].split('@')[0]

        statList['people'][k]['oldest'] = statList['people'][k]['oldest'].strftime("%Y-%m-%d")
        statList['people'][k]['newest'] = statList['people'][k]['newest'].strftime("%Y-%m-%d")


    statList['stat']['newest'] = statNewDate.strftime("%Y-%m-%d")
    statList['stat']['oldest'] = statOldDate.strftime("%Y-%m-%d")
    print(" from " + statList['stat']['oldest'] + " to " + statList['stat']['newest'])

def util_create_short_url(fp, lBugs, text='Link'):
    url = "https://bugs.documentfoundation.org/buglist.cgi?bug_id="
    for bug in lBugs:
        url += str(bug) + "%2C"

    url = url[:-3]
    shortener = Shortener('Tinyurl', timeout=9000)
    print('\t\t+ ' + text + ': ' + shortener.short(url), file=fp)

def util_print_QA_line_blog(fp, statList, dValue, total_count):

    if len(dValue['id']) > 1:
        auxString = 'bugs.'
    else:
        auxString = "bug."

    print(('  * {} ' + auxString).format(len(dValue['id'])), file=fp)

    #Count the number of reps
    my_dict = {i: dValue['author'].count(i) for i in dValue['author']}

    d_view = [(v, k) for k, v in my_dict.items()]
    d_view.sort(reverse=True)

    print('  * Total users: {}'.format(len(d_view)), file=fp)

    usersString = '  * Done by: \n'
    count = 0
    for i1,i2 in d_view:
        try:
            count += 1
            if count <= total_count:
                usersString += '      ' +  statList['people'][i2]['name'] + ' ( ' + str(i1) + ' ) \n'
            else:
                break
        except:
            continue

    print(usersString[:-2], file=fp)

    if 'status' in dValue:
        print('  * Status: ', file=fp)
        for k,v in dValue['status'].items():
            print('      ' + str(k) + ' : ' + str(v), file=fp)

    print(file=fp)

    if 'difftime' in dValue:
        sortList = sorted(dValue['difftime'])
        rangeList = sortList[-1] - sortList[0]
        subLists = {}
        for i in sortList:
            timePeriod = ''
            if i < 1:
                timePeriod = '0001day'
            elif i < 3:
                timePeriod = '0003days'
            elif i < 7:
                timePeriod = '0007days'
            elif i < 30:
                timePeriod = '0030days'
            elif i < 90:
                timePeriod = '0090days'
            elif i < 180:
                timePeriod = '0180days'
            elif i < 365:
                timePeriod = '0365days'
            elif i < 1095:
                timePeriod = '1095days'
            else:
                timePeriod = 'older'
            if timePeriod not in subLists:
                subLists[timePeriod] = []
            subLists[timePeriod].append(i)

        print('  * Times: ', file=fp)
        for k,v in sorted(subLists.items()):
            print('      ' + str(k) + ' : ' + str(len(v)), file=fp)

def util_print_QA_line_created(fp, dValue ):
    others = 0
    s = [(k, dValue[k]) for k in sorted(dValue, key=dValue.get, reverse=True)]
    total = 0
    for k, v in s:
        print('      {}: {}'.format(k, v), file=fp)

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

def users_Report(statList):
    print('Users report from {} to {}'.format(cfg['newUserPeriod'].strftime("%Y-%m-%d"), statList['stat']['newest']))
    #fp = open('/tmp/users_report.txt', 'w', encoding='utf-8')

    print('{} new users in the last {} days'.format(len(statList['newUsersPeriod']), cfg['newUserPeriod']))

    for v,k in statList['newUsersPeriod'].items():
        print(v)


def Blog_Report(statList) :
    fp = open('/tmp/blog_report.txt', 'w', encoding='utf-8')

    print('* Report from {} to {}'.format(cfg['reportPeriod'].strftime("%Y-%m-%d"), statList['stat']['newest']), file=fp )

    print('* Total reports created: {}'.format(len(statList['bugs']['created']['id'])), file=fp)

    print('* Total enhancements created: {}'.format(statList['bugs']['created']['enhancement_count']), file=fp)

    print('* Total bugs created: {}'.format(statList['bugs']['created']['no_enhancement_count']), file=fp)
    print(file=fp)

    print('* Bugs reported.', file=fp)
    util_print_QA_line_blog(fp, statList, statList['bugs']['created'], 15)

    print(file=fp)
    print('* Bugs confirmed.', file=fp)
    util_print_QA_line_blog(fp, statList, statList['bugs']['confirmed'], 20)

    print(file=fp)
    print('* Bugs fixed.', file=fp)
    util_print_QA_line_blog(fp, statList, statList['bugs']['fixed'], 20)

    print(file=fp)
    for key, value in sorted(statList['weeklyReport']['keyword_added'].items()):
        if value and key in ['easyHack', 'bisected', 'haveBacktrace', 'regression']:
            print('* ' + key + '.', file=fp)
            util_print_QA_line_blog(fp, statList, value, 15)

    print(file=fp)
    for key, value in sorted(statList['weeklyReport']['status_changed'].items()):
        if value and key in ['RESOLVED_DUPLICATE', 'VERIFIED_FIXED']:
            print('* ' + key.replace("_", " ") + '.', file=fp)
            util_print_QA_line_blog(fp, statList, value, 20)

    print(file=fp)
    print('* Bugs created by week', file=fp)

    for key, value in sorted(statList['bugs']['created']['split_week'].items()):
        print('{}: {}'.format(key, value), file=fp)

    print(file=fp)
    print('* Bugs created by month', file=fp)

    for key, value in sorted(statList['bugs']['created']['split_month'].items()):
        print('{}: {}'.format(key, value), file=fp)

    print(file=fp)
    print('* Components of created bugs', file=fp)
    util_print_QA_line_created(fp, statList['bugs']['created']['component'])

    print(file=fp)
    print('* Systems of created bugs', file=fp)
    util_print_QA_line_created(fp, statList['bugs']['created']['system'])

    print(file=fp)
    print('* Platforms of created bugs', file=fp)
    util_print_QA_line_created(fp, statList['bugs']['created']['platform'])

    print(file=fp)
    print('* Statuses of created bugs', file=fp)
    util_print_QA_line_created(fp, statList['bugs']['created']['status'])

    print(file=fp)
    print('* Resolution of created bugs', file=fp)
    util_print_QA_line_created(fp, statList['bugs']['created']['resolution'])
    print(file=fp)

    print('* Bugs moved to resolved by week', file=fp)

    for key, value in sorted(statList['bugs']['closed']['split_week'].items()):
        print('{}: {}'.format(key, value), file=fp)

    print(file=fp)
    print('* Statuses of bugs moved to resolved', file=fp)
    util_print_QA_line_created(fp, statList['bugs']['closed']['status'])

    fp.close()

def runCfg():
    cfg = get_config()
    cfg['todayDate'] = datetime.datetime.now().replace(hour=0, minute=0,second=0)
    cfg['reportPeriod'] = util_convert_days_to_datetime(cfg, reportPeriodDays)
    cfg['untouchedPeriod'] = util_convert_days_to_datetime(cfg, untouchedPeriodDays)

    for period in periods_list:
        cfg[period] = util_convert_days_to_datetime(cfg, period)

    return cfg

if __name__ == '__main__':
    print("Reading and writing data to " + dataDir)

    cfg = runCfg()

    bugzillaData = get_bugzilla()

    statList = util_create_statList()

    analyze_bugzilla(statList, bugzillaData, cfg)

    if len(sys.argv) > 1:
        if sys.argv[1] == 'blog':
            Blog_Report(statList)
        elif sys.argv[1] == 'user':
            users_Report(statList)
        elif sys.argv[1] == 'massping':
            massping_Report(statList)
        elif sys.argv[1] == 'automate':
            automated_tagging(statList)
            automated_massping(statList)
        else:
            print("You must use 'blog', 'target', 'period', 'users', 'massping', 'automate' as parameter.")
            sys.exit(1)

    print('End of report')
