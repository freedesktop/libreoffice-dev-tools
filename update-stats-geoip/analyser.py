#!/usr/bin/python

# Introduces Python 3 style print
from __future__ import print_function

import argparse
import collections
import datetime
import cPickle as pickle
import os

VERSIONLIST = set({"3.3", "3.4", "3.5", "3.6", "4.0", "4.1", "4.2"})

parser = argparse.ArgumentParser(description='Process LO Update Ping data')
#parser.addArgument('versions', metavar='V', type=int, nargs='+',
                   #help='The LO versions you would like to analyse (3.5, 3.6, 4.0, 4.1.)')

args = parser.parse_args()


sPrefix = "country-months"

#sSep = "\t" # Easier on the eyes
sSep = ";" # Easier on the software

# Year/Month to start with.
year = 2011
month = 1

sHeaderLine="Country" + sSep + "Version" + sSep + "YearMonth" + sSep + "hits"

print(sHeaderLine)

while (datetime.date(year, month, 1) + datetime.timedelta(days=20)) < datetime.date.today():
    month += 1
    if (month > 12):
        year += 1
        month = 1
    aData = collections.defaultdict(dict)
    for version in VERSIONLIST:
        sFile = "storage-" + sPrefix + "/" + version + "/" + str(year) + "/" + str(month).zfill(2) + "/countryhits.dat"
        if not os.path.exists(sFile):
            continue;
        with open(sFile, 'r') as aFile:
            aData[version] = pickle.load(aFile)

    for sVersion in VERSIONLIST:
        for sCountry,nHits in aData.get(sVersion, {}).iteritems():
            if (nHits > 300) and len(sCountry) > 0:
                print(sCountry + sSep + sVersion + sSep + str(year)+str(month).zfill(2) + sSep + str(nHits))
