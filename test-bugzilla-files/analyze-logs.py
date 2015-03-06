#!/usr/bin/env python

# Libreoffice test-bugzilla-files control script
# Copyright (C) 2014  Markus Mohrhard
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import os.path
import collections
import csv
import re

def analyze_import_crash(crashtest_file, crashes):
    if not os.path.exists(crashtest_file):
        return 0

    regex = re.compile("Crash:/srv/crashtestdata/files/(\w*)")
    for line in open(crashtest_file):
        r = regex.search(line)
        format = r.groups()[0]
        if format not in crashes:
            crashes[format] = 0
        crashes[format] = 1 + crashes[format]
    return crashes

def analyze_export_crash(crashtest_file, crashes):
    if not os.path.exists(crashtest_file):
        return 0

    regex = re.compile("/srv/crashtestdata/files/\w+/[a-zA-Z0-9_-]+\.(\w+)")
    for line in open(crashtest_file):
        r = regex.search(line)
        format = r.groups()[0]
        if format not in crashes:
            crashes[format] = 0
        crashes[format] = 1 + crashes[format]
    return crashes

def analyze_validation_errors(directory):
    exts = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            filebase, fileext = os.path.splitext(file)
            if fileext == ".log":
                exts.append(os.path.splitext(filebase)[1].replace(".",""))
    return collections.Counter(exts)

def get_directories():
    d='.'
    directories = [o for o in os.listdir(d) if os.path.isdir(os.path.join(d,o))]
    return directories

def import_csv(filename):
    if not os.path.exists(filename):
        return None
    infile = open(filename,'r')
    reader = csv.DictReader(infile.readlines())
    infile.close()
    return reader

def export_csv(filename, data, reader):
    fieldnames = set(data.keys())

    if not reader is None:
        fieldnames.update(reader.fieldnames)
    writer = csv.DictWriter(open(filename, "w"), sorted(fieldnames), restval=0)
    writer.writeheader()
    if not reader is None:
        for row in reader:
            writer.writerow(row)
    writer.writerow(data)

def update_import():
    import_crashes = dict()
    analyze_import_crash("crashlog.txt", import_crashes)
    reader = import_csv("importCrash.csv")
    export_csv("importCrash.csv", import_crashes, reader)

def update_export():
    export_crashes = dict()
    analyze_export_crash("exportCrash.txt", export_crashes)
    reader = import_csv("exportCrashes.csv")
    export_csv("exportCrashes.csv", export_crashes, reader)

def update_validation():
    validation_errors = analyze_validation_errors("./validation")
    reader = import_csv("validationErrors.csv")
    export_csv("validationErrors.csv", validation_errors, reader)

update_import()
update_export()
update_validation()
