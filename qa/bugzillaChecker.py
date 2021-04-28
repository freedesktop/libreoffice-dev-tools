#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

import common
import sys
import datetime
import re
import ast

bugzillaReportPath = '/tmp/bugzilla_report.txt'
bugzillaUserReportPath = '/tmp/bugzilla_users_report.txt'
if datetime.date.today().weekday() == 0:
    # Weekends
    reportPeriodDays = 3
else:
    reportPeriodDays = 1

newUserPeriodDays = 30
newUserBugs = 3

memberPeriodDays = 365
memberBugs = 50

oldUserPeriodDays = 180
oldUserBugs = 30

# bugs which last comment is from the Commit Notification
pingFixedBugPeriodDays = 30

# Unconfirmed bugs which last comment is not written by the reporter
# or not comments at all
retestUnconfirmedPeriodDays = 30

# Unconfirmed bugs which last comment is written by the reporter
inactiveUnconfirmedPeriodDays = 180

# Assigned bugs without activity
inactiveAssignedPeriodDays = 90

# tuple of versions to check whether the version has been changed at confirmation time
versionsToCheck = ('5', '6')

crashReportDomain = "https://crashreport.libreoffice.org/stats/signature/"

minNumOfDupes = 5
minNumOfCC = 20

def util_create_statList_checkers():
    return {
        'people': {}
        }

def util_add_to_result(lResults, key, value):
    if  key not in lResults:
        lResults[key] = []
    lResults[key].append(value)


def analyze_bugzilla_checkers(statList, bugzillaData, cfg):
    print("Analyzing bugzilla chekers\n", end="", flush=True)

    lResults = {}
    dupesBugs = {}

    for key, row in bugzillaData['bugs'].items():
        rowId = row['id']

        #Ignore META bugs and deletionrequest bugs.
        if not row['summary'].lower().startswith('[meta]') and row['component'].lower() != 'deletionrequest':
            creationDate = datetime.datetime.strptime(row['creation_time'], "%Y-%m-%dT%H:%M:%SZ")

            rowStatus = row['status']
            rowResolution = row['resolution']

            if rowStatus == 'VERIFIED' or rowStatus == 'RESOLVED':
                rowStatus += "_" + rowResolution

            rowKeywords = row['keywords']

            creatorMail = row['creator']

            rowVersion = row['version']

            common.util_check_bugzilla_mail(statList, creatorMail, row['creator_detail']['real_name'], creationDate, rowId)

            if common.isOpen(rowStatus) and rowId not in dupesBugs:
                dupesBugs[rowId] = { 'totalDupes': 0, 'totalCC': len(row['cc']), 'priority': row['priority'], 'severity': row['severity'],
                        'isRegression': 'regression' in rowKeywords }

            rowDupeOf = common.util_check_duplicated(bugzillaData, rowId)
            if rowDupeOf and common.isOpen(bugzillaData['bugs'][str(rowDupeOf)]['status']):
                if rowDupeOf not in dupesBugs:
                    dupesBugs[rowDupeOf] = { 'totalDupes': 0, 'totalCC': len(bugzillaData['bugs'][str(rowDupeOf)]['cc']),
                            'priority': bugzillaData['bugs'][str(rowDupeOf)]['priority'],
                            'severity': bugzillaData['bugs'][str(rowDupeOf)]['severity'],
                            'isRegression': 'regression' in bugzillaData['bugs'][str(rowDupeOf)]['keywords'] }
                dupesBugs[rowDupeOf]['totalDupes'] += 1

            crashSignature = row['cf_crashreport']
            if crashSignature:
                if not crashSignature.startswith('["'):
                    util_add_to_result(lResults, 'incorrect_crash_signature', rowId)
                else:
                    if common.isOpen(rowStatus):
                        lcrashSignature = ast.literal_eval(crashSignature)
                        for i in lcrashSignature:
                            crashReportUrl = crashReportDomain + str(i).replace(' ', '%20').replace('`', '%60')
                            crashReportUrl = crashReportUrl.replace('<', '%3C').replace('>', '%3E')
                            #Link should be shorter than 255, otherwise Bugzilla returns an error
                            if crashReportUrl not in row['see_also'] and len(crashReportUrl) < 255:
                                util_add_to_result(lResults, 'add_crashReport_to_seeAlso', rowId)

            everConfirmed = False
            autoConfirmed = False
            versionChanged = False
            oldestVersion = 999999
            newerVersion = False
            autoFixed = False
            closeDate = None
            movedToFixed = False
            movedToNeedInfo = False
            isReopened = False
            addAssigned = False
            movedToNew = False
            addAssigned = False
            actionMail = None

            for action in row['history']:
                actionMail = action['who']
                actionDate = datetime.datetime.strptime(action['when'], "%Y-%m-%dT%H:%M:%SZ")
                common.util_check_bugzilla_mail(statList, actionMail, '', actionDate, rowId)

                # Use this variable in case the status is set before the resolution
                newStatus = None
                for change in action['changes']:

                    if change['field_name'] == 'version':
                        versionChanged = True
                        if actionDate >= cfg['reportPeriod'] and (common.isOpen(rowStatus) or rowStatus == 'UNCONFIRMED'):
                            addedVersion = change['added']
                            removedVersion = change['removed']
                            if addedVersion == 'unspecified':
                                addedVersion = 999999
                            elif addedVersion == 'Inherited From OOo':
                                addedVersion = 0
                            else:
                                addedVersion = int(''.join([s for s in re.split('\.|\s',addedVersion) if s.isdigit()]).ljust(3, '0')[:2] )

                            if removedVersion == 'unspecified':
                                removedVersion = 999999
                            elif removedVersion == 'Inherited From OOo':
                                removedVersion = 0
                            else:
                                removedVersion = int(''.join([s for s in re.split('\.|\s',removedVersion) if s.isdigit()]).ljust(3, '0')[:2] )

                            if removedVersion < oldestVersion:
                                oldestVersion = removedVersion

                            if addedVersion <= oldestVersion:
                                oldestVersion = addedVersion
                                newerVersion = False
                            else:
                                newerVersion = True

                    elif change['field_name'] == 'status':
                        addedStatus = change['added']
                        removedStatus = change['removed']

                        if addedStatus == 'REOPENED' and rowStatus == 'REOPENED' and not movedToFixed:
                            isReopened = True

                        if actionDate >= cfg['reportPeriod'] and addedStatus == 'NEEDINFO' and \
                                rowStatus == 'NEEDINFO' and common.isOpen(removedStatus):
                            movedToNeedInfo = True

                        if movedToNeedInfo and removedStatus == 'NEEDINFO':
                            movedToNeedInfo = False

                        if  addedStatus == 'RESOLVED' or addedStatus == 'VERIFIED':
                            if(rowResolution):
                                addedStatus = addedStatus + "_" + rowResolution
                            else:
                                newStatus = addedStatus

                        #if any other user moves it to open ( ASSIGNED, NEW or REOPENED ),
                        #the bug is no longer autoconfirmed
                        if not everConfirmed and common.isOpen(addedStatus) and actionMail != creatorMail:
                            everConfirmed = True
                            autoConfirmed = False

                        #Check for autoconfirmed bugs:
                        #Bug's status is open ( ASSIGNED, NEW or REOPENED ), moved to open by the reporter
                        #from non-open status and never confirmed by someone else.
                        #Ignore bisected bugs or some trusted authors defined in configQA.json
                        if actionDate >= cfg['reportPeriod'] and not everConfirmed and actionMail == creatorMail and \
                            common.isOpen(rowStatus) and common.isOpen(addedStatus) and 'bisected' not in rowKeywords and \
                            creatorMail not in cfg['configQA']['ignore']['autoConfirmed']:
                                autoConfirmed = True

                        if autoFixed and removedStatus == 'RESOLVED':
                            autoFixed = False

                        if actionDate >= cfg['reportPeriod']:
                            if actionMail == creatorMail and addedStatus == 'RESOLVED_FIXED' and \
                                    rowStatus == 'RESOLVED_FIXED' and 'target:' not in row['whiteboard']:
                                autoFixed = True

                            if removedStatus == "ASSIGNED" and addedStatus == "NEW" and \
                                    rowStatus == "NEW" and row['assigned_to'] != 'libreoffice-bugs@lists.freedesktop.org':
                                util_add_to_result(lResults, 'remove_assignee', rowId)
                            elif addedStatus == "ASSIGNED" and rowStatus == "ASSIGNED" and \
                                    row['assigned_to'] == 'libreoffice-bugs@lists.freedesktop.org':
                                util_add_to_result(lResults, 'add_assignee', rowId)

                            if addedStatus == 'NEW' and rowStatus == 'NEW' and row['product'] == 'LibreOffice':
                                movedToNew = True

                            if addedStatus == 'RESOLVED_FIXED' and rowStatus == 'RESOLVED_FIXED' and ('regression' in rowKeywords \
                                    or 'crash' in row['summary'].lower() or 'perf' in rowKeywords):
                                util_add_to_result(lResults, 'verify_fix', rowId)

                    elif change['field_name'] == 'resolution':
                        if newStatus:
                            addedStatus = newStatus + "_" + change['added']
                            newStatus = None

                        if change['added'] == 'FIXED':
                            movedToFixed = True
                            isReopened = False
                            if common.isOpen(rowStatus):
                                closeDate = actionDate
                        elif change['removed'] == 'FIXED' and actionDate >= cfg['reportPeriod'] and \
                                closeDate and (actionDate - closeDate).days > 30:
                            util_add_to_result(lResults, 'reopened_after_1_months', rowId)

                    elif change['field_name'] == 'keywords':
                        if actionDate >= cfg['reportPeriod']:
                            keywordsAdded = change['added'].split(", ")
                            for keyword in keywordsAdded:
                                if keyword in common.keywords_list and keyword in rowKeywords:
                                        if keyword == 'patch' and (common.isOpen(rowStatus) or rowStatus == 'UNCONFIRMED'):
                                            util_add_to_result(lResults, 'patch_added', rowId)

                                        if row['status'] != 'RESOLVED':
                                            if keyword == 'bibisectRequest' and 'regression' not in rowKeywords:
                                                util_add_to_result(lResults, 'bibisectRequest_added', rowId)

                                            elif keyword == 'possibleRegression' and 'possibleRegression' in rowKeywords:
                                                util_add_to_result(lResults, 'possibleregression_added', rowId)
                                            elif keyword == 'needsUXEval' and 'libreoffice-ux-advise@lists.freedesktop.org' not in row['cc']:
                                                util_add_to_result(lResults, 'needsUXEval_missing_email', rowId)

                    elif change['field_name'] == 'whiteboard':
                        if actionDate >= cfg['reportPeriod']:
                            for whiteboard in change['added'].split(' '):
                                if 'backportrequest' in whiteboard.lower() and \
                                        whiteboard in row['whiteboard'] and common.isOpen(rowStatus):
                                    util_add_to_result(lResults, 'backport_added', rowId)


                    elif change['field_name'] == 'assigned_to':
                        if actionDate >= cfg['reportPeriod']:
                            removedAssignee = change['removed']
                            addedAssignee = change['added']
                            if  removedAssignee == "libreoffice-bugs@lists.freedesktop.org" and \
                                    row['assigned_to'] != 'libreoffice-bugs@lists.freedesktop.org' and \
                                    ( rowStatus == 'NEW' or rowStatus == 'UNCONFIRMED'):
                                addAssigned = True
                                util_add_to_result(lResults, 'change_status_assigned', rowId)
                            if addedAssignee == "libreoffice-bugs@lists.freedesktop.org" and \
                                    row['assigned_to'] == 'libreoffice-bugs@lists.freedesktop.org' and rowStatus == 'ASSIGNED':
                                util_add_to_result(lResults, 'remove_assigned_status', rowId)

            commentMail = None
            comments = row['comments'][1:]
            for idx, comment in enumerate(comments):
                commentMail = comment['creator']
                commentDate = datetime.datetime.strptime(comment['time'], "%Y-%m-%dT%H:%M:%SZ")

                common.util_check_bugzilla_mail(statList, commentMail, '', commentDate, rowId)

            if len(comments) > 0:
                if rowStatus == 'UNCONFIRMED' and 'needsDevAdvice' not in rowKeywords and row['severity'] != 'enhancement':
                    if comments[-1]['creator'] != creatorMail and '[Automated Action]' not in comments[-1]['text'] and \
                        datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ") < cfg['retestUnconfirmedPeriod']:
                        util_add_to_result(lResults, 'unconfirmed_last_comment_not_from_reporter', rowId)
                    elif comments[-1]['creator'] == creatorMail and \
                        datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ") < cfg['inactiveUnconfirmedPeriod']:
                        util_add_to_result(lResults, 'unconfirmed_last_comment_from_reporter', rowId)

            if rowStatus == 'UNCONFIRMED' and row['severity'] == 'enhancement' and 'QA:needsComment' not in row['whiteboard'] and \
                    datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ") < cfg['retestUnconfirmedPeriod']:
                util_add_to_result(lResults, 'inactive_unconfirmed_enhacements', rowId)

            if autoFixed:
                util_add_to_result(lResults, 'auto_fixed', rowId)

            if autoConfirmed:
                util_add_to_result(lResults, 'auto_confirmed', rowId)

            if newerVersion and rowVersion != 'unspecified':
                util_add_to_result(lResults, 'newer_version', rowId)

            if isReopened and not autoConfirmed:
                util_add_to_result(lResults, 'is_reopened', rowId)

            #In case the reporter assigned the bug to himself at creation time
            if not addAssigned and creationDate >= cfg['reportPeriod'] and \
                    row['assigned_to'] != 'libreoffice-bugs@lists.freedesktop.org' and (rowStatus == 'NEW' or rowStatus == 'UNCONFIRMED'):
                util_add_to_result(lResults, 'change_status_assigned', rowId)

            if movedToNeedInfo and everConfirmed:
                util_add_to_result(lResults, 'moved_to_needinfo', rowId)

            if not versionChanged and movedToNew and not autoConfirmed and row['severity'] != 'enhancement' and \
                    'regression' not in rowKeywords and 'bisected' not in rowKeywords and \
                    'easyHack' not in rowKeywords and 'needsUXEval' not in rowKeywords and \
                    row['component'] != 'Documentation' and \
                    row['component'] != 'UI' and \
                    row['component'] != 'iOS' and row['component'] != 'Android Viewer' and \
                    actionMail not in cfg['configQA']['ignore']['confirmer'] and \
                    (rowVersion.startswith(versionsToCheck) or rowVersion == 'unspecified'):
                util_add_to_result(lResults, 'version_not_changed', rowId)


            if common.isOpen(rowStatus) and 'target:' in row['whiteboard'] and 'easyHack' not in row['keywords']:

                it = 1
                #Check the last 3 comments
                totalComments = 3
                while it <= totalComments:
                    negIt = it * -1
                    if len(comments) >= it:
                        commentMail = comments[negIt]['creator']
                        commentText = comments[negIt]['text']
                        commentDate = datetime.datetime.strptime(comments[negIt]['time'], "%Y-%m-%dT%H:%M:%SZ")
                        if commentDate < cfg['PingFixedBugPeriod'] and commentDate >= cfg['pingFixedBugDiff']:
                            if it == 1 and  'Is this bug fixed?' in commentText and commentMail == 'xiscofauli@libreoffice.org':
                                util_add_to_result(lResults, 'take_action_fixed_bug', rowId)
                                break

                            elif commentMail == 'libreoffice-commits@lists.freedesktop.org':
                                # Check the commit hasn't been reverted
                                if 'evert' in commentText:
                                    break
                                else:
                                    util_add_to_result(lResults, 'ping_bug_fixed', rowId)
                                    break

                            # Ignore duplicated comments
                            elif 'has been marked as a duplicate of this bug' in commentText:
                                totalComments += 1
                            it += 1
                        else:
                            break
                    else:
                        break

            if rowStatus == 'ASSIGNED' and \
                    datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ") < cfg['inactiveAssignedPeriod'] and \
                    rowId not in cfg['configQA']['ignore']['inactiveAssigned']:
                util_add_to_result(lResults, 'inactive_assignee', rowId)

        elif row['summary'].lower().startswith('[meta]'):
            if not row['alias'] and common.isOpen(row['status']):
                util_add_to_result(lResults, 'empty_alias', rowId)

    for k, v in dupesBugs.items():
        if v['severity'] == 'enhancement':
            if v['totalDupes'] < minNumOfDupes and v['totalCC'] < minNumOfCC and (v['priority'] == 'high' or v['priority'] == 'highest'):
                util_add_to_result(lResults, 'change_enhancement_priority_to_medium', k)
            elif (v['totalDupes'] >= minNumOfDupes or v['totalCC'] >= minNumOfCC) and (v['priority'] != 'high' and v['priority'] != 'highest'):
                util_add_to_result(lResults, 'change_enhancement_priority_to_high', k)
        else:
            if v['totalDupes'] >= minNumOfDupes or v['totalCC'] >= minNumOfCC:
                if v['isRegression'] and v['priority'] != 'highest':
                    util_add_to_result(lResults, 'change_bug_priority_to_highest', k)
                elif (v['priority'] != 'high' and v['priority'] != 'highest'):
                    util_add_to_result(lResults, 'change_bug_priority_to_high', k)

    fp = open(bugzillaReportPath, 'w', encoding='utf-8')
    print("Creating file " + bugzillaReportPath)

    for dKey, dValue in sorted(lResults.items()):
        if dValue:
            print('\n=== ' + dKey.replace('_', ' ').upper() + ' ( ' + str(len(dValue)) +  ' ) ===', file=fp)

            sortedValues = sorted([str(item) for item in dValue])
            if len(sortedValues) == 1:
                print('\t1. ' + common.urlShowBug + sortedValues[0] , file=fp)
            else:
                count = 1
                for i in range(0, len(sortedValues), 20):
                    subList = sortedValues[i:i + 20]
                    url = "https://bugs.documentfoundation.org/buglist.cgi?bug_id=" + ','.join(subList)
                    print('\t' + str(count) + '. ' + url , file=fp)
                    count += 1

    fp.close()

    fp = open(bugzillaUserReportPath, 'w', encoding='utf-8')
    print("Creating file " + bugzillaUserReportPath)
    for k, v in statList['people'].items():
        if not statList['people'][k]['name']:
            statList['people'][k]['name'] = statList['people'][k]['email'].split('@')[0]

        if statList['people'][k]['oldest'] >= cfg['newUserPeriod'] and len(statList['people'][k]['bugs']) >= newUserBugs and \
                statList['people'][k]['email'] not in cfg['configQA']['ignore']['newContributors']:
            print('\n=== New contributor: '+ statList['people'][k]['name'] + " ("  + statList['people'][k]['email'] + ") ===", file=fp)
            lBugs = list(statList['people'][k]['bugs'])
            for idx in range(len(lBugs)):
                isEasyHack = False
                if 'easyHack' in bugzillaData['bugs'][str(lBugs[idx])]['keywords']:
                        isEasyHack = True
                print("{:<3} | {:<58} | {}".format(
                    str(idx + 1), common.urlShowBug + str(lBugs[idx]), 'easyHack: ' + str(isEasyHack)), file=fp)
            cfg['configQA']['ignore']['newContributors'].append(statList['people'][k]['email'])

        if statList['people'][k]['oldest'] >= cfg['memberPeriod'] and \
                len(statList['people'][k]['bugs']) >= memberBugs and statList['people'][k]['email'] not in cfg['configQA']['ignore']['members']:
            print('\n=== New MEMBER: ' + statList['people'][k]['name'] + " ("  + statList['people'][k]['email'] + ") ===", file=fp)
            print('\tOldest: ' + statList['people'][k]['oldest'].strftime("%Y-%m-%d"), file=fp)
            print('\tNewest: ' + statList['people'][k]['newest'].strftime("%Y-%m-%d"), file=fp)
            print('\tTotal: ' + str(len(statList['people'][k]['bugs'])), file=fp)
            cfg['configQA']['ignore']['members'].append(statList['people'][k]['email'])

        if statList['people'][k]['newest'] < cfg['oldUserPeriod'] and statList['people'][k]['newest'] >= cfg['oldUserPeriod2'] and \
                len(statList['people'][k]['bugs']) >= oldUserBugs and statList['people'][k]['email'] not in cfg['configQA']['ignore']['oldContributors']:
            print('\n=== Old Contributor: ' + statList['people'][k]['name'] + " ("  + statList['people'][k]['email'] + ") ===", file=fp)
            print('\tOldest: ' + statList['people'][k]['oldest'].strftime("%Y-%m-%d"), file=fp)
            print('\tNewest: ' + statList['people'][k]['newest'].strftime("%Y-%m-%d"), file=fp)
            print('\tTotal: ' + str(len(statList['people'][k]['bugs'])), file=fp)
            cfg['configQA']['ignore']['oldContributors'].append(statList['people'][k]['email'])

        statList['people'][k]['oldest'] = statList['people'][k]['oldest'].strftime("%Y-%m-%d")
        statList['people'][k]['newest'] = statList['people'][k]['newest'].strftime("%Y-%m-%d")

    fp.close()
    dumpResult = {}
    dumpResult['configQA'] = cfg['configQA']
    common.util_dump_config(dumpResult)

def runCfg():
    cfg = common.get_config()
    cfg['reportPeriod'] = common.util_convert_days_to_datetime(reportPeriodDays)
    cfg['newUserPeriod'] = common.util_convert_days_to_datetime(newUserPeriodDays)
    cfg['oldUserPeriod'] = common.util_convert_days_to_datetime(oldUserPeriodDays)
    cfg['oldUserPeriod2'] = common.util_convert_days_to_datetime(oldUserPeriodDays + reportPeriodDays)
    cfg['memberPeriod'] = common.util_convert_days_to_datetime(memberPeriodDays)
    cfg['PingFixedBugPeriod'] = common.util_convert_days_to_datetime(pingFixedBugPeriodDays)
    cfg['pingFixedBugDiff'] = common.util_convert_days_to_datetime(pingFixedBugPeriodDays + reportPeriodDays)
    cfg['retestUnconfirmedPeriod'] = common.util_convert_days_to_datetime(retestUnconfirmedPeriodDays)
    cfg['inactiveUnconfirmedPeriod'] = common.util_convert_days_to_datetime(inactiveUnconfirmedPeriodDays)
    cfg['inactiveAssignedPeriod'] = common.util_convert_days_to_datetime(inactiveAssignedPeriodDays)
    return cfg

if __name__ == '__main__':
    print("Reading and writing data to " + common.dataDir)

    if len(sys.argv) > 1:
        try:
            reportPeriodDays = int(sys.argv[1])
        except ValueError:
            print("The argument is not an int. Ignoring it...")

    cfg = runCfg()

    bugzillaData = common.get_bugzilla()

    statList = util_create_statList_checkers()

    analyze_bugzilla_checkers(statList, bugzillaData, cfg)
