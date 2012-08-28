#!/usr/bin/env python

import sys, re
import urllib2, gzip
from StringIO import StringIO
from collections import Counter

month = ''
if len(sys.argv) >= 2:
    month = sys.argv[1]

url = 'http://lists.freedesktop.org/archives/libreoffice-bugs/' + month + '.txt.gz'
print 'Downloading ' + url

try:
    response = urllib2.urlopen(url)
    buf = StringIO(response.read())
    gz = gzip.GzipFile(fileobj=buf)

    txt = gz.read()
    gz.close()

    reportedby = re.compile(r'^.*ReportedBy:.(.*)$', re.MULTILINE)
    reporters = re.findall(reportedby, txt)

    wrangledby = re.compile(r'^.*<(.*)> changed:$', re.MULTILINE)
    wranglers = re.findall(wrangledby, txt)

    topreporters = Counter(reporters).most_common(10)
    topwranglers = Counter(wranglers).most_common(10)

    print '=== Top reporters:'
    for reporter in topreporters:
        print reporter[0] + '\t' + str(reporter[1])

    print '=== Top wranglers:'
    for wrangler in topwranglers:
        print wrangler[0] + '\t' + str(wrangler[1])

except urllib2.URLError:
    print 'Unknown file - give an archive in the form YYYY-Month as argv[1]'

