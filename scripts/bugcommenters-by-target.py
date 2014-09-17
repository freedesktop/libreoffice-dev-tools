#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import sys
import re
import textwrap
from urllib.request import urlopen, URLError
from io import BytesIO

def get_bugs_for_target(target):
    url = 'https://bugs.libreoffice.org/buglist.cgi?bug_status=UNCONFIRMED&bug_status=NEW&bug_status=ASSIGNED&bug_status=REOPENED&bug_status=RESOLVED&bug_status=VERIFIED&bug_status=CLOSED&bug_status=NEEDINFO&bug_status=PLEASETEST&columnlist=&list_id=351988&product=LibreOffice&query_format=advanced&resolution=FIXED&status_whiteboard=target%%3A%s&status_whiteboard_type=allwords&ctype=csv' % target
    try:
        resp = urlopen(url)
    except URLError:
        sys.stderr.write('Error fetching {}'.format(url))
        sys.exit(1)
    bug_ids=[]
    for line in [raw.decode('utf-8').strip('\n') for raw in BytesIO(resp.read())][1:]:
        bug_ids.append(int(line))
    return bug_ids

def get_bug_xml(bug_id):
    xml=''
    try:
        url = 'https://bugs.libreoffice.org/show_bug.cgi?ctype=xml&id=%d' % bug_id
        resp = urlopen(url)
    except URLError:
        sys.stderr.write('Error fetching {}'.format(url))
        sys.exit(1)
    for line in [raw.decode('utf-8') for raw in BytesIO(resp.read())]:
        xml+=line
    return xml

def get_bug_touchers(bug_id):
    touchers=[]
    whoregex = re.compile('<who name="([^"]+)">([^<]+)</who>')
    for line in get_bug_xml(bug_id).split('\n'):
        match = whoregex.search(line)
        if match:
            touchers.append(match.group(1))
    return touchers

def get_target_toucher_counts(target):
    touch_counts = {}
    bug_ids = get_bugs_for_target(target)
    sys.stderr.write('scanning %d bugs for target %s: %s\n' % (len(bug_ids), target, str(bug_ids)))
    for bug_id in bug_ids:
        sys.stderr.write('scanning bug %d ...\n' % bug_id)
        # we dont count multiple comments on one bug, thus using a set here
        for toucher in set(get_bug_touchers(bug_id)):
            if toucher in touch_counts:
                touch_counts[toucher]+=1
            else:
                touch_counts[toucher]=1
    touch_counts_sorted = reversed(sorted((count, name) for (name, count) in touch_counts.items()))
    return touch_counts_sorted

# Print one line (wrapped to 70 cols) for each set of users who made
# the same # of bug comments.
#
# (We use this format for Release pages on the wiki)
def print_for_wiki():
    counts = {}
    for count, name in get_target_toucher_counts(sys.argv[1]):
        if name == 'Commit Notification':
            # Throw out these lines
            pass
        elif count in counts:
            counts[count] += ", " + name
        else:
            counts[count] = name

    # Sort dictionary keys from largest # of comments to least and
    # print them out.
    pad = 5

    # Text body is indented 1 additional char from comment count.
    tw = textwrap.TextWrapper(subsequent_indent=" " * (pad + 1))
    for count, names in sorted(counts.items(), reverse=True):
        print("{n:{width}} ".format(n=count, width=pad) + tw.fill(names))

# Print one line for each commenter.
def print_regular():
    for touch_count in get_target_toucher_counts(sys.argv[1]):
        if not touch_count[1] == 'Commit Notification':
            print("%5d %s" % (touch_count[0], touch_count[1]))

if __name__ == '__main__':
    if(len(sys.argv) > 2 and
       sys.argv[2] == "wiki"):
        print_for_wiki()
    elif(len(sys.argv) > 1):
        print_regular()
    else:
        print('Error: Please provide a LibreOffice version!')
