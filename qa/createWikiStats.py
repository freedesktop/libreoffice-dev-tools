#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

import common
import datetime
from tabulate import tabulate

targets_list = ['5.4.5', '6.0.1']

periods_list = [30, 60, 90, 180, 365]

minNumOfDupes = 3

def util_create_wiki_statList():
    return {
        'targets': {t:{'count':0, 'people':{}} for t in targets_list},
        'period': {p:{'count':0, 'people':{}} for p in periods_list},
        'dupesBugs': {},
        'duplicates':
            {
                'regressions': {},
                'enhancements': {},
                'bugs':{},
            },
        'CC':
            {
                'regressions': {},
                'enhancements': {},
                'bugs':{}
            },
        'people': {},
        'stat': {'oldest': datetime.datetime.now(), 'newest': datetime.datetime(2001, 1, 1)}
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
             'system_changed': 0,
             'metabug_added': 0,
             'metabug_removed': 0
         }

def util_increase_user_actions(statList, bug, mail, targets, action, actionTime):
    if mail == 'libreoffice-commits@lists.freedesktop.org':
        return

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

def util_create_bug(summary, component, os, version, keywords, creationDate, count_cc):
    return { 'summary': summary,
             'component': component,
             'os': os,
             'version': version,
             'keywords': keywords,
             'creationDate': creationDate,
             'count': count_cc
        }

def analyze_bugzilla_wiki_stats(statList, bugzillaData, cfg):
    print("Analyzing bugzilla\n", end="", flush=True)
    statNewDate = statList['stat']['newest']
    statOldDate = statList['stat']['oldest']

    for key, row in bugzillaData['bugs'].items():
        rowId = row['id']

        #Ignore META bugs and deletionrequest bugs.
        if not row['summary'].lower().startswith('[meta]') and row['component'].lower() != 'deletionrequest':
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

            common.util_check_bugzilla_mail(
                    statList, creatorMail, row['creator_detail']['real_name'], creationDate, rowId)

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

            util_increase_user_actions(statList, key, creatorMail, bugTargets, 'created', creationDate)

            if common.isOpen(rowStatus) and len(row['cc']) >= 10:
                typeName = 'bugs'
                if row['severity'] == "enhancement":
                    typeName = 'enhancements'
                elif 'regression' in rowKeywords:
                    typeName = 'regressions'
                statList['CC'][typeName][rowId] = util_create_bug(
                        row['summary'], row['component'], row['op_sys'], row['version'], rowKeywords, creationDate, len(row['cc']))

            rowDupeOf = common.util_check_duplicated(bugzillaData, rowId)
            if rowDupeOf and str(rowDupeOf) in bugzillaData['bugs'] and \
                        common.isOpen(bugzillaData['bugs'][str(rowDupeOf)]['status']):
                if rowDupeOf not in statList['dupesBugs']:
                    statList['dupesBugs'][rowDupeOf] = []
                statList['dupesBugs'][rowDupeOf].append(rowId)

                typeName = 'bugs'
                if bugzillaData['bugs'][str(rowDupeOf)]['severity'] == "enhancement":
                    typeName = 'enhancements'
                elif 'regression' in bugzillaData['bugs'][str(rowDupeOf)]['keywords']:
                    typeName = 'regressions'

                statList['duplicates'][typeName][rowDupeOf] = util_create_bug(
                bugzillaData['bugs'][str(rowDupeOf)]['summary'],
                bugzillaData['bugs'][str(rowDupeOf)]['component'],
                bugzillaData['bugs'][str(rowDupeOf)]['op_sys'],
                bugzillaData['bugs'][str(rowDupeOf)]['version'],
                bugzillaData['bugs'][str(rowDupeOf)]['keywords'],
                datetime.datetime.strptime(
                    bugzillaData['bugs'][str(rowDupeOf)]['creation_time'], "%Y-%m-%dT%H:%M:%SZ"), 1)

            for action in row['history']:
                actionMail = action['who']
                actionDate = datetime.datetime.strptime(action['when'], "%Y-%m-%dT%H:%M:%SZ")

                # Use this variable in case the status is set before the resolution
                newStatus = None
                for change in action['changes']:
                    if change['field_name'] == 'blocks':
                        if change['added']:
                            for metabug in change['added'].split(', '):
                                continue
                                #TODO
                                #util_increase_user_actions(statList, key, actionMail, bugTargets, 'metabug_added', actionDate)

                        if change['removed']:
                            for metabug in change['removed'].split(', '):
                                continue
                                #TODO
                                #util_increase_user_actions(statList, key, actionMail, bugTargets, 'metabug_added', actionDate)

                    if change['field_name'] == 'status':
                        addedStatus = change['added']
                        removedStatus = change['removed']

                        if  addedStatus == 'RESOLVED' or addedStatus == 'VERIFIED':
                            if(rowResolution):
                                addedStatus = addedStatus + "_" + rowResolution
                                util_increase_user_actions(statList, key, actionMail, bugTargets, 'status_changed', actionDate)
                            else:
                                newStatus = addedStatus
                        else:
                            util_increase_user_actions(statList, key, actionMail, bugTargets, 'status_changed', actionDate)

                    elif change['field_name'] == 'resolution':
                        if newStatus:
                            addedStatus = newStatus + "_" + change['added']
                            util_increase_user_actions(statList, key, actionMail, bugTargets, 'status_changed', actionDate)

                            newStatus = None

                    elif change['field_name'] == 'priority':
                        util_increase_user_actions(statList, key, actionMail, bugTargets, 'priority_changed', actionDate)

                    elif change['field_name'] == 'severity':
                        util_increase_user_actions(statList, key, actionMail, bugTargets, 'severity_changed', actionDate)

                    elif change['field_name'] == 'keywords':
                        keywordsAdded = change['added'].split(", ")
                        for keyword in keywordsAdded:
                            if keyword in common.keywords_list:
                                util_increase_user_actions(statList, key, actionMail, bugTargets, 'keyword_added', actionDate)

                        keywordsRemoved = change['removed'].split(", ")
                        for keyword in keywordsRemoved:
                            if keyword in common.keywords_list:
                                util_increase_user_actions(statList, key, actionMail, bugTargets, 'keyword_removed', actionDate)

                    elif change['field_name'] == 'op_sys':
                        newSystem = change['added']
                        util_increase_user_actions(statList, rowId, actionMail, bugTargets, 'system_changed', actionDate)

            comments = row['comments'][1:]
            for idx, comment in enumerate(comments):
                commentMail = comment['creator']
                commentDate = datetime.datetime.strptime(comment['time'], "%Y-%m-%dT%H:%M:%SZ")

                util_increase_user_actions(statList, rowId, commentMail, bugTargets, 'comments', commentDate)

            #this way we can get the users' name
            for person in row['cc_detail']:
                common.util_check_bugzilla_mail(statList, person['email'], person['real_name'])

    statList['stat']['newest'] = statNewDate.strftime("%Y-%m-%d")
    statList['stat']['oldest'] = statOldDate.strftime("%Y-%m-%d")
    print(" from " + statList['stat']['oldest'] + " to " + statList['stat']['newest'])

def create_wikimedia_table_for_cc_and_duplicates(cfg, statList):

    for nameList in statList['duplicates']:
        for k, v in statList['dupesBugs'].items():
            if k in statList['duplicates'][nameList]:
                if len(v) >= minNumOfDupes:
                    statList['duplicates'][nameList][k]['count'] = len(v)
                else:
                    del statList['duplicates'][nameList][k]

    for typeList in ['duplicates','CC']:
        for nameList in statList[typeList]:
            fileName = typeList + '_' + nameList
            print('Creating wikimedia table for ' + fileName)
            output = ""

            output += '{{TopMenu}}\n'
            output += '{{Menu}}\n'
            output += '{{Menu.QA}}\n'
            output += '\n'
            table = []

            if nameList == 'regressions':
                headers = ['Id', 'Summary', 'Component', 'OS', 'Version', 'Bisected', 'Reported']
            elif nameList == 'enhancements':
                headers = ['Id', 'Summary', 'Component', 'OS', 'Version', 'Reported']
            else:
                headers = ['Id', 'Summary', 'Component', 'OS', 'Version', 'EasyHack', 'Reported']

            if typeList == 'CC':
                headers.append('Total CC')
                output += '{} {} have 10 or more people in the CC list. (sorted in alphabetical order by number of users)\n'.format(
                        len(statList['CC'][nameList]), nameList)
            else:
                headers.append('Total Duplicates')
                output += '{} open {} have 3 or more duplicates. (sorted in alphabetical order by number of duplicates)\n'.format(
                        len(statList['duplicates'][nameList]), nameList)

            for k,v in statList[typeList][nameList].items():
                row = []
                row.append('[' + common.urlShowBug + str(k) + ' #tdf' + str(k) + ']')
                row.append(v['summary'])
                row.append(v['component'])
                row.append(v['os'])
                row.append(v['version'])

                if nameList == 'regressions':
                    if 'bibisectNotNeeded' in v['keywords']:
                        row.append('Not Needed')
                    elif 'bisected' in v['keywords']:
                        row.append('True')
                    else:
                        row.append('False')

                if nameList == 'bugs':
                    if 'easyHack' in v['keywords']:
                        row.append('True')
                    else:
                        row.append('False')

                row.append(v['creationDate'].strftime("%Y-%m-%d %H:%M:%S"))
                row.append(v['count'])
                table.append(row)

            output += tabulate(sorted(table, key = lambda x: x[len(headers) - 1], reverse=True), headers, tablefmt='mediawiki')
            output += "\n"
            output +='Generated on {}.'.format(cfg['todayDate'])
            output += "\n"
            output += '[[Category:EN]]\n'
            output += '[[Category:QA/Stats]]'

            fp = open('/tmp/table_' + fileName + '.txt', 'w', encoding='utf-8')
            print(output.replace('wikitable', 'wikitable sortable'), file=fp)
            fp.close()

def create_wikimedia_table_by_target(cfg, statList):
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
            name = ''
            if vP['email'] in statList['people']:
                name = statList['people'][kP]['name']
            if not name:
                name = vP['email'].split('@')[0]

            row = []
            row.append(name)
            row.append(vP['created'])
            row.append(vP['comments'])
            row.append(vP['status_changed'])
            row.append(vP['keyword_added'])
            row.append(vP['keyword_removed'])
            row.append(vP['severity_changed'])
            row.append(vP['priority_changed'])
            row.append(vP['system_changed'])
            row.append(len(set(vP['bugs'])))
            table.append(row)

        output += tabulate(sorted(table, key = lambda x: x[0]), headers, tablefmt='mediawiki')
        output += "\n"
        output +='Generated on {}.'.format(cfg['todayDate'])
        output += "\n"
        output += '[[Category:EN]]\n'
        output += '[[Category:QA/Stats]]'

        fp = open('/tmp/table_' + kT + '.txt', 'w', encoding='utf-8')
        print(output.replace('wikitable', 'wikitable sortable'), file=fp)
        fp.close()

def create_wikimedia_table_by_period(cfg, statList):
    for kT,vT in sorted(statList['period'].items()):
        print('Creating wikimedia table for actions done in the last {} days.'.format(kT))
        output = ""

        output += '{{TopMenu}}\n'
        output += '{{Menu}}\n'
        output += '{{Menu.QA}}\n'
        output += '\n'

        output += '{} people helped to triage {} bugs in the last {} days. (sorted in alphabetical order by user\'s name)\n'.format(
            len(vT['people']), vT['count'], kT)
        output += '\n'
        table = []
        headers = ['Name', 'Created', 'Comments', 'Status Changed', 'Keyword Added', 'Keyword Removed',
                   'Severity Changed', 'Priority Changed', 'System Changed', 'Total Bugs']

        for kP, vP in vT['people'].items():
            name = ''
            if vP['email'] in statList['people']:
                name = statList['people'][kP]['name']
            if not name:
                name = vP['email'].split('@')[0]

            row = []
            row.append(name)
            row.append(vP['created'])
            row.append(vP['comments'])
            row.append(vP['status_changed'])
            row.append(vP['keyword_added'])
            row.append(vP['keyword_removed'])
            row.append(vP['severity_changed'])
            row.append(vP['priority_changed'])
            row.append(vP['system_changed'])
            row.append(len(set(vP['bugs'])))
            table.append(row)

        output += tabulate(sorted(table, key = lambda x: x[0]), headers, tablefmt='mediawiki')
        output += "\n"
        output += 'Generated on {}.'.format(cfg['todayDate'])
        output += "\n"
        output += '[[Category:EN]]\n'
        output += '[[Category:QA/Stats]]'

        fp = open('/tmp/period_' + str(kT) + '.txt', 'w', encoding='utf-8')
        print(output.replace('wikitable', 'wikitable sortable'), file=fp)
        fp.close()

def runCfg():
    cfg = {}
    cfg['todayDate'] = datetime.datetime.now().replace(hour=0, minute=0,second=0)

    for period in periods_list:
        cfg[period] = common.util_convert_days_to_datetime(period)

    return cfg

if __name__ == '__main__':
    print("Reading and writing data to " + common.dataDir)

    cfg = runCfg()

    bugzillaData = common.get_bugzilla()

    statList = util_create_wiki_statList()

    analyze_bugzilla_wiki_stats(statList, bugzillaData, cfg)

    create_wikimedia_table_by_target(cfg, statList)
    create_wikimedia_table_by_period(cfg, statList)
    create_wikimedia_table_for_cc_and_duplicates(cfg, statList)

    print('End of report')
