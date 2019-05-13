#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import comments
import common
import requests
import datetime
import os
import json

untouchedPeriodDays = 365

needInfoPingPeriodDays = 180

needInfoFollowUpPingPeriodDays = 30

needsCommentPeriodDays = 14

def util_create_statList():
    return {
        'tags':
            {
                'addObsolete': set(),
                'removeObsolete': set()
            },
        'untouched': {},
        'needInfoPing': {},
        'needInfoFollowUpPing': {},
        'needInfoToUnconfirmed': {},
        'needsComment':
            {
                'add': [],
                'remove': []
            }
    }
def analyze_bugzilla(statList, bugzillaData, cfg):
    print("Analyze bugzilla\n", end="", flush=True)
    for key, row in bugzillaData['bugs'].items():

        rowId = row['id']

        #Ignore META bugs and deletionrequest bugs.
        if not row['summary'].lower().startswith('[meta]') and row['component'].lower() != 'deletionrequest':
            rowStatus = row['status']
            rowResolution = row['resolution']

            if rowStatus == 'VERIFIED' or rowStatus == 'RESOLVED':
                rowStatus += "_" + rowResolution

            rowKeywords = row['keywords']

            rowCreator = row['creator_detail']['real_name']
            if not rowCreator:
                rowCreator = row['creator_detail']['email'].split('@')[0]

            if rowStatus == "NEEDINFO" and \
                    datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ") < cfg['needInfoPingPeriod']:
                statList['needInfoPing'][rowId] = rowCreator

            comments = row['comments'][1:]
            bSameAuthor = True
            for idx, comment in enumerate(comments):
                #Check for duplicated comments
                if idx > 0 and comment['text'] == comments[idx-1]['text']:
                        statList['tags']['addObsolete'].add(comment["id"])

                if rowStatus != 'NEEDINFO' and \
                        "obsolete" not in [x.lower() for x in comment["tags"]] and \
                        ('MassPing-UntouchedBug' in comment["text"] or \
                        comment["text"].startswith("A polite ping, still working on this bug") or \
                        '[Automated Action]' in comment["text"] or \
                        'MassPing-NeedInfo' in comment["text"]):
                    statList['tags']['addObsolete'].add(comment["id"])

                if bSameAuthor and comment['creator'] != row['creator']:
                    bSameAuthor = False

            if bSameAuthor and rowStatus == 'UNCONFIRMED' and 'QA:needsComment' not in row['whiteboard'] and \
                    datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ") < cfg['needsCommentPeriod']:
                statList['needsComment']['add'].append(rowId)

            elif not bSameAuthor and 'QA:needsComment' in row['whiteboard']:
                statList['needsComment']['remove'].append(rowId)


            if len(comments) > 0:
                if rowStatus == 'NEEDINFO' and \
                        comments[-1]['creator'] == row['creator']:
                    statList['needInfoToUnconfirmed'][rowId] = rowCreator

                if 'MassPing-UntouchedBug' in comments[-1]["text"]:
                    if rowStatus != 'NEEDINFO':
                        if "obsolete" not in [x.lower() for x in comments[-1]["tags"]]:
                            statList['tags']['addObsolete'].remove(comments[-1]["id"])
                        else:
                            statList['tags']['removeObsolete'].add(comments[-1]["id"])
                elif 'MassPing-NeedInfo-Ping' in comments[-1]["text"]:
                    if rowStatus != 'NEEDINFO':
                        if "obsolete" not in [x.lower() for x in comments[-1]["tags"]]:
                            statList['tags']['addObsolete'].remove(comments[-1]["id"])
                        else:
                            statList['tags']['removeObsolete'].add(comments[-1]["id"])
                    else:
                        if datetime.datetime.strptime(row['last_change_time'], "%Y-%m-%dT%H:%M:%SZ") < cfg['needInfoFollowUpPingPeriod']:
                            statList['needInfoFollowUpPing'][rowId] = rowCreator

                elif 'MassPing-NeedInfo' in comments[-1]["text"] or \
                        comments[-1]["text"].startswith("A polite ping, still working on this bug"):
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
                        statList['untouched'][rowId] = rowCreator

def post_comment(statList, keyInStatList, commentId, comment, addFirstLine, changeCommand=""):
    for bugId, creator in statList[keyInStatList].items():
        bugId = str(bugId)

        urlGet = 'https://bugs.documentfoundation.org/rest/bug/' + bugId + '/comment?api_key=' + cfg['configQA']['api-key']
        rGet = requests.get(urlGet)
        rawData = json.loads(rGet.text)
        rGet.close()

        if commentId not in rawData['bugs'][bugId]['comments'][-1]['text']:
            if addFirstLine:
                firstLine = "Dear " + creator + ",\\n\\n"
                fullComment = firstLine + comment
            else:
                fullComment = comment

            command = '{"comment" : "' + fullComment.replace('\n', '\\n') + '", "is_private" : false}'
            urlPost = 'https://bugs.documentfoundation.org/rest/bug/' + bugId + '/comment?api_key=' + cfg['configQA']['api-key']
            rPost = requests.post(urlPost, command.encode('utf-8'))
            print('Bug: ' + bugId + ' - Comment: ' + str(json.loads(rPost.text)['id']))
            rPost.close()

            if changeCommand:
                urlPut = 'https://bugs.documentfoundation.org/rest/bug/' + bugId + '?api_key=' + cfg['configQA']['api-key']
                rPut = requests.put(urlPut, changeCommand.encode('utf-8'))
                print('Bug: ' + bugId + ' - ' + changeCommand)
                rPut.close()

def update_whiteboard(statList, whiteboardTag):
    for action, listOfBugs in statList[whiteboardTag].items():
        for bugId in listOfBugs:
            bugId = str(bugId)

            urlGet = 'https://bugs.documentfoundation.org/rest/bug/' + bugId + '?api_key=' + cfg['configQA']['api-key']
            rGet = requests.get(urlGet)
            rawData = json.loads(rGet.text)
            rGet.close()
            whiteboard = rawData['bugs'][0]['whiteboard']

            doRequest = False
            tag = 'QA:' + whiteboardTag
            if action == 'add':
                if rawData['bugs'][0]['status'] == 'UNCONFIRMED' and tag not in whiteboard :
                    doRequest = True
                    whiteboard = whiteboard + ' ' + tag
            elif action == 'remove':
                if tag in whiteboard :
                    doRequest = True
                    whiteboard = whiteboard.replace(tag, '').strip()

            if doRequest :
                command = '{"whiteboard" : "' + whiteboard.strip() + '"}'
                urlPut = 'https://bugs.documentfoundation.org/rest/bug/' + bugId + '?api_key=' + cfg['configQA']['api-key']
                rPut = requests.put(urlPut, command.encode('utf-8'))
                print('Bug: ' + bugId + ' - ' + command)
                rPut.close()

def automated_needsCommentFromQA(statList):
    print('== Add tag to UNCONFIRMED bug that needs a comment ==')
    update_whiteboard(statList, "needsComment")

def automated_needInfoToUnconfirmed(statList):

    print('== Move NEEDINFO to UNCONFIRMED ==')
    command = '{"status" : "UNCONFIRMED"}'
    post_comment(statList, "needInfoToUnconfirmed", 'NeedInfo-To-Unconfirmed', comments.needInfoToUnconfirmedComment, False, command)

def automated_needInfoFollowUpPing(statList):

    print('== NEEDINFO FollowUp Ping ==')
    command = '{"status" : "RESOLVED", "resolution" : "INSUFFICIENTDATA"}'
    post_comment(statList, "needInfoFollowUpPing", 'MassPing-NeedInfo-FollowUp', comments.needInfoFollowUpPingComment, True, command)

def automated_needInfoPing(statList):

    print('== NEEDINFO Ping ==')
    post_comment(statList, "needInfoPing", 'MassPing-NeedInfo-Ping', comments.needInfoPingComment, True)

def automated_untouched(statList):

    print('== Untouched bugs ==')
    post_comment(statList, "untouched", 'MassPing-UntouchedBug', comments.untouchedPingComment, True)

def automated_tagging(statList):
    #tags are sometimes not saved in bugzilla_dump.json
    #thus, save those comments automatically tagged as obsolete
    #so we don't tag them again next time

    print('== Obsolete comments ==')
    lAddObsolete = []
    filename = common.configDir + "addObsolete.txt"
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
    cfg = common.get_config()
    cfg['untouchedPeriod'] = common.util_convert_days_to_datetime(untouchedPeriodDays)
    cfg['needInfoPingPeriod'] = common.util_convert_days_to_datetime(needInfoPingPeriodDays)
    cfg['needInfoFollowUpPingPeriod'] = common.util_convert_days_to_datetime(needInfoFollowUpPingPeriodDays)
    cfg['needsCommentPeriod'] = common.util_convert_days_to_datetime(needsCommentPeriodDays)

    return cfg

if __name__ == '__main__':
    print("Reading and writing data to " + common.dataDir)

    cfg = runCfg()

    bugzillaData = common.get_bugzilla()

    statList = util_create_statList()

    analyze_bugzilla(statList, bugzillaData, cfg)

    automated_tagging(statList)
    automated_untouched(statList)
    automated_needInfoPing(statList)
    automated_needInfoFollowUpPing(statList)
    automated_needInfoToUnconfirmed(statList)
    automated_needsCommentFromQA(statList)
