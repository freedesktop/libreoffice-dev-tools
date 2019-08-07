#!/usr/bin/env python3
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import common
from datetime import date

data = {
    'bugzilla' : {
        'fileName' : '/tmp/bugzilla_report.txt',
        'emails': []
        },
    'users' : {
        'fileName' : '/tmp/bugzilla_users_report.txt',
        'emails': []
        },
}
def sendReports():
    for k, v in data.items():
        with open(v['fileName'], 'r') as content_file:
            text = content_file.read()

            for email in v['emails']:
                common.sendMail({'mail': {'bcc': None}}, email,
                        'Bugzilla Report from ' + date.today().strftime("%y/%m/%d"), text, None)

if __name__ == '__main__':
    sendReports()
