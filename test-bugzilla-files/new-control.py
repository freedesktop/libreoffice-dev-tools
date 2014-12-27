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
import concurrent.futures
import time
import subprocess
import getopt
import sys

def partition(l, n):
    for i in range(0, len(l), n):
        yield l[i:i+n]

def get_tasks(directory, files_per_task):
    flist = [os.path.join(dirpath, f) for dirpath, dirnames, fnames in os.walk(directory) for f in fnames]

    partitioned_list = list(partition(flist, files_per_task))
    task_files = []
    i = 0
    for list_item in partitioned_list:
        filename = "task" + str(i)
        task_file = open(filename, "w")
        for item in list_item:
            task_file.write("%s\n" % item)
        task_files.append(os.path.join(os.getcwd(),filename))
        i += 1
    print("number of tasks: " + str(len(task_files)))
    return task_files

def execute_task(task_file, asan):
    print(asan)
    if asan == 1:
        subprocess.call("./execute_asan.sh " + task_file + " --asan", shell=True)
    elif asan == 0:
        subprocess.call("./execute.sh " + task_file, shell=True)
    time.sleep(1)

def usage():
    message = """usage: {program} [option] dir"
 - h | --help: print usage information
 
 'dir' is the path to the directory with the test files"""
    print(message.format(program = os.path.basename(sys.argv[0])))

if __name__ == "__main__":
    opts, args = getopt.getopt(sys.argv[1:], "hd:a", ["help", "directory=", "asan"])
    if "-h" in opts or "--help" in opts:
        usage()
        sys.exit()

    asan = 0
    if count(opts) > 0 and "--asan" in opts[0]:
        print("yeah")
        asan = 1

    if len(args) == 0:
        usage()
        sys.exit(1)

    directory = args[0]

    print(directory)
    if not os.path.isdir(directory):
        print("no valid directory")
        sys.exit(1)

    task_size = 100
    workers = 20
    if asan == 1:
        workers = 32

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_task = {executor.submit(execute_task, task_file, asan): task_file for task_file in get_tasks(directory, task_size)}
        for future in concurrent.futures.as_completed(future_to_task):
            task = future_to_task[future]
            try:
                future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (task, exc))
            else:
                print('%r successfully passed' % (task))
