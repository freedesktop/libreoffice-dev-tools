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
import urllib.request
import time
import subprocess

def get_directories():
    d='.'
    directories = [o for o in os.listdir(d) if os.path.isdir(os.path.join(d,o))]
    return directories

def execute_task(directory):
    print("Yeah")
    print(directory)
    subprocess.call("./execute.sh " + directory, shell=True)
    time.sleep(10)
    return 

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    future_to_task = {executor.submit(execute_task, dirs): dirs for dirs in get_directories()}
    for future in concurrent.futures.as_completed(future_to_task):
        task = future_to_task[future]
        try:
            future.result()
        except Exception as exc:
            print('%r generated an exception: %s' % (task, exc))
        else:
            print('%r successfully passed' % (task))
