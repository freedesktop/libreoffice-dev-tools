# libreoffice git bugzilla integration
# Copyright (C) 2014 Markus Mohrhard
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

import datetime
import os
import re
import sys, getopt
import git
import ConfigParser

if hasattr(sys.version_info, "major") and sys.version_info.major >= 3:
# pylint: disable=F0401,E0611
    from urllib.parse import urlparse
else:
    from urlparse import urlparse

import bugzilla
from bugzilla import Bugzilla
from bugzilla.base import _BugzillaToken

master_target = "4.4.0"
bug_regex = "fdo#(\d+)"

class FreedesktopBZ:
    bzclass = bugzilla.Bugzilla44

    bz = None

    def connect(self):
        config = ConfigParser.ConfigParser()
        config.read('config.cfg')
        url = config.get('bugzilla', 'url')
        user = config.get('bugzilla', 'user')
        password = config.get('bugzilla', 'password')
        self.bz = self.bzclass(url=url, cookiefile = "/tmp/cookie", tokenfile = "/tmp/token")
        self.bz.login(user=user, password=password)

    def update_whiteboard(self, commit, bugnr, new_version, branch, repo_name):
        bug = self.bz.getbug(bugnr)
        print(bug)
        old_whiteboard = bug.getwhiteboard()

        m = re.findall(new_version, old_whiteboard)
        if m is None or len(m) == 0:
            new_whiteboard = old_whiteboard + " target:" + new_version
            bug.setwhiteboard(new_whiteboard)

        cgiturl = "http://cgit.freedesktop.org/libreoffice/%s/commit/?id=%s" %(repo_name, commit.hexsha)
        if branch is not None and branch != "master":
            cgiturl = cgiturl + "&h=" + branch
        else:
            branch = "master"

        comment_msg = """%s committed a patch related to this issue.
It has been pushed to "%s":

%s

%s

It will be available in %s.

The patch should be included in the daily builds available at
http://dev-builds.libreoffice.org/daily/ in the next 24-48 hours. More
information about daily builds can be found at:
http://wiki.documentfoundation.org/Testing_Daily_Builds
Affected users are encouraged to test the fix and report feedback.""" %(commit.author, branch, cgiturl, commit.summary, new_version)
        bug.addcomment(comment_msg)




def find_target_version(repo, branch):
    if branch is None or branch == "master":
        return master_target

    # check if committed to a release branch
    # form libreoffice-x-y-z => will be available in x.y.z
    match = re.search("libreoffice-(\d+)-(\d+)-(\d+)", branch)
    if match is not None:
        return ".".join(map(str, match.groups()))

    # form libreoffice-x-y
    # branch of libreoffice-x-y-z exists => will be available in x.y.z+1
    # else
    #   tag libreoffice-x.y.0.z exists => will be available in x.y.0.z+1 (RC)
    #   else
    #       beta
    match = re.search("libreoffice-(\d+)-(\d+)", branch)
    if match is not None:
        base = ".".join(map(str, match.groups()))
        branches = repo.remote().refs
        branch_names = [str(branch) for branch in branches]
        print(branch_names)
        search_string = "libreoffice-"+"-".join(map(str, match.groups())) + "-(\d+)"
        print(search_string)
        micro_list = [m.group(1) for m in [re.search(search_string, branch) for branch in branch_names] if m is not None]
        if micro_list.count() == 0:
            # first search if we are at an RC already
            search_string = "libreoffice-" + base + ".0." + "(\d+)"
            rc_list = [m.group(1) for m in [re.search(search_string, str(tag)) for tag in tags] if m is not None]
            print(rc_list)
            if len(rc_list) > 0:
                return base + ".0." + str(max(rc_list) + 1)

            # we have not yet tagged an RC, check which betas have been tagged
            search_string = "libreoffice-" + base + ".0.0.beta(\d+)" 
            beta_list = [m.group(1) for m in [re.search(search_string, str(tag)) for tag in tags] if m is not None]
            if len(beta_list) == 0:
                # no beta yet
                return base + ".0.0.beta0"
            if max(beta_list) == 2:
                # we only release two betas, therefore now the next will be a RC
                return base + ".0.1"
            
            # normal beta
            return base + ".0.0.beta" + str(max(beta_list) + 1)
        print(micro_list)
        # the next release from libreoffice-x-y is max existing z-branch + 1
        return base + "." + str(max(micro_list) + 1)

    return None

def get_commit(repo, commit_id):
    commit = repo.commit(commit_id)
    return commit

def find_bugid(repo, commit_id):
    commit = get_commit(repo, commit_id)
    summary_line = commit.summary
    m = re.search(bug_regex, summary_line)
    if m is None or len(m.groups()) == 0:
        print("no bugid found")
        sys.exit()
    
    return m.groups()

def read_repo(repo_name):
    config = ConfigParser.ConfigParser()
    config.read('config.cfg')
    path = config.get(repo_name, 'location')
    repo = git.repo.base.Repo(path)
    return repo

def main(argv):
    print(argv)
    try:
        opts, args = getopt.getopt(argv,"hc:b:r:",["commit=","branch=","repo=","help"])
    except getopt.GetoptError:
        print('test.py -c commitid -r repo [-b branchname]')
        sys.exit(2)

    commit_id = None
    branch = None
    repo_name = None

    for opt, arg in opts:
        if opt == '-h':
            print('test.py -c commitid [-b branchname] [-r repo]')
            sys.exit()
        elif opt in ("-c", "--commit_id"):
            commit_id = arg
        elif opt in ("-b", "--branch"):
            branch = arg
        elif opt in ("-r", "--repo"):
            repo_name = arg

    print(commit_id)
    print(branch)
    print(repo_name)

    repo = read_repo(repo_name)

    target_version = find_target_version(repo, branch)

    bug_ids = find_bugid(repo, commit_id)
    
    commit = get_commit(repo, commit_id)

    if target_version is None:
        sys.exit()

    bz = FreedesktopBZ()
    bz.connect()
    for bug_id in bug_ids:
        bz.update_whiteboard(commit, bug_id, target_version, branch, repo_name)

if __name__ == "__main__":
   main(sys.argv[1:])
