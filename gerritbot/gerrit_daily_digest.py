#!/usr/bin/env python
# -*- Mode: makefile-gmake; tab-width: 4; indent-tabs-mode: t -*-
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
'''
Created on 19.06.2012

@author: david ostrovsky
'''

from subprocess import check_output, STDOUT
from json import loads
import getopt, sys
import argparse
#from pprint import pprint

def main():
    parser = argparse.ArgumentParser('gerrit daily digest generator')
    parser.add_argument('-s', '--status', choices=['open', 'merged', 'abandoned'], required=True)
    parser.add_argument('-g', '--gerrit', help='(i. e. logerrit or gerrit.libreoffice.org, use alias in your ~/.ssh(config with your public key)', required=True)
    parser.add_argument('-p', '--project', help='(i. e. core)', required=True)
    parser.add_argument('-b', '--branch', help='(i. e. master)', required=True)
    args=vars(parser.parse_args())
    gerrit_host_name = args['gerrit']
    status = args['status']
    project = args['project']
    branch = args['branch']
    cmd = "ssh " + gerrit_host_name + " gerrit query --format=JSON status:" + status + " project:core branch:master"
    lines = check_output(cmd, shell=True, stderr=STDOUT).strip()
    for chunk in lines.split("\n"):
        data = loads(chunk)
        #pprint(data)
        if 'url' in data.keys():
            print data['url'] + " \"" + data['subject'] + "\" " + data['owner']['email'] 
    
if __name__ == "__main__":
    main()
# vim: set et sw=4 ts=4:
