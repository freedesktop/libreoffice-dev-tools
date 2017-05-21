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
import requests
from requests.auth import HTTPDigestAuth





def util_errorMail(text):
    print(text)
    sendMail = 'mail -r mentoring@libreoffice.org -s "ERROR: esc-automate FAILED" mentoring@libreoffice.org <<EOF\n' + text + '\nPlease have a look at vm174\nEOF\n'
    os.system(sendMail)



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



def doBugzilla(id, command, isComment=False):
    global cfg

    if isComment:
      comment = '/comment'
    else:
      comment = ''
    url = 'https://bugs.documentfoundation.org/rest/bug/' + id + comment + '?api_key=' + cfg['bugzilla']['api-key']
    try:
      if isComment:
        r = requests.post(url, command)
      else:
        r = requests.put(url, command)
      rawData = json.loads(r.text)
      r.close()
    except Exception as e:
      print('Error load url ' + url + ' due to ' + str(e))
      exit(-1)
    if 'code' in rawData:
      raise Exception('code: ' + str(rawData['code']) + ' text: ' + rawData['message'])
    return



def doGerrit(id, command):
    cmd = 'ssh gerrit.libreoffice.org gerrit ' + command + ' ' + id
    r = os.system(cmd)
    if r != 0:
      raise Exception('error: ' + cmd + ' failed')



def doMail(mail, subject, content, attach=None):
    if attach:
      attach = '-a ' + attach + ' '
    else:
      attach = ''
    sendMail = 'mail -r mentoring@libreoffice.org -s "' + subject + '" ' + attach + mail + ' <<EOF\n' + content + '\nEOF\n'
    r = os.system(sendMail)
    if r != 0:
      raise Exception('mail failed')



def handle_gerrit_abandon(id, patchset):
    pid = str(id) + ',' + str(patchset)
    cmd = 'review --abandon --message \'"' + cfg['automate']['gerrit']['abandon'] + '"\''
    doGerrit(pid, cmd)



def handle_gerrit_review(id, row):
    cmd = 'set-reviewers -a  \'"' + row['name'] + '"\''
    doGerrit(id, cmd)
    handle_gerrit_comment(id, row['patchset'], useText='added reviewer')



def handle_gerrit_comment(id, patchset, useText = None):
    pid = str(id) + ',' + str(patchset)
    if useText is None:
      txt = 'A polite ping, ' + cfg['automate']['gerrit']['comment']
    else:
      txt = useText
    cmd = 'review --message \'"' + txt + '"\''
    doGerrit(pid, cmd)



def handle_bugzilla_unassign(id, text):
    handle_bugzilla_reset_user(id, text)
    handle_bugzilla_reset_status(id, text)
    handle_bugzilla_comment(id, text, isPolite=False)



def handle_bugzilla_comment(id, text, isPolite=True):
    if isPolite:
      polite = 'A polite ping, '+ cfg['automate']['bugzilla']['comment']
    else:
      polite = cfg['automate']['bugzilla']['unassign']
    command = '{"comment" : "' + polite + '", "is_private" : false}'
    doBugzilla(id, command, isComment=True)



def handle_bugzilla_reset_status(id, text):
    command = '{"status": "NEW"}'
    doBugzilla(id, command)
    return



def handle_bugzilla_reset_user(id, text):
    command = '{"assigned_to": "libreoffice-bugs@lists.freedesktop.org"}'
    doBugzilla(id, command)



def handle_bugzilla_cc(id, email):
    command = '{"cc": {"add": ["mentoring@documentfoundation.org"]}}'
    doBugzilla(id, command)



def handle_bugzilla_ui_cc(id, email):
    command = '{"cc": {"add": ["libreoffice-ux-advise@lists.freedesktop.org"]}}'
    doBugzilla(id, command)



def handle_mail_pdf(email, name):
    global cfg, pdfFieldData

    xDate = cfg['nowDate'].strftime('%Y-%m-%d')
    x = pdfFieldData.replace('/V ()', '/V (' + xDate + ')', 1).replace('/V ()', '/V (' + name + ')', 1)

    fileFdf = '/tmp/fields.fdf'
    fp = open(fileFdf, 'w')
    print(x, file=fp)
    fp.close()

    filePdf = '/tmp/award.pdf'
    pdfGen = 'pdftk ' + cfg['homedir'] + 'AcknowledgmentForm.pdf fill_form ' + fileFdf + ' output ' + filePdf
    r = os.system(pdfGen)
    if r != 0:
      raise Exception('pdf generation failed ')

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
      util_errorMail('ERROR: ' + str(func) + ' failed with ' + str(e))
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

    executeLoop(handle_gerrit_abandon, 'gerrit', 'to_abandon_abandon')
    executeLoop(handle_gerrit_review,  'gerrit', 'to_review')
    executeLoop(handle_gerrit_comment, 'gerrit', 'to_abandon_comment')
    executeLoop(handle_bugzilla_unassign, 'bugzilla', 'to_unassign_unassign')
    executeLoop(handle_bugzilla_comment, 'bugzilla', 'to_unassign_comment')
    executeLoop(handle_bugzilla_reset_status, 'bugzilla', 'assign_problem_status')
    executeLoop(handle_bugzilla_reset_user, 'bugzilla', 'assign_problem_user')
    executeLoop(handle_bugzilla_cc, 'bugzilla', 'missing_cc')
    executeLoop(handle_bugzilla_ui_cc, 'bugzilla', 'missing_ui_cc')
    executeLoop(handle_mail_miss_you, 'mail', 'we_miss_you_email')
    executeLoop(handle_mail_pdf, 'mail', 'award_1st_email')

    util_dump_file(automateFile, autoList)


if __name__ == '__main__':
    runCfg(sys.platform)
    runAutomate()
