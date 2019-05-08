#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import common

def util_create_statList():
    return {
        'needinfo': [],
        '1year': [],
        '2years': [],
        '3years': []
    }

def analyze_bugzilla(statList, bugzillaData):
    print("Analyze bugzilla\n", end="", flush=True)

    for key, row in bugzillaData['bugs'].items():
        #Ignore META bugs and deletionrequest bugs.
        if not row['summary'].lower().startswith('[meta]') and row['component'].lower() != 'deletionrequest':
            rowId = row['id']

            comments = row['comments'][1:]

            if len(comments) > 0:
                if comments[-1]["text"].startswith(common.untouchedPingComment[:250]):

                    if len(comments) > 1 and comments[-2]["text"].startswith(common.untouchedPingComment[:250]):
                        if len(comments) > 2 and comments[-3]["text"].startswith(common.untouchedPingComment[:250]):
                            statList['3years'].append(rowId)
                        else:
                            statList['2years'].append(rowId)
                    else:
                        statList['1year'].append(rowId)

                elif 'MassPing-NeedInfo-Ping' in comments[-1]["text"]:
                    if row['status'] == 'NEEDINFO':
                        statList['needinfo'].append(rowId)

def massping_Report(statList):
    fp = open('/tmp/massping_report.txt', 'w', encoding='utf-8')

    for key, value in sorted(statList.items()):
        print(file=fp)
        print('* ' + key + ' - ' + str(len(value)) + ' bugs.', file=fp)
        for i in range(0, len(value), 400):
            subList = value[i:i + 400]
            common.util_create_short_url(fp, subList)

    fp.close()

if __name__ == '__main__':
    print("Reading and writing data to " + common.dataDir)


    bugzillaData = common.get_bugzilla()

    statList = util_create_statList()

    analyze_bugzilla(statList, bugzillaData)

    massping_Report(statList)
