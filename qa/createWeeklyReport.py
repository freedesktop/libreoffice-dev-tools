#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import common
import datetime

reportPeriodDays = 7

def util_create_statList_weeklyReport():
    return {
        'created': [],
        'still_unconfirmed': [],
        'unconfirmed': [],
        'newUsers': {},
        'comments_count': {},
        'status_changed': {s: {'id':[], 'author': [] } for s in common.statutes_list},
        'keyword_added': {k: {'id':[], 'author': [], 'status': {s:0 for s in common.statutes_list}} for k in common.keywords_list},
        'keyword_removed': {k: {'id':[], 'author': []} for k in common.keywords_list},
        'whiteboard_added': {},
        'whiteboard_removed': {},
        'severity_changed': {s: {'id':[], 'author': []} for s in common.severities_list},
        'priority_changed': {p: {'id':[], 'author': []} for p in common.priorities_list},
        'system_changed': {p: {'id':[], 'author': []} for p in common.system_list},
        'metabug_added': {},
        'metabug_removed': {},
        'people': {},
        'metabugAlias': {},
        'stat': {'oldest': datetime.datetime.now(), 'newest': datetime.datetime(2001, 1, 1)}
    }

def analyze_bugzilla_weeklyReport(statList, bugzillaData, cfg):
    print("Analyzing Bugzilla\n", end="", flush=True)
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

            if rowStatus == 'UNCONFIRMED':
                statList['unconfirmed'].append(rowId)

            if creationDate >= cfg['reportPeriod']:
                statList['created'].append(rowId)
                if rowStatus == 'UNCONFIRMED':
                    statList['still_unconfirmed'].append(rowId)

            rowKeywords = row['keywords']

            creatorMail = row['creator']

            crashSignature = row['cf_crashreport']

            common.util_check_bugzilla_mail(statList, creatorMail, row['creator_detail']['real_name'], creationDate, rowId)

            for action in row['history']:
                actionMail = action['who']
                actionDate = datetime.datetime.strptime(action['when'], "%Y-%m-%dT%H:%M:%SZ")
                common.util_check_bugzilla_mail(statList, actionMail, '', actionDate, rowId)

                # Use this variable in case the status is set before the resolution
                newStatus = None
                for change in action['changes']:
                    if change['field_name'] == 'blocks':
                        if change['added']:
                            for metabug in change['added'].split(', '):

                                if actionDate >= cfg['reportPeriod'] and int(metabug) in row['blocks']:
                                    if metabug not in statList['metabug_added']:
                                        statList['metabug_added'][metabug] = {'id':[], 'author':[]}

                                    statList['metabug_added'][metabug]['id'].append(rowId)
                                    statList['metabug_added'][metabug]['author'].append(actionMail)

                        if change['removed']:
                            for metabug in change['removed'].split(', '):

                                if actionDate >= cfg['reportPeriod'] and int(metabug) not in row['blocks']:
                                    if metabug not in statList['metabug_removed']:
                                        statList['metabug_removed'][metabug] = {'id':[], 'author':[]}

                                    statList['metabug_removed'][metabug]['id'].append(rowId)
                                    statList['metabug_removed'][metabug]['author'].append(actionMail)

                    if change['field_name'] == 'status':
                        addedStatus = change['added']
                        removedStatus = change['removed']

                        if rowStatus == 'ASSIGNED' and addedStatus == 'ASSIGNED':
                            lastAssignedEmail = actionMail

                        if  addedStatus == 'RESOLVED' or addedStatus == 'VERIFIED':
                            if(rowResolution):
                                addedStatus = addedStatus + "_" + rowResolution
                                if actionDate >= cfg['reportPeriod'] and rowStatus == addedStatus:
                                    statList['status_changed'][addedStatus]['id'].append(rowId)
                                    statList['status_changed'][addedStatus]['author'].append(actionMail)
                            else:
                                newStatus = addedStatus
                        else:

                            if actionDate >= cfg['reportPeriod'] and rowStatus == addedStatus:
                                statList['status_changed'][addedStatus]['id'].append(rowId)
                                statList['status_changed'][addedStatus]['author'].append(actionMail)

                    elif change['field_name'] == 'resolution':
                        if newStatus:
                            addedStatus = newStatus + "_" + change['added']

                            if actionDate >= cfg['reportPeriod'] and rowStatus == addedStatus:
                                statList['status_changed'][addedStatus]['id'].append(rowId)
                                statList['status_changed'][addedStatus]['author'].append(actionMail)

                            newStatus = None

                    elif change['field_name'] == 'priority':
                        newPriority = change['added']
                        if actionDate >= cfg['reportPeriod'] and newPriority == row['priority']:
                            statList['priority_changed'][newPriority]['id'].append(rowId)
                            statList['priority_changed'][newPriority]['author'].append(actionMail)


                    elif change['field_name'] == 'severity':
                        newSeverity = change['added']
                        if actionDate >= cfg['reportPeriod'] and newSeverity == row['severity']:
                            statList['severity_changed'][newSeverity]['id'].append(rowId)
                            statList['severity_changed'][newSeverity]['author'].append(actionMail)

                    elif change['field_name'] == 'keywords':
                        keywordsAdded = change['added'].split(", ")
                        for keyword in keywordsAdded:
                            if keyword in common.keywords_list:

                                if actionDate >= cfg['reportPeriod'] and keyword in rowKeywords:
                                    statList['keyword_added'][keyword]['id'].append(rowId)
                                    statList['keyword_added'][keyword]['author'].append(actionMail)
                                    statList['keyword_added'][keyword]['status'][rowStatus] += 1

                        keywordsRemoved = change['removed'].split(", ")
                        for keyword in keywordsRemoved:
                            if keyword in common.keywords_list:

                                if actionDate >= cfg['reportPeriod'] and keyword not in rowKeywords:
                                    statList['keyword_removed'][keyword]['id'].append(rowId)
                                    statList['keyword_removed'][keyword]['author'].append(actionMail)

                    elif change['field_name'] == 'whiteboard':
                        for whiteboard in change['added'].split(' '):
                            if 'backportrequest' in whiteboard.lower():

                                if actionDate >= cfg['reportPeriod'] and whiteboard in row['whiteboard']:
                                    if whiteboard not in statList['whiteboard_added']:
                                        statList['whiteboard_added'][whiteboard] = {'id':[], 'author':[]}

                                    statList['whiteboard_added'][whiteboard]['id'].append(rowId)
                                    statList['whiteboard_added'][whiteboard]['author'].append(actionMail)


                        for whiteboard in change['removed'].split(' '):
                            if 'backportrequest' in whiteboard.lower():

                                if actionDate >= cfg['reportPeriod'] and whiteboard not in row['whiteboard']:
                                    if whiteboard not in statList['whiteboard_removed']:
                                        statList['whiteboard_removed'][whiteboard] = {'id':[], 'author':[]}

                                    statList['whiteboard_removed'][whiteboard]['id'].append(rowId)
                                    statList['whiteboard_removed'][whiteboard]['author'].append(actionMail)

                    elif change['field_name'] == 'op_sys':
                        newSystem = change['added']

                        if actionDate >= cfg['reportPeriod'] and newSystem in row['op_sys']:
                            statList['system_changed'][newSystem]['id'].append(rowId)
                            statList['system_changed'][newSystem]['author'].append(actionMail)

                    elif change['field_name'] == 'assigned_to':
                        if actionDate >= cfg['reportPeriod']:
                            removedAssignee = change['removed']
                            addedAssignee = change['added']
                            if  removedAssignee == "libreoffice-bugs@lists.freedesktop.org" and \
                                    row['assigned_to'] != 'libreoffice-bugs@lists.freedesktop.org' and \
                                    ( rowStatus == 'NEW' or rowStatus == 'UNCONFIRMED'):
                                addAssigned = True
                                addAssignedMail = actionMail
                            if addedAssignee == "libreoffice-bugs@lists.freedesktop.org" and \
                                    row['assigned_to'] == 'libreoffice-bugs@lists.freedesktop.org' and \
                                    rowStatus == 'ASSIGNED':
                                removeAssigned = True
                                removeAssignedMail = actionMail

            commentMail = None
            comments = row['comments'][1:]
            for idx, comment in enumerate(comments):
                commentMail = comment['creator']
                commentDate = datetime.datetime.strptime(comment['time'], "%Y-%m-%dT%H:%M:%SZ")

                common.util_check_bugzilla_mail(statList, commentMail, '', commentDate, rowId)

                if commentDate >= cfg['reportPeriod']:
                    if commentMail not in statList['comments_count']:
                        statList['comments_count'][commentMail] = 0
                    statList['comments_count'][commentMail] += 1

        elif row['summary'].lower().startswith('[meta]'):
            statList['metabugAlias'][rowId] = row['alias']

    for k, v in statList['people'].items():
        if not statList['people'][k]['name']:
            statList['people'][k]['name'] = statList['people'][k]['email'].split('@')[0]

        if statList['people'][k]['oldest'] >= cfg['reportPeriod']:
            statList['newUsers'][k] = statList['people'][k]

        statList['people'][k]['oldest'] = statList['people'][k]['oldest'].strftime("%Y-%m-%d")
        statList['people'][k]['newest'] = statList['people'][k]['newest'].strftime("%Y-%m-%d")

    statList['stat']['newest'] = statNewDate.strftime("%Y-%m-%d")
    statList['stat']['oldest'] = statOldDate.strftime("%Y-%m-%d")
    print(" from " + statList['stat']['oldest'] + " to " + statList['stat']['newest'])

def util_print_QA_line_weekly(fp, statList, dValue, action, isMetabug=False):

    #Replace metabugs keys by aliases
    if isMetabug:
        dValueAux = {}
        for key, value in dValue.items():
            if int(key) in statList['metabugAlias'] and \
                    statList['metabugAlias'][int(key)]:
                dValueAux[statList['metabugAlias'][int(key)][0]] = dValue[key]
        dValue = dValueAux

    for key, value in sorted(dValue.items()):
        if value['id']:
            nBugs = len(value['id'])
            if nBugs == 1:
                aux1 = 'bug has'
                aux2 = 'bug'
            else:
                aux1 = "bugs have"
                aux2 = 'bugs'

            if action == 'added' or action == 'removed':
                aux3 = 'to'
                if action == 'removed':
                    aux3 = 'from'
                print(('  * \'{}\' has been {} {} {} {}.').format(key, action, aux3, nBugs, aux2), file=fp)
            else:
                print(('  * {} {} been changed to \'{}\'.').format(nBugs, aux1, key.replace('_', ' ')), file=fp)

            common.util_create_short_url(fp, value['id'])
            #Count the number of reps
            my_dict = {i: value['author'].count(i) for i in value['author']}

            d_view = [(v, k) for k, v in my_dict.items()]

            d_view.sort(reverse=True)
            usersString = '\t\t+ Done by: '

            for i1,i2 in d_view:
                try:
                    usersString += statList['people'][i2]['name'] + ' ( ' + str(i1) + ' ), '
                except:
                    continue

            print(usersString[:-2], file=fp)
            print(file=fp)

def create_weekly_Report(statList) :
    print('QA report from {} to {}'.format(cfg['reportPeriod'].strftime("%Y-%m-%d"), statList['stat']['newest']))
    fp = open('/tmp/weekly_report.txt', 'w', encoding='utf-8')

    print('Hello,', file=fp)
    print(file=fp)
    print('What have happened in QA in the last {} days?'.format(reportPeriodDays), file=fp)
    print(file=fp)

    print('  * {} bugs have been created, of which, {} are still unconfirmed ( Total Unconfirmed bugs: {} )'.format(\
            len(statList['created']),
            len(statList['still_unconfirmed']),
            len(statList['unconfirmed'])), file=fp)

    common.util_create_short_url(fp, statList['created'], 'Created bugs')
    common.util_create_short_url(fp, statList['still_unconfirmed'], 'Still unconfirmed bugs')

    print(file=fp)
    print('  * {} comments have been written by {} users.'.format(
        sum(statList['comments_count'].values()), len(statList['comments_count'])), file=fp)
    print(file=fp)

    print('  * {} new users have signed up to Bugzilla.'.format(len(statList['newUsers'])), file=fp)
    print(file=fp)

    if statList['status_changed']:
        print("== STATUSES CHANGED ==", file=fp)
        util_print_QA_line_weekly(fp, statList, statList['status_changed'], 'changed')

    if statList['keyword_added']:
        print("== KEYWORDS ADDED ==", file=fp)
        util_print_QA_line_weekly(fp, statList, statList['keyword_added'], 'added')

    if statList['keyword_removed']:
        print("== KEYWORDS REMOVED ==", file=fp)
        util_print_QA_line_weekly(fp, statList, statList['keyword_removed'], 'removed')

    if statList['whiteboard_added']:
        print("== BACKPORTREQUEST ADDED ==", file=fp)
        util_print_QA_line_weekly(fp, statList, statList['whiteboard_added'], 'added')

    if statList['whiteboard_removed']:
        print("== BACKPORTREQUEST REMOVED ==", file=fp)
        util_print_QA_line_weekly(fp, statList, statList['whiteboard_removed'], 'removed')

    if statList['severity_changed']:
        print("== SEVERITY CHANGED ==", file=fp)
        util_print_QA_line_weekly(fp, statList, statList['severity_changed'], 'changed')

    if statList['priority_changed']:
        print("== PRIORITY CHANGED ==", file=fp)
        util_print_QA_line_weekly(fp, statList, statList['priority_changed'], 'changed')

    if statList['system_changed']:
        print("== SYSTEM CHANGED ==", file=fp)
        util_print_QA_line_weekly(fp, statList, statList['system_changed'], 'changed')

    if statList['metabug_added']:
        print("== METABUGS ADDED ==", file=fp)
        util_print_QA_line_weekly(fp, statList, statList['metabug_added'], 'added', True)

    if statList['metabug_removed']:
        print("== METABUG REMOVED ==", file=fp)
        util_print_QA_line_weekly(fp, statList, statList['metabug_removed'], 'removed', True)

    print('Thank you all for making Libreoffice rock!', file=fp)
    print(file=fp)
    print('Generated on {} based on stats from {}. Note: Metabugs are ignored.'.format(
        datetime.datetime.now().strftime("%Y-%m-%d"), statList['addDate']), file=fp)
    print(file=fp)
    print('Regards', file=fp)
    fp.close()

def runCfg():
    cfg = common.get_config()
    cfg['todayDate'] = datetime.datetime.now().replace(hour=0, minute=0,second=0)
    cfg['reportPeriod'] = common.util_convert_days_to_datetime(cfg, reportPeriodDays)

    return cfg

if __name__ == '__main__':
    print("Reading and writing data to " + common.dataDir)

    cfg = runCfg()

    bugzillaData = common.get_bugzilla()

    statList = util_create_statList_weeklyReport()

    analyze_bugzilla_weeklyReport(statList, bugzillaData, cfg)

    create_weekly_Report(statList)

    print('End of report')
