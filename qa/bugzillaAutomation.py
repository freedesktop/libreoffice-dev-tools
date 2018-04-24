#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import common
import requests
import datetime
import os
import json

needInfoFollowUpPingComment = "Dear Bug Submitter,\n\nPlease read this message in its entirety before proceeding."

untouchedPeriodDays = 365

#Path to addObsolete.txt
addObsoleteDir = '/home/xisco/dev-tools/qa'

def util_create_statList():
    return {
        'tags':
            {
                'addObsolete': set(),
                'removeObsolete': set()
            },
        'untouched': []
    }
def analyze_bugzilla(statList, bugzillaData, cfg):
    print("Analyze bugzilla\n", end="", flush=True)
    for key, row in bugzillaData['bugs'].items():

        rowId = row['id']

        #Ignore META bugs and deletionrequest bugs.
        if not row['summary'].lower().startswith('[meta]') and row['component'] != 'deletionrequest':
            rowStatus = row['status']
            rowResolution = row['resolution']

            if rowStatus == 'VERIFIED' or rowStatus == 'RESOLVED':
                rowStatus += "_" + rowResolution

            rowKeywords = row['keywords']

            comments = row['comments'][1:]
            for idx, comment in enumerate(comments):
                #Check for duplicated comments
                if idx > 0 and comment['text'] == comments[idx-1]['text']:
                        statList['tags']['addObsolete'].add(comment["id"])

                if rowStatus != 'NEEDINFO' and \
                        "obsolete" not in [x.lower() for x in comment["tags"]] and \
                        (comment["text"].startswith(common.untouchedPingComment[:250]) or \
                        comment["text"].startswith("A polite ping, still working on this bug") or \
                        comment["text"].startswith(common.needInfoPingComment) or \
                        comment["text"].startswith(needInfoFollowUpPingComment)):
                    statList['tags']['addObsolete'].add(comment["id"])

            if len(comments) > 0:
                if comments[-1]["text"].startswith(common.untouchedPingComment[:250]):

                    if rowStatus != 'NEEDINFO':
                        if "obsolete" not in [x.lower() for x in comments[-1]["tags"]]:
                            statList['tags']['addObsolete'].remove(comments[-1]["id"])
                        else:
                            statList['tags']['removeObsolete'].add(comments[-1]["id"])
                elif comments[-1]["text"].startswith(common.needInfoPingComment):
                    if rowStatus != 'NEEDINFO':
                        if "obsolete" not in [x.lower() for x in comments[-1]["tags"]]:
                            statList['tags']['addObsolete'].remove(comments[-1]["id"])
                        else:
                            statList['tags']['removeObsolete'].add(comments[-1]["id"])
                elif comments[-1]["text"].startswith(needInfoFollowUpPingComment) or \
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
                        statList['untouched'].append(rowId)

def automated_untouched(statList):

    print('== Untouched bugs ==')
    for bugId in statList['untouched']:
        bugId = str(bugId)
        command = '{"comment" : "' + common.untouchedPingComment.replace('\n', '\\n') + '", "is_private" : false}'

        urlGet = 'https://bugs.documentfoundation.org/rest/bug/' + bugId + '/comment?api_key=' + cfg['configQA']['api-key']
        rGet = requests.get(urlGet)
        rawData = json.loads(rGet.text)
        rGet.close()

        if rawData['bugs'][bugId]['comments'][-1]['text'][:250] != common.untouchedPingComment[:250]:
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
    filename = addObsoleteDir + "addObsolete.txt"
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
    cfg['untouchedPeriod'] = common.util_convert_days_to_datetime(cfg, untouchedPeriodDays)

    return cfg

if __name__ == '__main__':
    print("Reading and writing data to " + common.dataDir)

    cfg = runCfg()

    bugzillaData = common.get_bugzilla()

    statList = util_create_statList()

    analyze_bugzilla(statList, bugzillaData, cfg)

    automated_tagging(statList)
    automated_untouched(statList)
