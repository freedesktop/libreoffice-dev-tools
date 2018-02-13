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
from tabulate import tabulate

targets_list = ['5.4.5', '6.0.1']

periods_list = [30, 60, 90, 180, 365]

minNumOfDupes = 3

def util_create_wiki_statList():
    return {
        'targets': {t:{'count':0, 'people':{}} for t in targets_list},
        'period': {p:{'count':0, 'people':{}} for p in periods_list},
        'MostCCBugs': {},
        'dupesBugs': {},
        'MostDupeBugs': {},
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

def util_check_duplicated(bugID, isFirst=True):
    rowDupeOf = bugzillaData['bugs'][str(bugID)]['dupe_of']
    if rowDupeOf:
        if str(rowDupeOf) in bugzillaData['bugs']:
            return util_check_duplicated(rowDupeOf, False)
        else:
            return bugID
    else:
        if isFirst:
            return None
        else:
            return bugID

def util_create_bug(summary, component, version, keywords, creationDate, count_cc):
    return { 'summary': summary,
             'component': component,
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
                statList['MostCCBugs'][rowId] = util_create_bug(
                        row['summary'], row['component'], row['version'], rowKeywords, creationDate, len(row['cc']))

            rowDupeOf = util_check_duplicated(rowId)
            if rowDupeOf:
                if rowDupeOf not in statList['dupesBugs']:
                    statList['dupesBugs'][rowDupeOf] = []
                statList['dupesBugs'][rowDupeOf].append(rowId)

                if str(rowDupeOf) in bugzillaData['bugs'] and \
                        common.isOpen(bugzillaData['bugs'][str(rowDupeOf)]['status']):
                    if rowDupeOf not in statList['MostDupeBugs']:
                        statList['MostDupeBugs'][rowDupeOf] = util_create_bug(
                        bugzillaData['bugs'][str(rowDupeOf)]['summary'],
                        bugzillaData['bugs'][str(rowDupeOf)]['component'],
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
                if person['email'] not in statList['people']:
                    statList['people'][person['email']] = person['real_name']

    statList['stat']['newest'] = statNewDate.strftime("%Y-%m-%d")
    statList['stat']['oldest'] = statOldDate.strftime("%Y-%m-%d")
    print(" from " + statList['stat']['oldest'] + " to " + statList['stat']['newest'])

def create_wikimedia_table_mostCCBugs_and_MostDupes(cfg, statList):

    for k, v in statList['dupesBugs'].items():
        if k in statList['MostDupeBugs']:
            if len(v) >= minNumOfDupes:
                statList['MostDupeBugs'][k]['count'] = len(v)
            else:
                del statList['MostDupeBugs'][k]

    for nameList in ['MostCCBugs', 'MostDupeBugs']:
        print('Creating wikimedia table for ' + nameList)
        output = ""

        output += '{{TopMenu}}\n'
        output += '{{Menu}}\n'
        output += '{{Menu.QA}}\n'
        output += '\n'
        table = []
        headers = ['Id', 'Summary', 'Component', 'Version', 'isRegression', 'isBisected',
                           'isEasyHack', 'haveBackTrace', 'Reported']
        if nameList == 'MostCCBugs':
            headers.append('Total CC')
            output += '{} bugs have 10 or more emails in the CC list. (sorted in alphabetical order by number of users)\n'.format(
                    len(statList['MostCCBugs']))
        else:
            headers.append('Total Duplicates')
            output += '{} open bugs have 3 or more duplicates. (sorted in alphabetical order by number of duplicates)\n'.format(
                    len(statList['MostDupeBugs']))

        for k,v in statList[nameList].items():
            row = []
            row.append('[' + common.urlShowBug + str(k) + ' #tdf' + str(k) + ']')
            row.append(v['summary'])
            row.append(v['component'])
            row.append(v['version'])
            if 'regression' in v['keywords']:
                row.append('True')
            else:
                row.append('False')
            if 'bisected' in v['keywords']:
                row.append('True')
            else:
                row.append('False')
            if 'easyHack' in v['keywords']:
                row.append('True')
            else:
                row.append('False')
            if 'haveBacktrace' in v['keywords']:
                row.append('True')
            else:
                row.append('False')
            row.append(v['creationDate'].strftime("%Y-%m-%d %H:%M:%S"))
            row.append(v['count'])
            table.append(row)

        output += tabulate(sorted(table, key = lambda x: x[9], reverse=True), headers, tablefmt='mediawiki')
        output += "\n"
        output +='Generated on {}.'.format(cfg['todayDate'])
        output += "\n"
        output += '[[Category:EN]]\n'
        output += '[[Category:QA/Stats]]'

        fp = open('/tmp/table_' + nameList + '.txt', 'w', encoding='utf-8')
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
                name = statList['people'][kP]
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
                name = statList['people'][kP]
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
        cfg[period] = common.util_convert_days_to_datetime(cfg, period)

    return cfg

if __name__ == '__main__':
    print("Reading and writing data to " + common.dataDir)

    cfg = runCfg()

    bugzillaData = common.get_bugzilla()

    statList = util_create_wiki_statList()

    analyze_bugzilla_wiki_stats(statList, bugzillaData, cfg)

    create_wikimedia_table_by_target(cfg, statList)
    create_wikimedia_table_by_period(cfg, statList)
    create_wikimedia_table_mostCCBugs_and_MostDupes(cfg, statList)

    print('End of report')
