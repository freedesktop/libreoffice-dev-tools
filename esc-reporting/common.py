#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

from subprocess import Popen, PIPE
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def sendMail(cfg, mail, subject, content, attachFile=None):
    msg = MIMEMultipart()
    msg["From"] = "mentoring@documentfoundation.org"
    msg["To"] = mail

    if cfg['mail']['bcc']:
        msg["Bcc"] = cfg['mail']['bcc']

    msg["Subject"] = subject

    msg.attach(MIMEText(content))

    if attachFile:
        fp = open(attachFile['path'], 'rb')
        attach = MIMEApplication(fp.read(), attachFile['extension'])
        fp.close()
        attach.add_header('Content-Disposition','attachment; filename="{}"'.format(attachFile['name']))
        msg.attach(attach)

    p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
    output, error = p.communicate(msg.as_string().encode('ascii'))
    return error

def util_errorMail(cfg, fileName, text):
    print(text)
    subject = "ERROR: " + fileName + " FAILED"
    message = text + '\nPlease have a look at vm174'
    sendMail(cfg, 'mentoring@documentfoundation.org', subject, message)
