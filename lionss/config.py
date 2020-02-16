#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
import os

# Variables for PyLoNS
repo_localpath = '/var/www/git/core'
# Openshift repo_localpath = os.environ['OPENSHIFT_DATA_DIR']+'lo_core'
og_root = 'https://opengrok.libreoffice.org/search?project=core&q='
#~ pattern_prefix, file_selectors, file_splitter
gg_settings = [dict() for x in range(1)]
gg_settings[0] = dict( pattern_prefix = '<property name="label" translatable="yes">',
    hotkey = '_',
    file_selectors = ['*.ui'], 
    text_splitter = '><',
    text_picker = 'fname' )
