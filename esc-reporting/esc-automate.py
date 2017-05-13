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


def doMail(mail, subject, content, attach=None):
    if attach:
      attach = '-a ' + attach + ' '
    else:
      attach = ''
    sendMail = 'mail -r mentoring@libreoffice.org -s "' + subject + '" ' + attach + mail + ' <<EOF\n' + content + '\nEOF\n'
    os.system(sendMail)



def handle_gerrit_abandon(id, text):
    # handle_gerrit_abandon(id, cfg['automate']['gerrit']['abandon'])
    return



def handle_gerrit_comment(id, text):
    # handle_gerrit_comment(id, 'A polite ping, ' + cfg['automate']['gerrit']['comment'])
    return



def handle_gerrit_review(id, email):
    return



def handle_bugzilla_comment(id, text):
    #handle_bugzilla_comment(id, 'A polite ping, ' + cfg['automate']['bugzilla']['comment'])
    return



def handle_bugzilla_unassign(id, text):
    # handle_bugzilla_unassign(id, cfg['automate']['bugzilla']['comment'])
    return



def handle_bugzilla_reset_user(id, text):
    return



def handle_bugzilla_reset_status(id, text):
    return



def handle_bugzilla_cc(id, email):
    # handle_bugzilla_cc(id, 'mentoring@libreoffice.org')
    return



def handle_bugzilla_ui_cc(id, email):
    # handle_bugzilla_ui_cc(id, 'libreoffice-ux-advise@lists.freedesktop.org')
    return



def handle_mail_pdf(email, name):
    global cfg, pdfFieldData

    xDate = cfg['nowDate'].strftime('%Y-%m-%d')
    x = pdfFieldData.replace('/V ()', '/V (' + name + ')', 1).replace('/V ()', '/V (' + xDate + ')', 1)

    fileFdf = '/tmp/fields.fdf'
    fp = open(fileFdf, 'w')
    print(x, file=fp)
    fp.close()

    filePdf = '/tmp/award.pdf'
    pdfGen = 'pdftk ' + cfg['homedir'] + 'AcknowledgmentForm.pdf fill_form ' + fileFdf + ' output ' + filePdf
    os.system(pdfGen)

    text = cfg['automate']['1st award']['content'].format(name)
    doMail(email, cfg['automate']['1st award']['subject'], text, attach=filePdf)




def handle_mail_miss_you(email, name):
    global cfg

    text = cfg['automate']['we miss you']['content'].format(name)
    doMail(email, cfg['automate']['we miss you']['subject'], text)



def executeLoop(func, xType, xName):
    global autoList

    try:
      for id in autoList[xType][xName]:
        func(id, autoList[xType][xName][id])
    except Exception as e:
      print('ERROR: ' + str(func) + ' failed with ' + str(e))
      return

    del autoList[xType][xName]
    autoList[xType][xName] = {}
    return



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

    cfg['nowDate'] = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    cfg['cutDate'] = cfg['nowDate'] - datetime.timedelta(days=365)
    cfg['1weekDate'] = cfg['nowDate'] - datetime.timedelta(days=7)
    cfg['1monthDate'] = cfg['nowDate'] - datetime.timedelta(days=30)
    cfg['3monthDate'] = cfg['nowDate'] - datetime.timedelta(days=90)
    cfg['1yearDate'] = cfg['nowDate'] - datetime.timedelta(days=365)
    return cfg



def runAutomate():
    global cfg, autoList, mail_pdf_index, pdfFieldData


    automateFile = cfg['homedir'] + 'automateTODO.json'
    autoList = util_load_data_file(automateFile)
    fp = open(cfg['homedir'] + 'AckFields.fdf', 'rb')
    pdfFieldData = "".join(map(chr, fp.read()))
    fp.close()

    #JIX executeLoop(handle_gerrit_abandon, 'gerrit', 'to_abandon_abandon')
    #JIX executeLoop(handle_gerrit_comment, 'gerrit', 'to_abandon_comment')
    #JIX executeLoop(handle_gerrit_review,  'gerrit', 'to_review')
    #JIX executeLoop(handle_bugzilla_comment, 'bugzilla', 'to_unassign_comment')
    #JIX executeLoop(handle_bugzilla_unassign, 'bugzilla', 'to_unassign_unassign')
    #JIX executeLoop(handle_bugzilla_reset_status, 'bugzilla', 'assign_problem_status')
    #JIX executeLoop(handle_bugzilla_reset_user, 'bugzilla', 'assign_problem_user')
    #JIX executeLoop(handle_bugzilla_cc, 'bugzilla', 'missing_cc')
    #JIX executeLoop(handle_bugzilla_ui_cc, 'bugzilla', 'missing_ui_cc')
    executeLoop(handle_mail_miss_you, 'mail', 'we_miss_you_email')
    executeLoop(handle_mail_pdf, 'mail', 'award_1st_email')

    #JIX util_dump_file(automateFile, autoList)


if __name__ == '__main__':
    runCfg(sys.platform)
    runAutomate()
