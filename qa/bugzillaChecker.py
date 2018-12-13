#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import common
import sys
import datetime
import re
import colorama
from colorama import Back
import ast

#Use this variable to hightlight the most recent bugs
coloredPeriodDays = 1

reportPeriodDays = 7

newUserPeriodDays = 30
newUserBugs = 3

memberPeriodDays = 365
memberBugs = 50

oldUserPeriodDays = 180
oldUserBugs = 20

# bugs which last comment is from the Commit Notification
pingFixedBugPeriodDays = 30

# Unconfirmed bugs which last comment is not written by the reporter
# or not comments at all
retestUnconfirmedPeriodDays = 30

# Unconfirmed bugs which last comment is written by the reporter
inactiveUnconfirmedPeriodDays = 180

# Needinfo bugs which last comment is written by the reporter
retestNeedinfoPeriodDays = 60

# Assigned bugs without activity
inactiveAssignedPeriodDays = 90

# tuple of versions to check whether the version has been changed at confirmation time
versionsToCheck = ('5', '6')

crashReportDomain = "https://crashreport.libreoffice.org/stats/signature/"

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

    for key, row in bugzillaData['bugs'].items():
        rowId = row['id']

        #Ignore META bugs and deletionrequest bugs.
        if not row['summary'].lower().startswith('[meta]') and row['component'] != 'deletionrequest':
            creationDate = datetime.datetime.strptime(row['creation_time'], "%Y-%m-%dT%H:%M:%SZ")

            rowStatus = row['status']
            rowResolution = row['resolution']

            if rowStatus == 'VERIFIED' or rowStatus == 'RESOLVED':
                rowStatus += "_" + rowResolution

            rowKeywords = row['keywords']

            creatorMail = row['creator']

            rowVersion = row['version']

            common.util_check_bugzilla_mail(statList, creatorMail, row['creator_detail']['real_name'], creationDate, rowId)

            crashSignature = row['cf_crashreport']
            if crashSignature:
                resultValue = [ rowId, creationDate, '']
                if not crashSignature.startswith('["'):
                    util_add_to_result(lResults, 'incorrect_crash_signature', resultValue)
                else:
                    if common.isOpen(rowStatus):
                        lcrashSignature = ast.literal_eval(crashSignature)
                        for i in lcrashSignature:
                            crashReportUrl = crashReportDomain + str(i).replace(' ', '%20').replace('`', '%60')
                            crashReportUrl = crashReportUrl.replace('<', '%3C').replace('>', '%3E')
                            #Link should be shorter than 255, otherwise Bugzilla returns an error
                            if crashReportUrl not in row['see_also'] and len(crashReportUrl) < 255:
                                util_add_to_result(lResults, 'add_crashReport_to_seeAlso', resultValue)

            everConfirmed = False
            autoConfirmed = False
            autoConfirmedValue = None
            versionChanged = False
            versionChangedValue = None
            oldestVersion = 999999
            newerVersion = False
            newerVersionValue = None
            autoFixed = False
            autoFixedValue = None
            lastAssignedValue = None
            closeDate = None
            movedToFixed = False
            movedToNeedInfo = False
            movedToNeedInfoValue = None
            isReopened = False
            reopenValue = None
            addAssigned = False
            addassignedValue = None
            movedToNew = False
            movedToNewValue = None
            addAssigned = False

            for action in row['history']:
                actionMail = action['who']
                actionDate = datetime.datetime.strptime(action['when'], "%Y-%m-%dT%H:%M:%SZ")
                common.util_check_bugzilla_mail(statList, actionMail, '', actionDate, rowId)

                resultValue = [ rowId, actionDate, actionMail ]

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
                                addedVersion = int(''.join([s for s in re.split('\.|\s',addedVersion) if s.isdigit()]).ljust(3, '0')[:3] )

                            if removedVersion == 'unspecified':
                                removedVersion = 999999
                            elif removedVersion == 'Inherited From OOo':
                                removedVersion = 0
                            else:
                                removedVersion = int(''.join([s for s in re.split('\.|\s',removedVersion) if s.isdigit()]).ljust(3, '0')[:3] )

                            if removedVersion < oldestVersion:
                                oldestVersion = removedVersion

                            if addedVersion <= oldestVersion:
                                oldestVersion = addedVersion
                                newerVersion = False
                            else:
                                newerVersion = True
                                newerVersionValue = resultValue

                    elif change['field_name'] == 'status':
                        addedStatus = change['added']
                        removedStatus = change['removed']

                        if rowStatus == 'ASSIGNED' and addedStatus == 'ASSIGNED':
                            lastAssignedValue = resultValue

                        if addedStatus == 'REOPENED' and rowStatus == 'REOPENED' and not movedToFixed:
                            isReopened = True
                            reopenValue = resultValue

                        if actionDate >= cfg['reportPeriod'] and addedStatus == 'NEEDINFO' and \
                                rowStatus == 'NEEDINFO' and common.isOpen(removedStatus):
                            movedToNeedInfo = True
                            movedToNeedInfoValue = resultValue

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
                                autoConfirmedValue = resultValue

                        if autoFixed and removedStatus == 'RESOLVED':
                            autoFixed = False

                        if actionDate >= cfg['reportPeriod']:
                            if actionMail == creatorMail and addedStatus == 'RESOLVED_FIXED' and \
                                    rowStatus == 'RESOLVED_FIXED' and 'target:' not in row['whiteboard']:
                                autoFixed = True
                                autoFixedValue = resultValue

                            if removedStatus == "ASSIGNED" and addedStatus == "NEW" and \
                                    rowStatus == "NEW" and row['assigned_to'] != 'libreoffice-bugs@lists.freedesktop.org':
                                util_add_to_result(lResults, 'remove_assignee', resultValue)
                            elif addedStatus == "ASSIGNED" and rowStatus == "ASSIGNED" and \
                                    row['assigned_to'] == 'libreoffice-bugs@lists.freedesktop.org':
                                util_add_to_result(lResults, 'add_assignee', resultValue)

                            if addedStatus == 'NEW' and rowStatus == 'NEW' and row['product'] == 'LibreOffice':
                                movedToNew = True
                                movedToNewValue = resultValue

                            if addedStatus == 'RESOLVED_FIXED' and rowStatus == 'RESOLVED_FIXED' and ('regression' in rowKeywords \
                                    or 'crash' in row['summary'].lower()):
                                util_add_to_result(lResults, 'verify_fix', resultValue)

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
                            util_add_to_result(lResults, 'reopened_after_1_months', resultValue)

                    elif change['field_name'] == 'keywords':
                        if actionDate >= cfg['reportPeriod']:
                            keywordsAdded = change['added'].split(", ")
                            for keyword in keywordsAdded:
                                if keyword in common.keywords_list and keyword in rowKeywords:
                                        if keyword == 'patch' and (common.isOpen(rowStatus) or rowStatus == 'UNCONFIRMED'):
                                            util_add_to_result(lResults, 'patch_added', resultValue)

                                        if row['status'] != 'RESOLVED':
                                            if keyword == 'regression' and 'bibisectRequest' not in rowKeywords and \
                                                    'bibisected' not in rowKeywords and 'bisected' not in rowKeywords and \
                                                    'preBibisect' not in rowKeywords and 'bibisectNotNeeded' not in rowKeywords and \
                                                    'notBibisectable' not in rowKeywords:
                                                util_add_to_result(lResults, 'regression_added', resultValue)

                                            elif keyword == 'bibisectRequest' and 'regression' not in rowKeywords:
                                                util_add_to_result(lResults, 'bibisectRequest_added', resultValue)

                                            elif keyword == 'possibleRegression' and 'possibleRegression' in rowKeywords:
                                                util_add_to_result(lResults, 'possibleregression_added', resultValue)
                                            elif keyword == 'needsUXEval' and 'libreoffice-ux-advise@lists.freedesktop.org' not in row['cc']:
                                                util_add_to_result(lResults, 'needsUXEval_missing_email', resultValue)

                    elif change['field_name'] == 'whiteboard':
                        if actionDate >= cfg['reportPeriod']:
                            for whiteboard in change['added'].split(' '):
                                if 'backportrequest' in whiteboard.lower() and \
                                        whiteboard in row['whiteboard'] and common.isOpen(rowStatus):
                                    util_add_to_result(lResults, 'backport_added', resultValue)


                    elif change['field_name'] == 'assigned_to':
                        if actionDate >= cfg['reportPeriod']:
                            removedAssignee = change['removed']
                            addedAssignee = change['added']
                            if  removedAssignee == "libreoffice-bugs@lists.freedesktop.org" and \
                                    row['assigned_to'] != 'libreoffice-bugs@lists.freedesktop.org' and \
                                    ( rowStatus == 'NEW' or rowStatus == 'UNCONFIRMED'):
                                addAssigned = True
                                util_add_to_result(lResults, 'change_status_assigned', resultValue)
                            if addedAssignee == "libreoffice-bugs@lists.freedesktop.org" and \
                                    row['assigned_to'] == 'libreoffice-bugs@lists.freedesktop.org' and rowStatus == 'ASSIGNED':
                                util_add_to_result(lResults, 'remove_assigned_status', resultValue)

            commentMail = None
            comments = row['comments'][1:]
            bSameAuthor = True
            for idx, comment in enumerate(comments):
                commentMail = comment['creator']
                commentDate = datetime.datetime.strptime(comment['time'], "%Y-%m-%dT%H:%M:%SZ")

                common.util_check_bugzilla_mail(statList, commentMail, '', commentDate, rowId)

                if bSameAuthor and commentMail != creatorMail:
                    bSameAuthor = False

            if bSameAuthor and rowStatus == 'UNCONFIRMED' and \
                    datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ") < cfg['retestUnconfirmedPeriod']:
                value = [ rowId, row['last_change_time'], creatorMail ]
                util_add_to_result(lResults, 'unconfirmed_without_comments', value)

            if len(comments) > 0:
                if rowStatus == 'UNCONFIRMED':
                    if comments[-1]['creator'] != creatorMail and \
                        datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ") < cfg['retestUnconfirmedPeriod']:
                        value = [ rowId, row['last_change_time'], comments[-1]['creator'] ]
                        util_add_to_result(lResults, 'unconfirmed_last_comment_not_from_reporter', value)
                    elif comments[-1]['creator'] == creatorMail and \
                        datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ") < cfg['inactiveUnconfirmedPeriod']:
                        value = [ rowId, row['last_change_time'], comments[-1]['creator'] ]
                        util_add_to_result(lResults, 'unconfirmed_last_comment_from_reporter', value)

                elif rowStatus == 'NEEDINFO' and comments[-1]['creator'] == creatorMail and \
                        datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ") >= cfg['retestNeedinfoPeriod']:
                    value = [ rowId, row['last_change_time'], comments[-1]['creator'] ]
                    util_add_to_result(lResults, 'needinfo_provided', value)

            if autoFixed:
                util_add_to_result(lResults, 'auto_fixed', autoFixedValue)

            if autoConfirmed:
                util_add_to_result(lResults, 'auto_confirmed', autoConfirmedValue)

            if newerVersion and rowVersion != 'unspecified':
                util_add_to_result(lResults, 'newer_version', newerVersionValue)

            if isReopened and not autoConfirmed:
                util_add_to_result(lResults, 'is_reopened', reopenValue)

            #In case the reporter assigned the bug to himself at creation time
            if not addAssigned and creationDate >= cfg['reportPeriod'] and \
                    row['assigned_to'] != 'libreoffice-bugs@lists.freedesktop.org' and (rowStatus == 'NEW' or rowStatus == 'UNCONFIRMED'):
                value = [ rowId, creationDate, row['assigned_to'] ]
                util_add_to_result(lResults, 'change_status_assigned', value)

            if movedToNeedInfo and everConfirmed:
                util_add_to_result(lResults, 'moved_to_needinfo', movedToNeedInfoValue)

            if movedToNew and row['component'] != 'Documentation' and 'needsUXEval' not in rowKeywords\
                    and 'regression' not in rowKeywords and not row['blocks']:
                util_add_to_result(lResults, 'metabug_not_added', movedToNewValue)

            if not versionChanged and movedToNew and not autoConfirmed and row['severity'] != 'enhancement' and \
                    'regression' not in rowKeywords and 'bisected' not in rowKeywords and \
                    'easyHack' not in rowKeywords and 'needsUXEval' not in rowKeywords and \
                    row['component'] != 'Documentation' and \
                    movedToNewValue[2] not in cfg['configQA']['ignore']['confirmer'] and \
                    (rowVersion.startswith(versionsToCheck) or rowVersion == 'unspecified'):
                util_add_to_result(lResults, 'version_not_changed', movedToNewValue)


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
                                value = [rowId, commentDate, row['assigned_to']]
                                util_add_to_result(lResults, 'take_action_fixed_bug', value)
                                break

                            elif commentMail == 'libreoffice-commits@lists.freedesktop.org':
                                # Check the commit hasn't been reverted
                                if 'evert' in commentText:
                                    break
                                else:
                                    value = [rowId, commentDate, row['assigned_to']]
                                    util_add_to_result(lResults, 'ping_bug_fixed', value)
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
                value = [rowId, row['last_change_time'], row['assigned_to']]
                util_add_to_result(lResults, 'inactive_assignee', value)

        elif row['summary'].lower().startswith('[meta]'):
            if not row['alias'] and common.isOpen(row['status']):
                value = [rowId, '', '']
                util_add_to_result(lResults, 'empty_alias', value)

    colorama.init(autoreset=True)
    for dKey, dValue in sorted(lResults.items()):
        if dValue:
            print('\n=== ' + dKey.replace('_', ' ').upper() + ' ===')
            dValue = sorted(dValue, key=lambda x: x[1])
            for idx in range(len(dValue)):
                background = Back.RESET

                if dValue[idx][1]:
                    if isinstance(dValue[idx][1], str):
                        dValue[idx][1] = datetime.datetime.strptime(dValue[idx][1], "%Y-%m-%dT%H:%M:%SZ")

                    if dKey == 'inactive_assignee':
                        if dValue[idx][1] >= cfg['coloredInactiveAssignedPeriod']:
                            background = Back.GREEN
                    elif dKey == 'unconfirmed_last_comment_not_from_reporter' or dKey == 'unconfirmed_without_comments':
                        if dValue[idx][1] >= cfg['coloredRetestUnconfirmedPeriod']:
                            background = Back.GREEN
                    elif dKey == 'unconfirmed_last_comment_from_reporter':
                        if dValue[idx][1] >= cfg['coloredInactiveUnconfirmedPeriod']:
                            background = Back.GREEN
                    elif dKey == 'ping_bug_fixed':
                        if dValue[idx][1] >= cfg['coloredFixBugPingPeriod']:
                            background = Back.GREEN
                    else:
                        if dValue[idx][1] >= cfg['coloredReportPeriod']:
                            background = Back.GREEN

                print(background + "{:<3} | {:<58} | {} | {}".format(
                    str(idx + 1), common.urlShowBug + str(dValue[idx][0]), str(dValue[idx][1] ), str(dValue[idx][2])))

    for k, v in statList['people'].items():
        if not statList['people'][k]['name']:
            statList['people'][k]['name'] = statList['people'][k]['email'].split('@')[0]

        if statList['people'][k]['oldest'] >= cfg['newUserPeriod'] and len(statList['people'][k]['bugs']) >= newUserBugs and \
                statList['people'][k]['email'] not in cfg['configQA']['ignore']['newContributors']:
            print('\n=== New contributor: '+ statList['people'][k]['name'] + " ("  + statList['people'][k]['email'] + ")")
            lBugs = list(statList['people'][k]['bugs'])
            for idx in range(len(lBugs)):
                isEasyHack = False
                if 'easyHack' in bugzillaData['bugs'][str(lBugs[idx])]['keywords']:
                        isEasyHack = True
                print("{:<3} | {:<58} | {}".format(
                    str(idx + 1), common.urlShowBug + str(lBugs[idx]), 'easyHack: ' + str(isEasyHack)))

        if statList['people'][k]['oldest'] >= cfg['memberPeriod'] and statList['people'][k]['newest'] >= cfg['reportPeriod'] and \
                len(statList['people'][k]['bugs']) >= memberBugs and statList['people'][k]['email'] not in cfg['configQA']['ignore']['members']:
            print('\n=== New MEMBER: ' + statList['people'][k]['name'] + " ("  + statList['people'][k]['email'] + ")")
            print('\tOldest: ' + statList['people'][k]['oldest'].strftime("%Y-%m-%d"))
            print('\tNewest: ' + statList['people'][k]['newest'].strftime("%Y-%m-%d"))
            print('\tTotal: ' + str(len(statList['people'][k]['bugs'])))

        if statList['people'][k]['newest'] < cfg['oldUserPeriod'] and statList['people'][k]['newest'] >= cfg['oldUserPeriod2'] and \
                len(statList['people'][k]['bugs']) >= oldUserBugs and statList['people'][k]['email'] not in cfg['configQA']['ignore']['oldContributors']:
            print('\n=== Old Contributor: ' + statList['people'][k]['name'] + " ("  + statList['people'][k]['email'] + ")")
            print('\tOldest: ' + statList['people'][k]['oldest'].strftime("%Y-%m-%d"))
            print('\tNewest: ' + statList['people'][k]['newest'].strftime("%Y-%m-%d"))
            print('\tTotal: ' + str(len(statList['people'][k]['bugs'])))

        statList['people'][k]['oldest'] = statList['people'][k]['oldest'].strftime("%Y-%m-%d")
        statList['people'][k]['newest'] = statList['people'][k]['newest'].strftime("%Y-%m-%d")

def runCfg():
    cfg = common.get_config()
    cfg['todayDate'] = datetime.datetime.now().replace(hour=0, minute=0,second=0)
    cfg['reportPeriod'] = common.util_convert_days_to_datetime(cfg, reportPeriodDays)
    cfg['coloredReportPeriod'] = common.util_convert_days_to_datetime(cfg, coloredPeriodDays)
    cfg['newUserPeriod'] = common.util_convert_days_to_datetime(cfg, newUserPeriodDays)
    cfg['oldUserPeriod'] = common.util_convert_days_to_datetime(cfg, oldUserPeriodDays)
    cfg['oldUserPeriod2'] = common.util_convert_days_to_datetime(cfg, oldUserPeriodDays + reportPeriodDays)
    cfg['memberPeriod'] = common.util_convert_days_to_datetime(cfg, memberPeriodDays)
    cfg['PingFixedBugPeriod'] = common.util_convert_days_to_datetime(cfg, pingFixedBugPeriodDays)
    cfg['pingFixedBugDiff'] = common.util_convert_days_to_datetime(cfg, pingFixedBugPeriodDays + reportPeriodDays)
    cfg['coloredFixBugPingPeriod'] = common.util_convert_days_to_datetime(cfg, coloredPeriodDays + pingFixedBugPeriodDays)
    cfg['retestUnconfirmedPeriod'] = common.util_convert_days_to_datetime(cfg, retestUnconfirmedPeriodDays)
    cfg['coloredInactiveUnconfirmedPeriod'] = common.util_convert_days_to_datetime(cfg, coloredPeriodDays + inactiveUnconfirmedPeriodDays)
    cfg['inactiveUnconfirmedPeriod'] = common.util_convert_days_to_datetime(cfg, inactiveUnconfirmedPeriodDays)
    cfg['coloredRetestUnconfirmedPeriod'] = common.util_convert_days_to_datetime(cfg, coloredPeriodDays + retestUnconfirmedPeriodDays)
    cfg['retestNeedinfoPeriod'] = common.util_convert_days_to_datetime(cfg, retestNeedinfoPeriodDays)
    cfg['inactiveAssignedPeriod'] = common.util_convert_days_to_datetime(cfg, inactiveAssignedPeriodDays)
    cfg['coloredInactiveAssignedPeriod'] = common.util_convert_days_to_datetime(cfg, coloredPeriodDays + inactiveAssignedPeriodDays)
    return cfg

if __name__ == '__main__':
    print("Reading and writing data to " + common.dataDir)

    if len(sys.argv) > 1:
        try:
            coloredPeriodDays = int(sys.argv[1])
        except ValueError:
            print("The argument is not an int. Ignoring it...")

    cfg = runCfg()

    bugzillaData = common.get_bugzilla()

    statList = util_create_statList_checkers()

    analyze_bugzilla_checkers(statList, bugzillaData, cfg)
