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
import re

reportPeriodDays = 7

newUserPeriodDays = 30
newUserBugs = 3

memberPeriodDays = 365
memberBugs = 50

oldUserPeriodDays = 180
oldUserPeriod2Days = 365
oldUserBugs = 20

fixBugPingPeriodDays = 30

retestUnconfirmedPeriodDays = 30

retestNeedinfoPeriodDays = 60

untouchedPeriodDays = 365

inactiveAssignedPeriodDays = 90

reopened6MonthsComment = "This bug has been in RESOLVED FIXED status for more than 6 months."

def util_create_statList_checkers():
    return {
        'people': {}
        }

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

            common.util_check_bugzilla_mail(statList, creatorMail, row['creator_detail']['real_name'], creationDate, rowId)

            actionMail = None
            everConfirmed = False
            autoConfirmed = False
            autoConfirmMail = ""
            versionChanged = False
            versionChangedMail = ""
            oldestVersion = 999999
            newerVersion = False
            newerVersionMail = ""
            autoFixed = False
            autoFixedMail = ""
            addAssigned = False
            addAssignedMail = ""
            removeAssigned = False
            removeAssignedMail = ""
            addAssignee = False
            addAssigneeMail = ""
            removeAssignee = False
            removeAssigneeMail = ""
            backPortAdded = False
            backPortAddedEmail = ""
            targetRemoved = False
            targetRemovedEmail = ""
            lastAssignedEmail = ""
            patchAdded = False
            regressionAdded = False
            possibleRegressionAdded = False
            isReopened6Months = False
            closeDate = None
            reopener6MonthsEmail = ""
            movedToFixed = False
            movedToNeedInfo = False
            movedToNeedInfomail = ""
            isReopened = False
            reopenerEmail = ""

            for action in row['history']:
                actionMail = action['who']
                actionDate = datetime.datetime.strptime(action['when'], "%Y-%m-%dT%H:%M:%SZ")
                common.util_check_bugzilla_mail(statList, actionMail, '', actionDate, rowId)

                # Use this variable in case the status is set before the resolution
                newStatus = None
                for change in action['changes']:

                    if change['field_name'] == 'version':
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
                                newerVersionMail = actionMail

                    elif change['field_name'] == 'status':
                        addedStatus = change['added']
                        removedStatus = change['removed']

                        if rowStatus == 'ASSIGNED' and addedStatus == 'ASSIGNED':
                            lastAssignedEmail = actionMail

                        if addedStatus == 'REOPENED' and rowStatus == 'REOPENED' and not movedToFixed:
                            isReopened = True
                            reopenerEmail = actionMail

                        if actionDate >= cfg['reportPeriod'] and addedStatus == 'NEEDINFO' and \
                                rowStatus == 'NEEDINFO' and common.isOpen(removedStatus):
                            movedToNeedInfo = True
                            movedToNeedInfoMail = actionMail

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
                                autoConfirmedMail = actionMail

                        if autoFixed and removedStatus == 'RESOLVED':
                            autoFixed = False

                        if actionDate >= cfg['reportPeriod']:
                            if actionMail == creatorMail and addedStatus == 'RESOLVED_FIXED' and \
                                    rowStatus == 'RESOLVED_FIXED' and 'target:' not in row['whiteboard']:
                                autoFixed = True
                                autoFixedMail = actionMail

                            if removedStatus == "ASSIGNED" and addedStatus == "NEW" and \
                                    rowStatus == "NEW" and row['assigned_to'] != 'libreoffice-bugs@lists.freedesktop.org':
                                removeAssignee = True
                                removeAssigneeMail = actionMail
                            elif addedStatus == "ASSIGNED" and rowStatus == "ASSIGNED" and \
                                    row['assigned_to'] == 'libreoffice-bugs@lists.freedesktop.org':
                                addAssignee = True
                                addAssigneeMail = actionMail

                    elif change['field_name'] == 'resolution':
                        if newStatus:
                            addedStatus = newStatus + "_" + change['added']
                            newStatus = None

                        if change['added'] == 'FIXED':
                            movedToFixed = True
                            isReopened = False
                            if common.isOpen(rowStatus):
                                closeDate = actionDate
                        elif change['removed'] == 'FIXED' and closeDate and actionDate >= cfg['reportPeriod'] and \
                                (actionDate - closeDate).days > 180:
                            isReopened6Months = True
                            reopener6MonthsEmail = actionMail


                    elif change['field_name'] == 'keywords':
                        if actionDate >= cfg['reportPeriod']:
                            keywordsAdded = change['added'].split(", ")
                            for keyword in keywordsAdded:
                                if keyword in common.keywords_list and keyword in rowKeywords:
                                        if keyword == 'patch':
                                            patchAdded = True

                                        if keyword == 'regression':
                                            regressionAdded = True

                                        if keyword == 'possibleRegression':
                                            possibleRegressionAdded = True

                    elif change['field_name'] == 'whiteboard':
                        if actionDate >= cfg['reportPeriod']:
                            for whiteboard in change['added'].split(' '):
                                if 'backportrequest' in whiteboard.lower() and \
                                        whiteboard in row['whiteboard'] and common.isOpen(rowStatus):
                                    backPortAdded = True
                                    backPortAddedMail = actionMail

                            for whiteboard in change['removed'].split(' '):
                                if 'target' in whiteboard.lower() and whiteboard.split(":")[1] not in row["whiteboard"]:
                                    targetRemoved = True
                                    targetRemovedMail = actionMail

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

                if common.isOpen(rowStatus) and reopened6MonthsComment in comment['text']:
                    isReopened6Months = True

            if len(comments) > 0:
                if rowStatus == 'UNCONFIRMED' and comments[-1]['creator'] != creatorMail and \
                        datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ") < cfg['retestUnconfirmedPeriod']:
                        if 'untouchedUnconfirmed' not in lResults:
                            lResults['untouchedUnconfirmed'] = []
                        tup = (rowId, row['last_change_time'])
                        lResults['untouchedUnconfirmed'].append(tup)
                elif rowStatus == 'NEEDINFO' and comments[-1]['creator'] == creatorMail and \
                        datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ") >= cfg['retestNeedinfoPeriod']:
                        if 'NeedInfoProvided' not in lResults:
                            lResults['NeedInfoProvided'] = []
                        tup = (rowId, row['last_change_time'])
                        lResults['NeedInfoProvided'].append(tup)
            else:
                if rowStatus == 'UNCONFIRMED' and \
                        datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ") < cfg['retestUnconfirmedPeriod']:
                    if 'Unconfirmed1Comment' not in lResults:
                        lResults['Unconfirmed1Comment'] = []
                    tup = (rowId, row['last_change_time'])
                    lResults['Unconfirmed1Comment'].append(tup)

            for person in row['cc_detail']:
                email = person['email']
                if commentMail == email or actionMail == email:
                    common.util_check_bugzilla_mail(statList, email, person['real_name'])

            if (common.isOpen(rowStatus) or rowStatus == 'UNCONFIRMED') and regressionAdded and \
                    'bibisectRequest' not in rowKeywords and 'bibisected' not in rowKeywords and \
                    'bisected' not in rowKeywords and 'preBibisect' not in rowKeywords and \
                    'bibisectNotNeeded' not in rowKeywords and 'notBibisectable' not in rowKeywords:
                if 'regressionAdded' not in lResults:
                    lResults['regressionAdded'] = []
                tup = (rowId, '')
                lResults['regressionAdded'].append(tup)

            if possibleRegressionAdded and 'possibleRegression' in rowKeywords:
                if 'possibleRegressionAdded' not in lResults:
                    lResults['possibleRegressionAdded'] = []
                tup = (rowId, '')
                lResults['possibleRegressionAdded'].append(tup)

            if autoFixed:
                if 'autoFixed' not in lResults:
                    lResults['autoFixed'] = []
                tup = (rowId, autoFixedMail)
                lResults['autoFixed'].append(tup)

            if autoConfirmed:
                if 'autoConfirmed' not in lResults:
                    lResults['autoConfirmed'] = []
                tup = (rowId, autoConfirmedMail)
                lResults['autoConfirmed'].append(tup)

            if newerVersion and row['version'] != 'unspecified':
                if 'newerVersion' not in lResults:
                    lResults['newerVersion'] =  []
                tup = (rowId, newerVersionMail)
                lResults['newerVersion'].append(tup)

            if (common.isOpen(rowStatus) or rowStatus == 'UNCONFIRMED') and patchAdded:
                if 'patchAdded' not in lResults:
                    lResults['patchAdded'] = []
                tup = (rowId, '')
                lResults['patchAdded'].append(tup)

            crashSignature = row['cf_crashreport']
            if crashSignature and not crashSignature.startswith('["'):
                if 'crashSignature' not in lResults:
                    lResults['crashSignature'] = []
                tup = (rowId, '')
                lResults['crashSignature'].append(tup)

            if isReopened6Months:
                if 'reopened6Months' not in lResults:
                    lResults['reopened6Months'] = []
                tup = (rowId, reopener6MonthsEmail)
                lResults['reopened6Months'].append(tup)

            if isReopened and not autoConfirmed:
                if 'reopened' not in lResults:
                    lResults['reopened'] = []
                tup = (rowId, reopenerEmail)
                lResults['reopened'].append(tup)

            #In case the reporter assigned the bug to himself at creation time
            if addAssigned or (creationDate >= cfg['reportPeriod'] and row['assigned_to'] != 'libreoffice-bugs@lists.freedesktop.org' and \
                    (rowStatus == 'NEW' or rowStatus == 'UNCONFIRMED')):
                if 'addAssigned' not in lResults:
                    lResults['addAssigned'] = []
                tup = (rowId, addAssignedMail)
                lResults['addAssigned'].append(tup)

            if removeAssigned:
                if 'removeAssigned' not in lResults:
                    lResults['removeAssigned'] = []
                tup = (rowId, removeAssignedMail)
                lResults['removeAssigned'].append(tup)

            if movedToNeedInfo and everConfirmed:
                if 'movedToNeedInfo' not in lResults:
                    lResults['movedToNeedInfo'] = []
                tup = (rowId, movedToNeedInfoMail)
                lResults['movedToNeedInfo'].append(tup)

            if addAssignee:
                if 'addAssignee' not in lResults:
                    lResults['addAssignee'] =[]
                tup = (rowId, addAssigneeMail)
                lResults['addAssignee'].append(tup)

            if removeAssignee:
                if 'removeAssignee' not in lResults:
                    lResults['removeAssignee'] =[]
                tup = (rowId, removeAssigneeMail)
                lResults['removeAssignee'].append(tup)

            if backPortAdded:
                if 'backPortAdded' not in lResults:
                    lResults['backPortAdded'] = []
                tup = (rowId, backPortAddedMail)
                lResults['backPortAdded'].append(tup)

            if targetRemoved:
                if 'targetRemoved' not in lResults:
                    lResults['targetRemoved'] = []
                tup = (rowId, targetRemovedMail)
                lResults['targetRemoved'].append(tup)

            #Check bugs where:
            # 1. last comment is done by 'libreoffice-commits@lists.freedesktop.org'
            # 2. Penultimate comment is done by 'libreoffice-commits@lists.freedesktop.org',
            # last comment is not written by the commit's author and it's not a revert commit
            if common.isOpen(rowStatus) and ((commentMail == 'libreoffice-commits@lists.freedesktop.org' and \
                    'evert' not in comments[-1]['text']) or \
                    (len(comments) >= 2 and comments[-2]['creator'] == 'libreoffice-commits@lists.freedesktop.org' and \
                    comments[-2]['text'].split(' committed a patch related')[0] != statList['people'][comments[-1]['creator']]['name'] and \
                    'evert' not in comments[-2]['text'])) and \
                    commentDate < cfg['fixBugPingPeriod'] and commentDate >= cfg['fixBugPingDiff'] and \
                    'easyHack' not in row['keywords']:
                if 'fixBugPing' not in lResults:
                    lResults['fixBugPing'] = []
                tup = (rowId, '')
                lResults['fixBugPing'].append(tup)

            if rowStatus == 'ASSIGNED' and \
                    datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ") < cfg['inactiveAssignedPeriod'] and \
                    'easyHack' not in row['keywords'] and \
                    rowId not in cfg['configQA']['ignore']['inactiveAssigned']:
                if 'inactiveAssigned' not in lResults:
                    lResults['inactiveAssigned'] = []
                tup = (rowId, lastAssignedEmail)
                lResults['inactiveAssigned'].append(tup)

        elif row['summary'].lower().startswith('[meta]'):
            if not row['alias'] and common.isOpen(row['status']):
                if 'emptyAlias' not in lResults:
                    lResults['emptyAlias'] = []
                tup = (rowId, '')
                lResults['emptyAlias'].append(tup)


    for dKey, dValue in lResults.items():
        if dValue:
            print('\n=== ' + dKey + ' ===')
            dValue = sorted(dValue, key=lambda x: x[1])
            for idx in range(len(dValue)):
                print(str(idx + 1) + ' - ' + common.urlShowBug + str(dValue[idx][0]) + " - " + str(dValue[idx][1]))

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
                print(str(idx + 1) + ' - ' + common.urlShowBug + str(lBugs[idx]) + ' - easyHack: ' + str(isEasyHack))

        if statList['people'][k]['oldest'] >= cfg['memberPeriod'] and statList['people'][k]['newest'] >= cfg['reportPeriod'] and \
                len(statList['people'][k]['bugs']) >= memberBugs and statList['people'][k]['email'] not in cfg['configQA']['ignore']['members']:
            print('\nNew member: ' + statList['people'][k]['name'] + " ("  + statList['people'][k]['email'] + ")")
            print('\tOldest: ' + statList['people'][k]['oldest'].strftime("%Y-%m-%d"))
            print('\tNewest: ' + statList['people'][k]['newest'].strftime("%Y-%m-%d"))
            print('\tTotal: ' + str(len(statList['people'][k]['bugs'])))

        if statList['people'][k]['newest'] < cfg['oldUserPeriod'] and statList['people'][k]['newest'] >= cfg['oldUserPeriod2'] and \
                len(statList['people'][k]['bugs']) >= oldUserBugs and statList['people'][k]['email'] not in cfg['configQA']['ignore']['oldContributors']:
            print('\nOld Contributor: ' + statList['people'][k]['name'] + " ("  + statList['people'][k]['email'] + ")")
            print('\tOldest: ' + statList['people'][k]['oldest'].strftime("%Y-%m-%d"))
            print('\tNewest: ' + statList['people'][k]['newest'].strftime("%Y-%m-%d"))
            print('\tTotal: ' + str(len(statList['people'][k]['bugs'])))

        statList['people'][k]['oldest'] = statList['people'][k]['oldest'].strftime("%Y-%m-%d")
        statList['people'][k]['newest'] = statList['people'][k]['newest'].strftime("%Y-%m-%d")

def runCfg():
    cfg = common.get_config()
    cfg['todayDate'] = datetime.datetime.now().replace(hour=0, minute=0,second=0)
    cfg['reportPeriod'] = common.util_convert_days_to_datetime(cfg, reportPeriodDays)
    cfg['newUserPeriod'] = common.util_convert_days_to_datetime(cfg, newUserPeriodDays)
    cfg['oldUserPeriod'] = common.util_convert_days_to_datetime(cfg, oldUserPeriodDays)
    cfg['oldUserPeriod2'] = common.util_convert_days_to_datetime(cfg, oldUserPeriod2Days)
    cfg['memberPeriod'] = common.util_convert_days_to_datetime(cfg, memberPeriodDays)
    cfg['fixBugPingPeriod'] = common.util_convert_days_to_datetime(cfg, fixBugPingPeriodDays)
    cfg['fixBugPingDiff'] = common.util_convert_days_to_datetime(cfg, fixBugPingPeriodDays + reportPeriodDays)
    cfg['untouchedPeriod'] = common.util_convert_days_to_datetime(cfg, untouchedPeriodDays)
    cfg['retestUnconfirmedPeriod'] = common.util_convert_days_to_datetime(cfg, retestUnconfirmedPeriodDays)
    cfg['retestNeedinfoPeriod'] = common.util_convert_days_to_datetime(cfg, retestNeedinfoPeriodDays)
    cfg['inactiveAssignedPeriod'] = common.util_convert_days_to_datetime(cfg, inactiveAssignedPeriodDays)
    return cfg

if __name__ == '__main__':
    print("Reading and writing data to " + common.dataDir)

    cfg = runCfg()

    bugzillaData = common.get_bugzilla()

    statList = util_create_statList_checkers()

    analyze_bugzilla_checkers(statList, bugzillaData, cfg)
