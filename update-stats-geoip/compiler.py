#!/usr/bin/python
#
# You will need to get the GeoLite ASN database from:
# http://dev.maxmind.com/geoip/legacy/geolite/
#
# No proper support for ipV6 addresses yet (i.e. geolocation/ISP data) -- they
# are in a separate db, and only available in newer version of python-geoip (i.e.
# would have to be built separately) so possibly not worth the bother yet?

# Introduces Python 3 style print
from __future__ import print_function

import bz2
import collections
import ConfigParser
import datetime
import GeoIP
import cPickle as pickle
import re
import sys
import time
import os.path

#sResolution = "%W" # Split by week
sResolution = "%m" # Split by month

sPrefix = "country-months"


sGEOIPFile = "GeoIP.dat"

gi = GeoIP.open(sGEOIPFile,GeoIP.GEOIP_STANDARD)

def getCountryForIP(sIP):
    return str(gi.country_name_by_addr(sIP))

dataLessDates = {
    datetime.date(2013,1,3),
    datetime.date(2013,2,28),
    datetime.date(2013,3,6),
    datetime.date(2013,3,7),
    datetime.date(2013,4,11),
    datetime.date(2013,4,12),
    datetime.date(2013,4,13),
    datetime.date(2013,4,14),
    datetime.date(2013,8,28),
    datetime.date(2013,8,29),
    datetime.date(2013,8,30),
    datetime.date(2013,8,31),
    datetime.date(2013,9,1),datetime.date(2013,9,2),datetime.date(2013,9,3),datetime.date(2013,9,4),datetime.date(2013,9,5),datetime.date(2013,9,6),datetime.date(2013,9,7),
    datetime.date(2013,9,8),datetime.date(2013,9,9),datetime.date(2013,9,10)
    }

VERSIONLIST = set({"3.3", "3.4", "3.5", "3.6", "4.0", "4.1", "4.2"})

linePattern = re.compile('^([^ ]+) - - \[([^\/]+)\/([^\/]+)\/([^:]+):([0-9][0-9])[^\]]*\] "GET [^"]*" [^ ]+ [^ ]+ "[^"]*" "[^ ]* ([0-9]\.[0-9])[^(]*\(([^-;]+)[^;]*; ([^;]*);')

print("*Analysing IPs...")

config = ConfigParser.RawConfigParser()
config.read('storage-' + sPrefix + '/compiler.cfg')


if config.has_option('Main', 'last_year'):
    currentFileDate = datetime.date(int(config.get('Main', 'last_year')), int(config.get('Main', 'last_month')), int(config.get('Main', 'last_day')))
else:
    currentFileDate = datetime.date(2012,04,27)

def getCurrentFileName():
    return "data/" + "update.libreoffice.org-access_log-" + currentFileDate.strftime("%Y%m%d") + ".bz2"

sKnownIPsLocation = "storage-" + sPrefix + "/knownIPs.dat"

knownIPs = set()
if os.path.isfile(sKnownIPsLocation):
    f = open(sKnownIPsLocation, 'r')
    knownIPs = set(f.readlines())

ipHits = collections.defaultdict(dict)
currentWeek = ""

newIPsOverall = set() # We keep a track of new IPs overall
newIPs = collections.defaultdict(set) # But also new IPs associated with what version they downloaded

lastDate = datetime.date(1980,1,1)

while os.path.isfile(getCurrentFileName()) or currentFileDate in dataLessDates:
    print(getCurrentFileName())

    if (currentFileDate in dataLessDates):
        currentFileDate += datetime.timedelta(days=1)
        continue

    with bz2.BZ2File(getCurrentFileName(), 'r') as aFile:
        for line in aFile:
            m = linePattern.split(line)
            if len(m) > 1:
                sIP = m[1]
                sDay = m[2]
                sMonth = m[3]
                sYear = m[4]

                currentDate = datetime.date(int(sYear), time.strptime(sMonth,'%b').tm_mon, int(sDay))

                # Store the week, reinitialise counts -- should be refactored out
                if currentWeek != currentDate.strftime(sResolution):
                     # We need the week before, i.e the week we just parsed
                     # The exact date we hit doesn't matter, but we need to shift
                     # an entire week since e.g. 6 days of data could be missing
                     # and currentDate *could* be the last day of the week.
                    storageDate = lastDate
                    if currentWeek != "":
                        for version in VERSIONLIST:
                            sDirectory = "storage-" + sPrefix + "/" + version + storageDate.strftime("/%Y/" + sResolution)
                            if not os.path.exists(sDirectory):
                                os.makedirs(sDirectory)
                            pickle.dump( ipHits.get(version, {}), open(sDirectory + "/iphits.dat", 'w' ))

                        # Create country mapping here:
                        for sVersion in VERSIONLIST:
                            countryHits = {} # Reuse for every version to save memory
                            for sIP,nHits in ipHits.get(sVersion, {}).iteritems():
                                sCountry = getCountryForIP(sIP)
                                if len(sCountry) > 0:
                                    countryHits[sCountry] = countryHits.get(sCountry,0) + nHits

                            sDirectory = "storage-" + sPrefix + "/" + sVersion + storageDate.strftime("/%Y/" + sResolution)
                            if not os.path.exists(sDirectory):
                                os.makedirs(sDirectory)
                            pickle.dump( countryHits, open(sDirectory + "/countryhits.dat", 'w' ))
                            print("storing "+ sDirectory + "/countryhits.dat")

                        # Deal with new IPSortedByHits
                        # per version
                        for sVersion in VERSIONLIST:
                            sDirectory = "storage-" + sPrefix + "/" + version + storageDate.strftime("/%Y/" + sResolution)
                            file = open(sDirectory + "/newips.dat", 'w')
                            file.writelines( "%s\n" % item for item in newIPs[sVersion] )
                        # And total
                        sDirectory = "storage-" + sPrefix + "/" + "overall" + storageDate.strftime("/%Y/" + sResolution)
                        if not os.path.exists(sDirectory):
                            os.makedirs(sDirectory)
                        file = open(sDirectory + "/newips.dat", 'w')
                        file.writelines( "%s\n" % item for item in newIPs )
                        knownIPs.add(sIP)

                    # Cleanup
                    currentWeek = currentDate.strftime(sResolution)
                    print("Now on week " + currentDate.strftime(sResolution + " of %Y"))
                    ipHits = collections.defaultdict(dict)
                    newIPsOverall = set() # We keep a track of new IPs overall
                    newIPs = collections.defaultdict(set) # But also new IPs associated with what version they downloaded

                    # And read in existing data for this week
                    for version in VERSIONLIST:
                        sFile = "storage-" + sPrefix + "/" + version + currentDate.strftime("/%Y/" + sResolution) + "/iphits.dat"
                        if os.path.exists(sFile):
                            print("*********************************************************************************")
                            print("WARNING: data mis-ordered, we are reloading the following file, could be very wrong")
                            print(sFile)
                            #raw_input("Press Enter to continue: ")
                            ipHits[version] = pickle.load(open(sFile))
                            #pickle.dump( ipHits.get(sVersion, {}), open(sDirectory + "/iphits.dat", 'w' ))
                            print("reading "+ sFile)
                        # Countries are reprocessed on every write, so we can ignore them
                        # Unique IPs will be a mess if data isn't ordered, so ignore for now...
                        # TODO: deal with ^^^

                lastDate = currentDate

                #sHour = m[5]
                #sOS = m[7] #Unused
                sVersion = m[6] # Hash of version...

                if sVersion in VERSIONLIST: # Some people hit the url with a browser, so various UAs here....
                    ipHits[sVersion][sIP] = ipHits.get(sVersion, {}).get(sIP,0) + 1

                    if sIP not in knownIPs:
                        newIPsOverall.add(sIP)
                        newIPs[sVersion].add(sIP)
                        # We don't add to the knownIPs list yet, as the data
                        # could get lost as we only write completed weeks
                        # of data, hence we update knownIPS in the week storage
                        # mechanism above
                else:
                    print("Unknown version: " + line)

    currentFileDate += datetime.timedelta(days=1)


if not config.has_section('Main'):
    config.add_section('Main')

config.set('Main', 'last_year', currentFileDate.strftime("%Y"))
config.set('Main', 'last_month', currentFileDate.strftime("%m"))
config.set('Main', 'last_day', currentFileDate.strftime("%d"))

config.write(open("storage-" + sPrefix + "/compiler.cfg", 'w'))

file = open(sKnownIPsLocation, 'w')
file.writelines( "%s\n" % item for item in knownIPs )

print("*Completed successfully")