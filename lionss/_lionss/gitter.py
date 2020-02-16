#!/usr/bin/env python
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

import subprocess
import os
import pylev # levenstein module

class worker:
    def __init__(self, needle, case, repo_path):
        self.goal = needle
        self.case = case
        self.proposals = dict()
        
        if os.path.exists(os.path.join(repo_path, '.git')):
            self.git_dir = '--git-dir=' + os.path.join(repo_path, '.git')
            self.worktree = '--work-tree=' + repo_path
        elif os.path.exists(os.path.join(repo_path, 'git')):
            self.git_dir = '--git-dir=' + repo_path
            self.worktree = ''
        else:
            raise Exception('git repo path not found. Repo must exist and be up-to-date !')


    def start(self, gset):
        self.ggsettings = gset
        # rough pattern building: all chars of the word(s) + hotkey sign)
        items = len(self.goal)
        goalpat = ''.join(set(self.goal + self.ggsettings['hotkey']))
        # add +1 for potential hotkey sign
        pattern_counter = '{' + str(items) + ',' + str(items + 1) + '}'
        fullpat = self.ggsettings['pattern_prefix'] + '[' + goalpat + ']' + pattern_counter

        try:
            gg_opt = '-EnI'
            if not self.case: gg_opt += 'i'
            
            gg_matches = subprocess.check_output(
                        ["git", self.git_dir, self.worktree] + 
                            ['grep', gg_opt, fullpat.encode('ascii'), '--'] + 
                            self.ggsettings['file_selectors'] + ['HEAD'],
                        stderr=subprocess.STDOUT)

        except subprocess.CalledProcessError as e:
            if e.returncode == 1:  # git grep found nothing
                return
            else:
                raise(e)
        except:
            raise
            
        line_matches = gg_matches.splitlines()
        dbg = ""
        for match in line_matches:
            [fname, line, text] = match.split(':', 2)
            goalmatch_real = text.split(self.ggsettings['text_splitter'][0])[1]\
                        .split(self.ggsettings['text_splitter'][1])[0] 
            if self.case: goalmatch = goalmatch_real
            else: goalmatch = goalmatch_real.lower()
            skip = False
            for word in self.goal.split(' '):
                if not self.case: word = word.lower()
                if not word in goalmatch: skip = True
            if skip: continue    

            if goalmatch_real not in self.proposals:
                self.proposals[goalmatch_real] = [[fname, line]]
            else:
                self.proposals[goalmatch_real] += [[fname, line]]
        #~ return str([dbg,gg_matches]+["git", self.git_dir, self.worktree] +
                   #~ ['grep', gg_opt, fullpat.encode('ascii'), '--'] +
                   #~ self.ggsettings['file_selectors']);
    
    def apply_lev(self, threshold):
        if self.proposals:
            for value in self.proposals.keys():
                if pylev.levenshtein(value, self.goal) > threshold:
                    del self.proposals[value]
    
# EOF
