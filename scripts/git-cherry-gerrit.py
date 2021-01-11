#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

"""
A version of 'git cherry' that works with change-ids, so it can pair patches
even if their patch id changed.
"""

from typing import List
import subprocess
import sys


def from_pipe(argv: List[str]) -> str:
    """Executes argv as a command and returns its stdout."""
    result = subprocess.check_output(argv)
    return result.strip().decode("utf-8")


def get_change_id(git_cat_file: subprocess.Popen, hash_string: str) -> str:
    """Looks up the change-id for a git hash."""
    git_cat_file.stdin.write((hash_string + "\n").encode("utf-8"))
    git_cat_file.stdin.flush()
    first_line = git_cat_file.stdout.readline().decode("utf-8")
    size = first_line.strip().split(" ")[2]
    commit_msg = git_cat_file.stdout.read(int(size)).decode("utf-8")
    git_cat_file.stdout.readline()
    for line in commit_msg.split("\n"):
        if "Change-Id:" in line:
            return line
    return ""


def main() -> None:
    """Commandline interface."""
    cherry_from = ""
    if len(sys.argv) >= 2:
        cherry_from = sys.argv[1]
    cherry_to = ""
    if len(sys.argv) >= 3:
        cherry_to = sys.argv[2]

    branch_point = ""
    if len(sys.argv) >= 4:
        branch_point = sys.argv[3]

    whitelist_file = ""
    if len(sys.argv) >= 5:
        whitelist_file = sys.argv[4]

    if not cherry_from:
        print("Usage: git-cherry-gerrit.py cherry_from cherry_to [branch_point_from] [whitelist_file]")
        sys.exit(1)

    merge_base = from_pipe(["git", "merge-base", cherry_from, cherry_to])

    if not branch_point:
        branch_point = merge_base

    to_change_ids = []
    to_hashes = from_pipe(["git", "rev-list", merge_base + ".." + cherry_to]).split("\n")
    git_cat_file = subprocess.Popen(['git', 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    for to_hash in to_hashes:
        to_change_ids.append(get_change_id(git_cat_file, to_hash))

    from_hashes = from_pipe(["git", "rev-list", branch_point + ".." + cherry_from]).split("\n")
    whitelist: List[str] = []
    if whitelist_file:
        with open(whitelist_file, "r") as stream:
            whitelist = stream.read().strip().split("\n")
    for from_hash in from_hashes:
        changeid = get_change_id(git_cat_file, from_hash)
        pretty = from_pipe(["git", "--no-pager", "log", "-1", "--format=format:%h%x09%an%x09%s%x0a", from_hash])
        if not changeid:
            if not whitelist_file or not [entry for entry in whitelist if pretty in entry]:
                print("WARNING: commit '" + pretty + "' has no Change-Id, assuming it has to be cherry-picked.")
            continue

        if changeid not in to_change_ids:
            if not whitelist_file or not [entry for entry in whitelist if pretty in entry]:
                print(pretty)

    git_cat_file.stdin.close()
    git_cat_file.terminate()


if __name__ == '__main__':
    main()

# vim:set shiftwidth=4 softtabstop=4 expandtab:
