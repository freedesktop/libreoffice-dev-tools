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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# When a commit referencing a report is merged, this script
# - adds a comment to the report
# - updates the whiteboard field with target information

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

master_target = "7.1.0"
bug_regex = "\\b(?:bug|fdo|tdf|lo)[#:]?(\\d+)\\b"
dry_run = False

class FreedesktopBZ:
    bzclass = bugzilla.Bugzilla44

    bz = None

    def connect(self):
        config = ConfigParser.ConfigParser()
        config.read(os.path.dirname(os.path.abspath(__file__)) + '/config.cfg')
        url = config.get('bugzilla', 'url')
        user = config.get('bugzilla', 'user')
        password = config.get('bugzilla', 'password')
        self.bz = self.bzclass(url=url, cookiefile = "/tmp/cookie", tokenfile = "/tmp/token")
        if not dry_run:
            self.bz.login(user=user, password=password)

    def update_whiteboard(self, commit, bugnr, new_version, branch, repo_name):
        print(bugnr)
        if dry_run:
            print("DRY RUN, we would set the whiteboard to: target:\n%s" % new_version)
        else:
            bug = self.bz.getbug(bugnr)
            print(bug)
            if not bug.product in ("LibreOffice", "LibreOffice Online"):
                print("refusing to update bug with non-LO component")
                return;
            old_whiteboard = bug.getwhiteboard()

            m = re.findall(new_version, old_whiteboard)
            if m is None or len(m) == 0:
                if not old_whiteboard == "":
                    old_whiteboard = old_whiteboard + " "
                new_whiteboard = old_whiteboard + "target:" + new_version
                bug.setwhiteboard(new_whiteboard)

        cgiturl = "https://git.libreoffice.org/%s/commit/%s" % (repo_name, commit.hexsha)
        if branch is None:
            branch = "master"

        comment_msg = """%s committed a patch related to this issue.
It has been pushed to "%s":

%s

%s""" %(commit.author, branch, cgiturl, commit.summary)

        if (repo_name == "core"):
            comment_msg += """

It will be available in %s.

The patch should be included in the daily builds available at
https://dev-builds.libreoffice.org/daily/ in the next 24-48 hours. More
information about daily builds can be found at:
https://wiki.documentfoundation.org/Testing_Daily_Builds

Affected users are encouraged to test the fix and report feedback.""" %(new_version)

        if dry_run:
            print("DRY RUN, we would add the following comment:\n%s" % comment_msg)
        else:
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
        if len(micro_list) == 0:
            # first search if we are at an RC already
            search_string = "libreoffice-" + base + ".0." + "(\d+)$"
            tags = repo.tags
            print(tags)
            rc_list = [m.group(1) for m in [re.search(search_string, str(tag)) for tag in tags] if m is not None]
            print(rc_list)
            if len(rc_list) > 0:
                return base + ".0." + str(int(max(rc_list)) + 1)

            # we have not yet tagged an RC, check which betas have been tagged
            search_string = "libreoffice-" + base + ".0.0.beta(\d+)"
            beta_list = [m.group(1) for m in [re.search(search_string, str(tag)) for tag in tags] if m is not None]
            print(beta_list)
            if len(beta_list) == 0:
                # no beta yet
                return base + ".0.0.beta0"
            if max(beta_list) >= 2:
                # we only release two betas (except when we release three),
                # therefore now the next will be a RC
                return base + ".0.1"

            # normal beta
            return base + ".0.0.beta" + str(int(max(beta_list)) + 1)
        print(micro_list)
        # the next release from libreoffice-x-y is max existing z-branch + 1
        return base + "." + str(int(max(micro_list)) + 1)

    return None

def get_commit(repo, commit_id):
    commit = repo.commit(commit_id)
    return commit

def find_bugid(repo, commit_id):
    commit = get_commit(repo, commit_id)
    summary_line = commit.summary
    regex = re.compile(bug_regex)
    m = regex.findall(summary_line)
    if m is None or len(m) == 0:
        print("no bugid found")
        sys.exit()

    return m

def read_repo(repo_name):
    config = ConfigParser.ConfigParser()
    config.read(os.path.dirname(os.path.abspath(__file__)) + '/config.cfg')
    path = config.get(repo_name, 'location')
    repo = git.repo.base.Repo(path)
    return repo

def main(argv):
    global dry_run
    print(argv)
    help_text = 'libreoffice-bugzilla2.py -c commitid [-b branchname] [-r repo] [--dry-run]'
    try:
        opts, args = getopt.getopt(argv,"dhc:b:r:",["dry-run","help","commit=","branch=","repo="])
    except getopt.GetoptError:
        print(help_text)
        sys.exit(2)

    commit_id = None
    branch = None
    repo_name = None

    for opt, arg in opts:
        if opt == '-h':
            print(help_text)
            sys.exit()
        elif opt in ("-d", "--dry-run"):
            dry_run = True
        elif opt in ("-c", "--commit"):
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
        print("missing target version")
        print(opts)
        sys.exit()

    bz = FreedesktopBZ()
    bz.connect()
    print(bug_ids)
    for bug_id in bug_ids:
        print(bug_id)
        bz.update_whiteboard(commit, bug_id, target_version, branch, repo_name)

if __name__ == "__main__":
   main(sys.argv[1:])

# vim:set shiftwidth=4 softtabstop=4 expandtab:
