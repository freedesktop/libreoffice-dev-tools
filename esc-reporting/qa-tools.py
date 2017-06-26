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
from pyshorteners import Shortener
import re

homeDir = '/home/xisco/dev-tools/esc-reporting/'

reportPeriod = '7d'

newUsersPeriod = '7d'

targets_list = ['5.4.0']

periods_list = ['30d', '60d', '90d', '180d']

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

product_list = ['cppunit', 'Document Liberation Project', 'Impress Remote', 'libabw', 'libetonyek', 'libexttextcatYes',
        'libfreehand', 'libgltf', 'libmspub', 'libpagemaker', 'LibreOffice', 'LibreOffice Online', 'libvisio', 'QA Tools']

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
             'newest': datetime.datetime(2001, 1, 1)
        }

def util_create_detailed_person(email):
    return { 'email': email,
             'bugs': [],
             'created': 0,
             'comments':0,
             'status_changed': 0,
             'keyword_added': 0,
             'keyword_removed': 0,
             'whiteboard_added': 0,
             'whiteboard_removed': 0,
             'severity_changed': 0,
             'priority_changed': 0,
             'system_changed': 0
         }

def util_create_statList():
    return {
        'data': 
        {
            'bugs':
            {
             'all':
                 {
                 'count': 0,
                 'status': {s:0 for s in statutes_list},
                 'keywords': {k:0 for k in keywords_list}
                 },
             'open':
                 {
                 'count': 0,
                 'keywords': {k:0 for k in keywords_list}
                 },
             }
        },
        'detailedReport':
        {
            'created_count': 0,
            'unconfirmed_count' : 0,
            'enhancement_count': 0,
            'no_enhancement_count': 0,
            'created_week': {},
            'is_confirm_count': 0,
            'is_fixed': 0,
            'comments_count': 0,
            'bug_component': {},
            'bug_system': {},
            'bug_platform': {},
            'bug_status': {},
            'bug_resolution': {},
            'backTraceStatus': {},
            'regressionStatus': {},
            'bisectedStatus': {},
            'status_changed_to': {s:0 for s in statutes_list},
            'keyword_added': {k:0 for k in keywords_list},
            'keyword_removed': {k:0 for k in keywords_list},
            'whiteboard_added': {},
            'whiteboard_removed': {},
            'severity_changed': {s:0 for s in severities_list},
            'priority_changed':  {p:0 for p in priorities_list},
            'system_changed': {p:0 for p in system_list},
            'lists': {
                'author': [[], []],
                'confirm': [[], []],
                'fixed': [[], []],
                'unconfirmed': [],
                'status_changed_to': {s: [[], []] for s in statutes_list},
                'keyword_added': {k: [[], []] for k in keywords_list},
                'keyword_removed': {k: [[], []] for k in keywords_list},
                'whiteboard_added': {},
                'whiteboard_removed': {},
                'severity_changed': {s: [[], []] for s in severities_list},
                'priority_changed': {p: [[], []] for p in priorities_list},
                'system_changed': {p: [[], []] for p in system_list}
            }
        },
        'people': {},
        'newUsersPeriod': {},
        'targets': {t:{'count':0, 'people':{}} for t in targets_list},
        'period': {p:{'count':0, 'people':{}} for p in periods_list},
        'stat': {'oldest': datetime.datetime.now(), 'newest': datetime.datetime(2001, 1, 1)}
    }

def util_check_bugzilla_mail(statList, mail, name, date=None):
    if mail not in statList['people']:
        statList['people'][mail] = util_create_person_bugzilla(mail, name)

    if name and not statList['people'][mail]['name']:
        statList['people'][mail]['name'] = name

    if date:
        if date < statList['people'][mail]['oldest']:
            statList['people'][mail]['oldest'] = date
        if date > statList['people'][mail]['newest']:
            statList['people'][mail]['newest'] = date

def get_bugzilla(cfg):
    fileName = homeDir + 'dump/bugzilla_dump.json'
    return util_load_file(fileName)

def isOpen(status):
    return status == 'NEW' or status == 'ASSIGNED' or status == 'REOPENED'

def util_increase_user_actions(statList, bug, mail, targets, action, actionTime):
    for target in targets:
        if mail not in statList['targets'][target]['people']:
            statList['targets'][target]['people'][mail] = util_create_detailed_person(mail)
        
        statList['targets'][target]['people'][mail][action] += 1
        statList['targets'][target]['people'][mail]['bugs'].append(bug)

    for period in periods_list:
        if actionTime >= cfg[period]:
            if mail not in statList['period'][period]['people']:
                statList['period'][period]['people'][mail] = util_create_detailed_person(mail)
    
            statList['period'][period]['people'][mail][action] += 1
            statList['period'][period]['people'][mail]['bugs'].append(bug)

def analyze_bugzilla(statList, bugzillaData, cfg):
    print("Analyze bugzilla\n", end="", flush=True)
    statNewDate = statList['stat']['newest']
    statOldDate = statList['stat']['oldest']

    statList['addDate'] = datetime.date.today().strftime('%Y-%m-%d')

    total = 0
    for key, row in bugzillaData['bugs'].items():
	    #Ignore META bugs and deletionrequest bugs.
        if not row['summary'].lower().startswith('[meta]') and row['component'] != 'deletionrequest':
            creationDate = datetime.datetime.strptime(row['creation_time'], "%Y-%m-%dT%H:%M:%SZ")
            if creationDate < statOldDate:
                statOldDate = creationDate
            if creationDate > statNewDate:
                statNewDate = creationDate

            statList['data']['bugs']['all']['count'] += 1

            rowStatus = row['status']
            rowResolution = row['resolution']

            if rowStatus == 'VERIFIED' or rowStatus == 'RESOLVED':
                rowStatus += "_" + rowResolution

            statList['data']['bugs']['all']['status'][rowStatus] += 1
            if isOpen(rowStatus):
                statList['data']['bugs']['open']['count'] += 1

            keywords = row['keywords']
            for keyword in keywords:
                if keyword in keywords_list:
                    statList['data']['bugs']['all']['keywords'][keyword] += 1
                    if isOpen(rowStatus):
                        statList['data']['bugs']['open']['keywords'][keyword] += 1

            creatorMail = row['creator']

            if creationDate >= cfg[reportPeriod]:
                statList['detailedReport']['created_count'] += 1

                if row['severity'] == 'enhancement':
                    statList['detailedReport']['enhancement_count'] += 1
                else:
                    statList['detailedReport']['no_enhancement_count'] += 1

                component = row['component']
                if component not in statList['detailedReport']['bug_component']:
                    statList['detailedReport']['bug_component'][component] = 0
                statList['detailedReport']['bug_component'][component] += 1

                if rowStatus not in statList['detailedReport']['bug_status']:
                    statList['detailedReport']['bug_status'][rowStatus] = 0
                statList['detailedReport']['bug_status'][rowStatus] += 1

                resolution = row['resolution']
                if resolution not in statList['detailedReport']['bug_resolution']:
                    statList['detailedReport']['bug_resolution'][resolution] = 0
                statList['detailedReport']['bug_resolution'][resolution] += 1

                platform = row['platform']
                if platform not in statList['detailedReport']['bug_platform']:
                    statList['detailedReport']['bug_platform'][platform] = 0
                statList['detailedReport']['bug_platform'][platform] += 1

                system = row['op_sys']
                if system not in statList['detailedReport']['bug_system']:
                    statList['detailedReport']['bug_system'][system] = 0
                statList['detailedReport']['bug_system'][system] += 1

                if rowStatus == 'UNCONFIRMED':
                    statList['detailedReport']['unconfirmed_count'] += 1
                    statList['detailedReport']['lists']['unconfirmed'].append(row['id'])

                statList['detailedReport']['lists']['author'][0].append(key)
                statList['detailedReport']['lists']['author'][1].append(creatorMail)

                week = str(creationDate.year) + '-' + str(creationDate.strftime("%V"))
                if week not in statList['detailedReport']['created_week']:
                    statList['detailedReport']['created_week'][week] = 0
                statList['detailedReport']['created_week'][week] += 1

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

            util_check_bugzilla_mail(statList, creatorMail, row['creator_detail']['real_name'], creationDate)
            util_increase_user_actions(statList, key, creatorMail, bugTargets, 'created', creationDate)

            actionMail = None
            confirmed = False
            fixed = False
            autoConfirmed = False
            versionChanged = False
            everConfirmed = False
            oldestVersion = 999999
            newerVersion = False
            for action in row['history']:
                actionMail = action['who']
                actionDate = datetime.datetime.strptime(action['when'], "%Y-%m-%dT%H:%M:%SZ")
                util_check_bugzilla_mail(statList, actionMail, '', actionDate)

                # Use this variable in case the status is set before the resolution
                newStatus = None
                for change in action['changes']:
                    if change['field_name'] == 'is_confirmed':
                        if actionDate >= cfg[reportPeriod] and row['is_confirmed']:
                            if confirmed:
                                statList['detailedReport']['lists']['confirm'][0].pop()
                                statList['detailedReport']['lists']['confirm'][1].pop()
                                statList['detailedReport']['is_confirm_count'] -= 1

                            statList['detailedReport']['is_confirm_count'] += 1
                            statList['detailedReport']['lists']['confirm'][0].append(key)
                            statList['detailedReport']['lists']['confirm'][1].append(actionMail)
                            confirmed = True

                    if change['field_name'] == 'version':
                        if creationDate >= cfg[reportPeriod] and isOpen(rowStatus):
                            addedVersion = change['added']
                            if addedVersion == 'unspecified':
                                addedVersion = 999999
                            elif addedVersion == 'Inherited From OOo':
                                addedVersion = 0
                            else:
                                addedVersion = int(''.join([s for s in re.split('\.|\s',addedVersion) if s.isdigit()]).ljust(4, '0'))


                            if addedVersion <= oldestVersion:
                                oldestVersion = addedVersion
                                newerVersion = False
                            else:
                                newerVersion = True

                    if change['field_name'] == 'status':

                        addedStatus = change['added']
                        removedStatus = change['removed']
                        if  addedStatus == 'RESOLVED' or addedStatus == 'VERIFIED':
                            if(rowResolution):
                                addedStatus = addedStatus + "_" + rowResolution
                                util_increase_user_actions(statList, key, actionMail, bugTargets, 'status_changed', actionDate)
                                if actionDate >= cfg[reportPeriod] and rowStatus == addedStatus:
                                    statList['detailedReport']['status_changed_to'][addedStatus] += 1
                                    statList['detailedReport']['lists']['status_changed_to'][
                                        addedStatus][0].append(key)
                                    statList['detailedReport']['lists']['status_changed_to'][
                                        addedStatus][1].append(actionMail)
                            else:
                                newStatus = addedStatus
                        else:
                            util_increase_user_actions(statList, key, actionMail, bugTargets, 'status_changed', actionDate)

                            if actionDate >= cfg[reportPeriod] and rowStatus == addedStatus:
                                statList['detailedReport']['status_changed_to'][addedStatus] += 1
                                statList['detailedReport']['lists']['status_changed_to'][
                                    addedStatus][0].append(key)
                                statList['detailedReport']['lists']['status_changed_to'][
                                    addedStatus][1].append(actionMail)

                        if actionDate >= cfg[reportPeriod] and addedStatus == 'RESOLVED_FIXED':
                            if fixed:
                                statList['detailedReport']['lists']['fixed'][0].pop()
                                statList['detailedReport']['lists']['fixed'][1].pop()
                                statList['detailedReport']['is_fixed'] -= 1

                            statList['detailedReport']['lists']['fixed'][0].append(key)
                            statList['detailedReport']['lists']['fixed'][1].append(actionMail)
                            statList['detailedReport']['is_fixed'] += 1
                            fixed = True

                        #if any other user moves it to open ( ASSIGNED, NEW or REOPENED ),
                        #the bug is no longer autoconfirmed
                        if not everConfirmed and isOpen(rowStatus) and isOpen(addedStatus) and actionMail != creatorMail:
                                everConfirmed = True
                                autoConfirmed = False

                        #Check for autoconfirmed bugs:
                        #Bug's status is open ( ASSIGNED, NEW or REOPENED ), moved to open by the reporter
                        #from non-open status and never confirmed by someone else.
                        #Ignore bisected bugs
                        if creationDate >= cfg[reportPeriod] and not everConfirmed and actionMail == creatorMail and \
                            isOpen(rowStatus) and isOpen(addedStatus) and 'bisected' not in keywords:
                                autoConfirmed = True

                    elif newStatus and change['field_name'] == 'resolution':
                        addedStatus = newStatus + "_" + change['added']
                        util_increase_user_actions(statList, key, actionMail, bugTargets, 'status_changed', actionDate)

                        if actionDate >= cfg[reportPeriod] and rowStatus == addedStatus:
                            statList['detailedReport']['status_changed_to'][addedStatus] += 1
                            statList['detailedReport']['lists']['status_changed_to'][addedStatus][0].append(key)
                            statList['detailedReport']['lists']['status_changed_to'][addedStatus][1].append(actionMail)

                        newStatus = None

                    elif change['field_name'] == 'priority':
                        newPriority = change['added']
                        util_increase_user_actions(statList, key, actionMail, bugTargets, 'priority_changed', actionDate)
                        if actionDate >= cfg[reportPeriod] and newPriority == row['priority']:
                            statList['detailedReport']['priority_changed'][newPriority] += 1
                            statList['detailedReport']['lists']['priority_changed'][newPriority][0].append(key)
                            statList['detailedReport']['lists']['priority_changed'][newPriority][1].append(actionMail)


                    elif change['field_name'] == 'severity':
                        newSeverity = change['added']
                        util_increase_user_actions(statList, key, actionMail, bugTargets, 'severity_changed', actionDate)
                        if actionDate >= cfg[reportPeriod] and newSeverity == row['severity']:
                            statList['detailedReport']['severity_changed'][newSeverity] += 1
                            statList['detailedReport']['lists']['severity_changed'][newSeverity][0].append(key)
                            statList['detailedReport']['lists']['severity_changed'][newSeverity][1].append(actionMail)

                    elif change['field_name'] == 'keywords':
                        keywordsAdded = change['added'].split(", ")
                        for keyword in keywordsAdded:
                            if keyword in keywords_list:
                                util_increase_user_actions(statList, key, actionMail, bugTargets, 'keyword_added', actionDate)

                                if actionDate >= cfg[reportPeriod] and keyword in row['keywords']:
                                    statList['detailedReport']['keyword_added'][keyword] += 1
                                    statList['detailedReport']['lists']['keyword_added'][keyword][0].append(key)
                                    statList['detailedReport']['lists']['keyword_added'][keyword][1].append(actionMail)

                                    if keyword == 'haveBacktrace':
                                        if rowStatus not in statList['detailedReport']['backTraceStatus']:
                                            statList['detailedReport']['backTraceStatus'][rowStatus] = 0
                                        statList['detailedReport']['backTraceStatus'][rowStatus] += 1
                                    elif keyword == 'regression':
                                        if rowStatus not in statList['detailedReport']['regressionStatus']:
                                            statList['detailedReport']['regressionStatus'][rowStatus] = 0
                                        statList['detailedReport']['regressionStatus'][rowStatus] += 1
                                    elif keyword == 'bisected':
                                        if rowStatus not in statList['detailedReport']['bisectedStatus']:
                                            statList['detailedReport']['bisectedStatus'][rowStatus] = 0
                                        statList['detailedReport']['bisectedStatus'][rowStatus] += 1



                        keywordsRemoved = change['removed'].split(", ")
                        for keyword in keywordsRemoved:
                            if keyword in keywords_list:
                                util_increase_user_actions(statList, key, actionMail, bugTargets, 'keyword_removed', actionDate)

                                if actionDate >= cfg[reportPeriod] and keyword not in row['keywords']:
                                    statList['detailedReport']['keyword_removed'][keyword] += 1

                                    statList['detailedReport']['lists']['keyword_removed'][keyword][0].append(key)
                                    statList['detailedReport']['lists']['keyword_removed'][keyword][1].append(actionMail)

                    elif change['field_name'] == 'whiteboard':
                        for whiteboard in change['added'].split(' '):
                            if 'backportrequest' in whiteboard.lower():
                                util_increase_user_actions(statList, key, actionMail, bugTargets, 'whiteboard_added', actionDate)

                                if actionDate >= cfg[reportPeriod] and whiteboard in row['whiteboard']:
                                    if whiteboard not in statList['detailedReport']['whiteboard_added']:
                                        statList['detailedReport']['whiteboard_added'][whiteboard] = 0
                                        statList['detailedReport']['lists']['whiteboard_added'][whiteboard] = [[],[]]
                                    statList['detailedReport']['whiteboard_added'][whiteboard] += 1

                                    statList['detailedReport']['lists']['whiteboard_added'][whiteboard][0].append(key)
                                    statList['detailedReport']['lists']['whiteboard_added'][whiteboard][1].append(actionMail)

                        for whiteboard in change['removed'].split(' '):
                            if 'backportrequest' in whiteboard.lower():
                                util_increase_user_actions(statList, key, actionMail, bugTargets, 'whiteboard_removed', actionDate)

                                if actionDate >= cfg[reportPeriod] and whiteboard not in row['whiteboard']:
                                    if whiteboard not in statList['detailedReport']['whiteboard_removed']:
                                        statList['detailedReport']['whiteboard_removed'][whiteboard] = 0
                                        statList['detailedReport']['lists']['whiteboard_removed'][whiteboard] = [[],[]]
                                    statList['detailedReport']['whiteboard_removed'][whiteboard] += 1

                                    statList['detailedReport']['lists']['whiteboard_removed'][whiteboard][0].append(key)
                                    statList['detailedReport']['lists']['whiteboard_removed'][whiteboard][1].append(actionMail)

                    elif change['field_name'] == 'op_sys':
                        newPlatform = change['added']
                        util_increase_user_actions(statList, key, actionMail, bugTargets, 'system_changed', actionDate)

                        if actionDate >= cfg[reportPeriod] and newPlatform not in row['platform']:
                            statList['detailedReport']['system_changed'][newPlatform] += 1

                            statList['detailedReport']['lists']['system_changed'][newPlatform][0].append(key)
                            statList['detailedReport']['lists']['system_changed'][newPlatform][1].append(actionMail)

            commentMail = None
            for comment in row['comments'][1:]:
                commentMail = comment['creator']
                commentDate = datetime.datetime.strptime(comment['time'], "%Y-%m-%dT%H:%M:%SZ")

                util_check_bugzilla_mail(statList, commentMail, '', commentDate)

                util_increase_user_actions(statList, key, commentMail, bugTargets, 'comments', commentDate)
                if commentDate >= cfg[reportPeriod]:
                    statList['detailedReport']['comments_count'] += 1

            for person in row['cc_detail']:
                email = person['email']
                if commentMail == email or actionMail == email:
                    util_check_bugzilla_mail(statList, email, person['real_name'])

            if autoConfirmed:
                total += 1
                print(str(total) + " - AUTO-CONFIRMED: https://bugs.documentfoundation.org/show_bug.cgi?id=" + str(row['id']))

            if newerVersion:
                total += 1
                print(str(total) + " - VERSION CHANGED TO A NEWER ONE: https://bugs.documentfoundation.org/show_bug.cgi?id=" + str(row['id']))

    for k, v in statList['people'].items():
        if not statList['people'][k]['name']:
            statList['people'][k]['name'] = statList['people'][k]['email'].split('@')[0]

        if statList['people'][k]['oldest'] >= cfg[newUsersPeriod]:
            statList['newUsersPeriod'][k] = statList['people'][k]

        statList['people'][k]['oldest'] = statList['people'][k]['oldest'].strftime("%Y-%m-%d")
        statList['people'][k]['newest'] = statList['people'][k]['newest'].strftime("%Y-%m-%d")


    statList['stat']['newest'] = statNewDate.strftime("%Y-%m-%d")
    statList['stat']['oldest'] = statOldDate.strftime("%Y-%m-%d")
    print(" from " + statList['stat']['oldest'] + " to " + statList['stat']['newest'])

def util_print_QA_line(fp, statList, string, number, tuple, action):

    if len(tuple[0]) == 1:
        auxString = 'bug has'
    else:
        auxString = "bugs have"

    if action == 'keyword_added' or action == 'whiteboard_added':
        print(('  * \'' + string + '\' has been added to {} bugs.').format(number), file=fp)
    elif action == 'keyword_removed' or action == 'whiteboard_removed':
        print(('  * \'' + string + '\' has been removed from {} bugs.').format(number), file=fp)
    elif action == 'created':
        print(('  * {} have been created, of which, {} are still unconfirmed ( Total Unconfirmed bugs: {} )').format(
                number[0], number[1], number[2]), file=fp)
    elif action == 'author':
        print(('  * {} have been created.').format(number), file=fp)
    else:
        print(('  * {} ' + auxString + ' been changed to \'' + string + '\'.').format(number), file=fp)


    url = "https://bugs.documentfoundation.org/buglist.cgi?bug_id="
    for bug in tuple[0]:
        url += str(bug) + "%2C"

    url = url[:-3]
    shortener = Shortener('Tinyurl', timeout=9000)
    print('\tLink: ' + shortener.short(url), file=fp)

    if not action == 'created':

        #Count the number of reps
        my_dict = {i: tuple[1].count(i) for i in tuple[1]}

        d_view = [(v, k) for k, v in my_dict.items()]

        d_view.sort(reverse=True)
        usersString = '\tDone by: '

        for i1,i2 in d_view:
            try:
                usersString += statList['people'][i2]['name'] + ' ( ' + str(i1) + ' ), '
            except:
                continue

        print(usersString[:-2], file=fp)

    print(file=fp)

def util_print_QA_line_blog(fp, statList, number, tuple, total_count):

    if len(tuple[0]) == 1:
        auxString = 'bug.'
    else:
        auxString = "bugs."

    print(('  * {} ' + auxString).format(number), file=fp)

    #Count the number of reps
    my_dict = {i: tuple[1].count(i) for i in tuple[1]}

    d_view = [(v, k) for k, v in my_dict.items()]
    d_view.sort(reverse=True)

    print('  * Total users: {}'.format(len(d_view)), file=fp)

    usersString = '  * Done by: \n'

    count = 0
    for i1,i2 in d_view:
        try:
            count += 1
            if count <= total_count:
                usersString += statList['people'][i2]['name'] + ' ( ' + str(i1) + ' ) \n'
            else:
                break
        except:
            continue

    print(usersString[:-2], file=fp)

    print(file=fp)

def util_print_QA_line_created(fp, d , whole):
    others = 0
    s = [(k, d[k]) for k in sorted(d, key=d.get, reverse=True)]
    total = 0
    for k, v in s:
        percent = 100 * float(v)/float(whole)
        if percent >= 3:
            print('{}: {} \t\t {}%'.format(k, v, percent), file=fp)
            total += percent
        else:
            others += v
    others_percent = 100 - total
    print('OTHERS: {} \t\t {}%'.format(others, others_percent) , file=fp)


def create_wikimedia_table_by_target(cfg, statList):
    from tabulate import tabulate
    for kT,vT in sorted(statList['targets'].items()):
        print('Creating wikimedia table for release ' + kT)
        output = ""

        output += '{{TopMenu}}\n'
        output += '{{Menu}}\n'
        output += '{{Menu.QA}}\n'
        output += '\n'

        output += '{} people helped to triage {} bugs tagged with target:{}. (sorted in alphabetical order by user\'s name)\n'.format(
            len(vT['people']), vT['count'], kT)
        output += '\n'
        table = []
        headers = ['Name', 'Created', 'Comments', 'Status Changed', 'Keyword Added', 'Keyword Removed',
                   'Severity Changed', 'Priority Changed', 'System Changed', 'Total Bugs']

        for kP, vP in vT['people'].items():
            name = statList['people'][kP]['name']
            if not name:
                name = statList['people'][kP]['email'].split('@')[0]

            if not name == 'libreoffice-commits':
                arrow = []
                arrow.append(name)
                arrow.append(vP['created'])
                arrow.append(vP['comments'])
                arrow.append(vP['status_changed'])
                arrow.append(vP['keyword_added'])
                arrow.append(vP['keyword_removed'])
                arrow.append(vP['severity_changed'])
                arrow.append(vP['priority_changed'])
                arrow.append(vP['system_changed'])
                arrow.append(len(set(vP['bugs'])))
                table.append(arrow)

        output += tabulate(sorted(table, key = lambda x: x[0]), headers, tablefmt='mediawiki')
        output += "\n"
        output +='Generated on {}.'.format(cfg['todayDate'])
        output += "\n"
        output += '[[Category:EN]]\n'
        output += '[[Category:QA/Stats]]'

        fp = open('/tmp/' + kT + '_table.txt', 'w', encoding='utf-8')
        print(output.replace('wikitable', 'wikitable sortable'), file=fp)
        fp.close()

def create_wikimedia_table_by_period(cfg, statList):
    from tabulate import tabulate
    for kT,vT in sorted(statList['period'].items()):
        print('Creating wikimedia table for actions done in the last {} days.'.format(kT[:-1]))
        output = ""

        output += '{{TopMenu}}\n'
        output += '{{Menu}}\n'
        output += '{{Menu.QA}}\n'
        output += '\n'

        output += '{} people helped to triage {} bugs in the last {} days. (sorted in alphabetical order by user\'s name)\n'.format(
            len(vT['people']), vT['count'], kT[:-1])
        output += '\n'
        table = []
        headers = ['Name', 'Created', 'Comments', 'Status Changed', 'Keyword Added', 'Keyword Removed',
                   'Severity Changed', 'Priority Changed', 'System Changed', 'Total Bugs']

        for kP, vP in vT['people'].items():
            name = statList['people'][kP]['name']
            if not name:
                name = statList['people'][kP]['email'].split('@')[0]

            if not name == 'libreoffice-commits':
                arrow = []
                arrow.append(name)
                arrow.append(vP['created'])
                arrow.append(vP['comments'])
                arrow.append(vP['status_changed'])
                arrow.append(vP['keyword_added'])
                arrow.append(vP['keyword_removed'])
                arrow.append(vP['severity_changed'])
                arrow.append(vP['priority_changed'])
                arrow.append(vP['system_changed'])
                arrow.append(len(set(vP['bugs'])))
                table.append(arrow)

        output += tabulate(sorted(table, key = lambda x: x[0]), headers, tablefmt='mediawiki')
        output += "\n"
        output += 'Generated on {}.'.format(cfg['todayDate'])
        output += "\n"
        output += '[[Category:EN]]\n'
        output += '[[Category:QA/Stats]]'

        fp = open('/tmp/' + kT + '_period.txt', 'w', encoding='utf-8')
        print(output.replace('wikitable', 'wikitable sortable'), file=fp)
        fp.close()

def users_Report(statList) :
    print('Users report from {} to {}'.format(cfg[newUsersPeriod].strftime("%Y-%m-%d"), statList['stat']['newest']))
    #fp = open('/tmp/users_report.txt', 'w', encoding='utf-8')

    print('{} new users in the last {} days'.format(len(statList['newUsersPeriod']), newUsersPeriod[:-1]))

    for v,k in statList['newUsersPeriod'].items():
        print(v)

def Blog_Report(statList) :
    fp = open('/tmp/blog_report.txt', 'w', encoding='utf-8')

    print('* Report from {} to {}'.format(cfg[reportPeriod].strftime("%Y-%m-%d"), statList['stat']['newest']), file=fp )

    print('* Total report created: {}'.format(statList['detailedReport']['created_count']), file=fp)

    print('* Total enhancements created: {}'.format(statList['detailedReport']['enhancement_count']), file=fp)

    print('* Total bugs created: {}'.format(statList['detailedReport']['no_enhancement_count']), file=fp)
    print(file=fp)

    print('* Bugs reported.', file=fp)
    util_print_QA_line_blog(fp, statList,
                       statList['detailedReport']['created_count'],
                       statList['detailedReport']['lists']['author'], 15)


    print(file=fp)
    print('* Bugs confirmed.', file=fp)
    util_print_QA_line_blog(fp, statList,
                       statList['detailedReport']['is_confirm_count'],
                       statList['detailedReport']['lists']['confirm'], 20)

    print(file=fp)
    print('* Bugs fixed.', file=fp)
    util_print_QA_line_blog(fp, statList,
                       statList['detailedReport']['is_fixed'],
                       statList['detailedReport']['lists']['fixed'], 20)


    print(file=fp)
    for key, value in sorted(statList['detailedReport']['keyword_added'].items()):
        if value and key in ['easyHack', 'bisected', 'haveBacktrace', 'regression']:
            print('* ' + key + '.', file=fp)
            util_print_QA_line_blog(fp, statList, value,
                statList['detailedReport']['lists']['keyword_added'][key], 15)

    print(file=fp)
    for key, value in sorted(statList['detailedReport']['status_changed_to'].items()):
        if value and key in ['RESOLVED_DUPLICATE', 'VERIFIED_FIXED']:
            print('* ' + key.replace("_", " ") + '.', file=fp)
            util_print_QA_line_blog(fp, statList, value,
                               statList['detailedReport']['lists']['status_changed_to'][key], 20)

    print(file=fp)
    print('* Bugs created by week', file=fp)

    for key, value in sorted(statList['detailedReport']['created_week'].items()):
        print('{}: {}'.format(key, value), file=fp)

    whole = statList['detailedReport']['created_count']

    print(file=fp)
    print('* Components of created bugs', file=fp)
    util_print_QA_line_created(fp, statList['detailedReport']['bug_component'], whole)

    print(file=fp)
    print('* Systems of created bugs', file=fp)
    util_print_QA_line_created(fp, statList['detailedReport']['bug_system'], whole)

    print(file=fp)
    print('* Platforms of created bugs', file=fp)
    util_print_QA_line_created(fp, statList['detailedReport']['bug_platform'], whole)

    print(file=fp)
    print('* Statuses of created bugs', file=fp)
    util_print_QA_line_created(fp, statList['detailedReport']['bug_status'], whole)

    print(file=fp)
    print('* Resolution of created bugs', file=fp)
    util_print_QA_line_created(fp, statList['detailedReport']['bug_resolution'],
        statList['detailedReport']['bug_status']['RESOLVED'])

    print(file=fp)
    print('* Regressions statuses', file=fp)
    util_print_QA_line_created(fp, statList['detailedReport']['regressionStatus'],
        statList['detailedReport']['keyword_added']['regression'])

    print(file=fp)
    print('* Bisected statuses', file=fp)
    util_print_QA_line_created(fp, statList['detailedReport']['bisectedStatus'],
        statList['detailedReport']['keyword_added']['bisected'])

    print(file=fp)
    print('* Backtrace statuses', file=fp)
    util_print_QA_line_created(fp, statList['detailedReport']['backTraceStatus'],
        statList['detailedReport']['keyword_added']['haveBacktrace'])

    fp.close()

def QA_Report(statList) :
    print('QA report from {} to {}'.format(cfg[reportPeriod].strftime("%Y-%m-%d"), statList['stat']['newest']))
    fp = open('/tmp/qa_report.txt', 'w', encoding='utf-8')

    print('Hello,', file=fp)
    print(file=fp)
    print('What have happened in QA in the last {} days?'.format(reportPeriod[:-1]), file=fp)
    print(file=fp)

    util_print_QA_line(fp, statList, '',
                       [statList['detailedReport']['created_count'], statList['detailedReport']['unconfirmed_count'],
                        statList['data']['bugs']['all']['status']['UNCONFIRMED']],
                       [statList['detailedReport']['lists']['unconfirmed']], 'created')

    print('  * {} comments have been written.'.format(statList['detailedReport']['comments_count']), file=fp)
    print(file=fp)

    print("== STATUS CHANGED ==", file=fp)
    for key, value in sorted(statList['detailedReport']['status_changed_to'].items()):
        if value:
            util_print_QA_line(fp, statList, key.replace("_", " "), value,
                               statList['detailedReport']['lists']['status_changed_to'][key], 'status_changed_to')


    print("== KEYWORDS ADDED ==", file=fp)
    for key, value in sorted(statList['detailedReport']['keyword_added'].items()):
        if value:
            util_print_QA_line(fp, statList, key, value,
                statList['detailedReport']['lists']['keyword_added'][key], 'keyword_added')


    print("== KEYWORDS REMOVED ==", file=fp)
    for key, value in sorted(statList['detailedReport']['keyword_removed'].items()):
        if value:
            util_print_QA_line(fp, statList, key, value,
                statList['detailedReport']['lists']['keyword_removed'][key], 'keyword_removed')

    print("== BACKPORTREQUEST ADDED ==", file=fp)
    for key, value in sorted(statList['detailedReport']['whiteboard_added'].items()):
        if value:
            util_print_QA_line(fp, statList, key, value,
                statList['detailedReport']['lists']['whiteboard_added'][key], 'whiteboard_added')


    print("== BACKPORTREQUEST REMOVED ==", file=fp)
    for key, value in sorted(statList['detailedReport']['whiteboard_removed'].items()):
        if value:
            util_print_QA_line(fp, statList, key, value,
                statList['detailedReport']['lists']['whiteboard_removed'][key], 'whiteboard_removed')


    print("== SEVERITY CHANGED ==", file=fp)
    for key, value in sorted(statList['detailedReport']['severity_changed'].items()):
        if value:
            util_print_QA_line(fp, statList, key, value,
                               statList['detailedReport']['lists']['severity_changed'][key], 'severity_changed')

    print("== PRIORITY CHANGED ==", file=fp)
    for key, value in sorted(statList['detailedReport']['priority_changed'].items()):
        if value:
            util_print_QA_line(fp, statList, key, value,
                               statList['detailedReport']['lists']['priority_changed'][key], 'priority_changed')


    print("== SYSTEM CHANGED ==", file=fp)
    for key, value in sorted(statList['detailedReport']['system_changed'].items()):
        if value:
            util_print_QA_line(fp, statList, key, value,
                               statList['detailedReport']['lists']['system_changed'][key], 'system_changed')

    print('Thank you all for making Libreoffice rock!', file=fp)
    print(file=fp)
    print('Generated on {} based on stats from {}. Note: Metabugs are ignored.'.format(
        datetime.datetime.now().strftime("%Y-%m-%d"), statList['addDate']), file=fp)
    print(file=fp)
    print('Regards', file=fp)
    fp.close()

def runCfg(homeDir):
    cfg = {}
    cfg['homedir'] = homeDir
    cfg['todayDate'] = datetime.datetime.now().replace(hour=0, minute=0,second=0)
    cfg[reportPeriod] = cfg['todayDate'] - datetime.timedelta(days= int(reportPeriod[:-1]))
    cfg[newUsersPeriod] = cfg['todayDate'] - datetime.timedelta(days= int(newUsersPeriod[:-1]))

    for period in periods_list:
        cfg[period] = cfg['todayDate'] - datetime.timedelta(days= int(period[:-1]))

    return cfg

if __name__ == '__main__':
    print("Reading and writing data to " + homeDir)

    cfg = runCfg(homeDir)

    bugzillaData = get_bugzilla(cfg)

    statList = util_create_statList()
    analyze_bugzilla(statList, bugzillaData, cfg)

    if len(sys.argv) > 1:
        if sys.argv[1] == 'report':
            QA_Report(statList)
        if sys.argv[1] == 'blog':
            Blog_Report(statList)
        elif sys.argv[1] == 'targets':
            create_wikimedia_table_by_target(cfg, statList)
        elif sys.argv[1] == 'periods':
            create_wikimedia_table_by_period(cfg, statList)
        elif sys.argv[1] == 'users':
            users_Report(statList)
        else:
            print('You must use \'report\', \'targets\', \'periods\' or \'users\' as parameter.')
            sys.exit(1)
    else:
        QA_Report(statList)
        create_wikimedia_table_by_target(cfg, statList)
        create_wikimedia_table_by_period(cfg, statList)

    print('End of report')
