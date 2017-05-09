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


def handle_gerrit_abandon(id, text):
    return



def handle_gerrit_comment(id, text):
    return



def handle_gerrit_review(id, email):
    return



def handle_bugzilla_comment(id, text):
    return



def handle_bugzilla_unassign(id, text):
    return



def handle_bugzilla_reset_status(id):
    return



def handle_bugzilla_cc(id, email):
    return



def handle_mail_pdf(name, email):
    global mail_pdf_index

    mail_pdf_index += 1
    return {'title': 'x', 'mail': 'mentoring@documentfoundation.org', 'attach': 'x', 'file' : '/tmp/x'}



def handle_mail_miss_you(name, email):
    global mail_miss_you

    mail_miss_you += 1
    fileName = '/tmp/esc_pdf_' + str(mail_miss_you)
    fp = fopen(fileName, 'w')
    print('Hi\n' \
          'We have noticed you have not submitted patches to LibreOffice in a while. ' \
          'LibreOffice depend on volunteers like you to keep the software growing.\n' \
          'Volunteering is something most of us does in our spare time, so it is normal to have periods where you ' \
          'want to concentrate on other items, we basically just wanted to say "we miss you".\n' \
          'If you have problems or want to comment on issues, please do not hesitate to contact our development mentor.\n\n' \
          'Thanks in advance\n' \
          'the LibreOffice Development Team\n', file=fp)
    fclose(fp)
    return {'title': 'LibreOffice calling for help', 'mail': 'mentoring@documentfoundation.org', 'file': fileName }



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
    global mail_pdf_index, mail_miss_you


    autoList = util_load_data_file(cfg['homedir'] + 'stats.json')['automateList']

    try:
      for id in autoList['gerrit']['to_abandon_abandon']:
        handle_gerrit_abandon(id, "Abandoning due to lack of work, be aware it can anytime be reopened if you want to continue working")
    except Exception as e:
      print('ERROR: handle_gerrit_abandon failed with ' + str(e))
      pass
    try:
      for id in autoList['gerrit']['to_abandon_comment']:
        handle_gerrit_comment(id, "A polite ping, still working on this patch")
    except Exception as e:
      print('ERROR: handle_gerrit_comment failed with ' + str(e))
      pass
    try:
      for row in autoList['gerrit']['to_review']:
        handle_gerrit_review(row['id'], row['email'])
    except Exception as e:
      print('ERROR: handle_gerrit_review failed with ' + str(e))
      pass

    try:
      for id in autoList['bugzilla']['to_unassign_comment']:
        handle_bugzilla_comment(id, "A polite ping, still working on this bug")
    except Exception as e:
      print('ERROR: handle_bugzilla_comment failed with ' + str(e))
      pass
    try:
      for id in autoList['bugzilla']['to_unassign_unassign']:
        handle_bugzilla_unassign(id, "Unassigning due to lack of work, be aware it can anytime be assigned again if you want to continue working")
    except Exception as e:
      print('ERROR: handle_bugzilla_unassign failed with ' + str(e))
      pass
    try:
      for id in autoList['bugzilla']['assign_problem_status']:
        handle_bugzilla_reset_status(id)
    except Exception as e:
      print('ERROR: handle_bugzilla_reset_status failed with ' + str(e))
      pass
    try:
      for id in autoList['bugzilla']['to_unassign_unassign']:
        handle_bugzilla_unassign(id, '')
    except Exception as e:
      print('ERROR: handle_bugzilla_unassign failed with ' + str(e))
      pass
    try:
      for id in autoList['bugzilla']['missing_cc']:
        handle_bugzilla_cc(id, 'mentoring@libreoffice.org')
    except Exception as e:
      print('ERROR: handle_bugzilla_cc failed with ' + str(e))
      pass
    try:
      for id in autoList['bugzilla']['missing_ui_cc']:
        handle_bugzilla_cc(id, 'libreoffice-ux-advise@lists.freedesktop.org')
    except Exception as e:
      print('ERROR: handle_bugzilla_cc failed with ' + str(e))
      pass

    xMail = []
    mail_pdf_index = 0
    mail_miss_you = 0
    try:
      for row in autoList['mail']['award_1st_email']:
        x = handle_mail_pdf(row['name'], row['email'])
        if not x is None:
          xMail.append(x)
    except Exception as e:
      print('ERROR: handle_mail_pdf failed with ' + str(e))
      pass
    try:
      for row in autoList['mail']['we_miss_you_email']:
        x = handle_mail_miss_you(row['name'], row['email'])
        if not x is None:
          xMail.append(x)
    except Exception as e:
      print('ERROR: analyze_reports failed with ' + str(e))
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
