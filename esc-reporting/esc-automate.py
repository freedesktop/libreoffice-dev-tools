#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#





### DESCRIPTION
#
# This program automates update of bugzilla, gerrit and sends mail
#
# Installed on vm174:/usr/local/bin runs every night (generating and mailing reports)
#
#



import sys
import os
import datetime
import json


def util_load_data_file(fileName):
    try:
      fp = open(fileName, encoding='utf-8')
      rawData = json.load(fp)
      fp.close()
    except Exception as e:
      print('Error load file ' + fileName + ' due to ' + str(e))
      exit(-1)
    return rawData



def util_dump_file(fileName, rawList):
    try:
      fp = open(fileName, 'w', encoding='utf-8')
      json.dump(rawList, fp, ensure_ascii=False, indent=4, sort_keys=True)
      fp.close()
    except Exception as e:
      print('Error dump file ' + fileName + ' due to ' + str(e))
      os.remove(fileName)
      exit(-1)





def runCfg(platform):
    global cfg
    if 'esc_homedir' in os.environ:
      homeDir = os.environ['esc_homedir']
    else:
      homeDir = '/home/esc-mentoring/esc'

    cfg = util_load_data_file(homeDir + '/config.json')
    cfg['homedir'] = homeDir + '/'
    cfg['platform'] = platform
    print("Reading and writing data to " + cfg['homedir'])

    cfg['award-mailed'] = util_load_data_file(cfg['homedir'] + 'award.json')['award-mailed']
    cfg['nowDate'] = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    cfg['cutDate'] = cfg['nowDate'] - datetime.timedelta(days=365)
    cfg['1weekDate'] = cfg['nowDate'] - datetime.timedelta(days=7)
    cfg['1monthDate'] = cfg['nowDate'] - datetime.timedelta(days=30)
    cfg['3monthDate'] = cfg['nowDate'] - datetime.timedelta(days=90)
    cfg['1yearDate'] = cfg['nowDate'] - datetime.timedelta(days=365)
    return cfg



def runAutomate():
    global cfg, autoList

    autoList = util_load_data_file(cfg['homedir'] + 'stats.json')['automateList']

    # analyze test for:
    # "A polite ping"

    # gerrit non-committer patches > 4 weeks: overdue review / poking reminders --> "to_abandon_comment"
    # gerrit patches > extra 4 weeks: auto-abandon if no comments / changes. --> "to_abandon_abandon"
    # gerrit patches from non-committers, add reviewer --> "to_review"
    # bugzilla: easy-hacks: un-assign those un-touched for 4 weeks to de-conflict --> "to_unassign_comment" "to_unassign_unassign"
    # bugzilla extra: easy-hacks, check assign consistent --> "assign_problem_status" "assign_problem_user",
    # bugzilla: checking mentoring@ is CC'd on all easy-hacks --> "missing_cc"
    # bugzilla:checking UX team is CC'd on all UX hacks --> "missing_ui_cc"
    # 1st patch award email auto-generate that --> "award_1st_email"
    # "we miss you" email --> "we_miss_you_email"

    xMail = []
    try:
      x = automate_gerrit()
      if not x is None:
        xMail.append(x)
    except:
      pass
    try:
      x = automate_bugzilla()
      if not x is None:
        xMail.append(x)
    except:
      pass
    try:
      x = automate_pdf()
      if not x is None:
        xMail.append(x)
    except:
      pass

    fp = open('/tmp/runAutoMail', 'w', encoding='utf-8')
    print("#!/bin/bash", file=fp)
    print("")
    for i in xMail:
      if 'attach' in i:
        attach = '-a ' + i['attach'] + ' '
      else:
        attach = ''
      print("mail -s '" + i['title'] + "' " + attach + i['mail'] + " <  " + i['file'], file=fp)
    fp.close()



if __name__ == '__main__':
    runCfg(sys.platform)
    runAutomate()
