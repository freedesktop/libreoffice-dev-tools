#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

import common

def util_create_statList_crashes():
    return {
        'crashes': {}
        }

def analyze_bugzilla_checkers(statList, bugzillaData):
    print("Analyzing crashes\n", end="", flush=True)

    for key, row in bugzillaData['bugs'].items():
        rowId = row['id']

        #Ignore META bugs and deletionrequest bugs.
        if not row['summary'].lower().startswith('[meta]') and row['component'].lower() != 'deletionrequest':

            rowStatus = row['status']
            rowResolution = row['resolution']

            if rowStatus == 'VERIFIED' or rowStatus == 'RESOLVED':
                rowStatus += "_" + rowResolution
            crashSignature = row['cf_crashreport']

            if crashSignature:
                if crashSignature not in statList['crashes']:
                    statList['crashes'][crashSignature] = []
                statList['crashes'][crashSignature].append([rowId, rowStatus])

def create_crashes_list(statList) :
    fp = open('/tmp/crashes.txt', 'w', encoding='utf-8')

    print('Crash list created in /tmp/crashes.txt')

    for key, value in sorted(statList['crashes'].items()):
        if len(value) > 1:
            print(file=fp)
            print('* ' + key + '.', file=fp)
            for i in value:
                print('\t - ' + i[1] + ' - ' + common.urlShowBug + str(i[0]), file=fp)
    fp.close()

if __name__ == '__main__':
    print("Reading and writing data to " + common.dataDir)

    bugzillaData = common.get_bugzilla()

    statList = util_create_statList_crashes()

    analyze_bugzilla_checkers(statList, bugzillaData)

    create_crashes_list(statList)
