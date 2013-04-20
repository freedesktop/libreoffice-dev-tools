#!/usr/bin/env python3

import sys, re
import gzip
from urllib.request import urlopen, URLError
from io import BytesIO
from collections import Counter

month = ''
if len(sys.argv) >= 2:
    month = sys.argv[1]

url = 'http://lists.freedesktop.org/archives/libreoffice-bugs/' + month + '.txt.gz'
print('Downloading ' + url)

try:
    response = urlopen(url)
    buf = BytesIO(response.read())
    gz = gzip.GzipFile(fileobj=buf)

    txt = gz.read().decode('us-ascii')
    gz.close()

    reportedby = re.compile(r'^.*Reporter:.(.*)$', re.MULTILINE)
    reporters = re.findall(reportedby, txt)

    wrangledby = re.compile(r'^.*<(.*)> changed:$', re.MULTILINE)
    wranglers = re.findall(wrangledby, txt)

    topreporters = Counter(reporters).most_common(30)
    topwranglers = Counter(wranglers).most_common(30)

    print('\n=== ' + month[5:] + ' ' + month[:4] + '===')
    print('\n--- Top 30 reporters ---')
    for reporter in topreporters:
        print('{0:40}{1:5d}'.format(reporter[0], reporter[1]))

    print('\n--- Top 30 wranglers ---')
    for wrangler in topwranglers:
        print('{0:40}{1:5d}'.format(wrangler[0], wrangler[1]))

except URLError:
    print('Unknown file - give an archive in the form YYYY-Month as argv[1]')

