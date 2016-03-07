#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import sys
import csv
import io
import datetime
import json
import xmltodict
from xml.etree.ElementTree import XML
from   urllib.request import urlopen, URLError



def get_list_easyHacks() :
    url = 'https://bugs.documentfoundation.org/buglist.cgi?' \
          'bug_status=UNCONFIRMED&bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&bug_status=VERIFIED&bug_status=NEEDINFO' \
          '&columnlist=Cbug_id' \
          '&keywords=easyHack%2C%20' \
          '&keywords_type=allwords' \
          '&query_format=advanced' \
          '&resolution=---' \
          '&ctype=csv' \
          '&human=0'
    try:
        resp = urlopen(url)
    except URLError:
        sys.stderr.write('Error fetching {}'.format(url))
        sys.exit(1)
    xCSV = list(csv.reader(io.TextIOWrapper(resp)))
    resp.close()
    rawList = []
    for row in xCSV[1:]:
       rawList.append(row[0])
    return rawList



def get_bug(id) :
    url = 'https://bugs.documentfoundation.org/show_bug.cgi?ctype=xml&id=' + id
    try:
        resp = urlopen(url)
    except URLError:
        sys.stderr.write('Error fetching {}'.format(url))
        sys.exit(1)
    bug = xmltodict.parse(resp.read())
    resp.close()
    return bug



def optimize_bug(bug_org) :
    bug = bug_org['bugzilla']['bug']
    del bug['bug_file_loc']
    del bug['cclist_accessible']
    del bug['classification']
    del bug['classification_id']
    del bug['comment_sort_order']
    del bug['creation_ts']
    del bug['delta_ts']
    del bug['reporter_accessible']
    del bug['resolution']

    # collect info for new comments:
    if 'reporter' not in bug :
        newText = 'org_reporter: MISSING'
    else :
        if type(bug['reporter']) is str:
            newText = 'org_reporter: ' + bug['reporter'] + '\n'
        else :
            newText = 'org_reporter: ' + bug['reporter']['@name'] + '/' + bug['reporter']['#text'] + '\n'
        del bug['reporter']

    for line in bug['long_desc'] :
       if 'who' not in line or type(line) is str:
         newText += 'who: UNKNOWN' + '\n' + line
       else :
         newText += 'who: ' + line['who']['@name'] + '/' + line['who']['#text']
    for i in range(len(bug['long_desc'])-1, -1, -1) :
       del bug['long_desc'][i]
    bug['long_desc'].append({'thetext' : newText})
    addAlso = 'https://issues.apache.org/ooo/show_bug.cgi?id='+bug['bug_id']
    if 'see_also' not in bug :
      bug['see_also'] = addAlso
    elif not type(bug['see_also']) is list :
        x = bug['see_also']
        bug['see_also']  = [x, addAlso]
    else :
      bug['see_also'].append(addAlso)
    del bug['bug_id']
    return bug




if __name__ == '__main__':
    # get data from bugzilla and gerrit
    easyHacks = get_list_easyHacks()
    easyHacks.sort()
    bugs = []

    for id in easyHacks :
      bugs.append(optimize_bug(get_bug(id)))

    print(json.dumps(bugs))

