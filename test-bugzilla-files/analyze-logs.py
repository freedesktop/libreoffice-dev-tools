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

def analyze_import_crash(directory):
    crashtest_file = os.path.join(directory, "crashlog.txt")
    if not os.path.exists(crashtest_file):
        return 0
    num_lines = sum(1 for line in open(crashtest_file))
    return num_lines

def analyze_export_crash(directory):
    crashtest_file = os.path.join(directory, "exportCrash.txt")
    if not os.path.exists(crashtest_file):
        return collections.Counter()
    exts = []
    for line in open(crashtest_file):
        ext = os.path.splitext(line)[1]
        exts.append(ext.replace(".","").replace("\n",""))
    return collections.Counter(exts)

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
    reader = csv.DictReader(open(filename))
    return reader

def export_csv(filename, data, reader):
    fieldnames = set(data.keys())
    if not reader is None:
        fieldnames &= set(reader.fieldnames)
    writer = csv.DictWriter(open(filename, "w"), fieldnames)
    writer.writeheader()
    if not reader is None:
        for row in reader:
            writer.writerow(row)
    writer.writerow(data)

def update_import():
    import_crashes = dict()
    for directory in get_directories():
        import_crashes[directory] = analyze_import_crash(directory)
    reader = import_csv("importCrash.csv")
    export_csv("importCrash.csv", import_crashes, reader)

def update_export():
    export_crashes = collections.Counter()
    for directory in get_directories():
        export_crashes += analyze_export_crash(directory)
    reader = import_csv("exportCrashes.csv")
    export_csv("exportCrashes.csv", export_crashes, reader)

def update_validation():
    validation_errors = analyze_validation_errors("./validation")
    reader = import_csv("validationErrors.csv")
    export_csv("validationErrors.csv", validation_errors, reader)

update_import()
update_export()
update_validation()
