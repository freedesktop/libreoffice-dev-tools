#!/usr/bin/env python
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import macroparser

def runParser (buf):
    mparser = macroparser.MacroParser(buf)
    mparser.debug = True
    mparser.parse()

def main ():
    buf = 'FOO   (asdfsdaf)'
    runParser(buf)
    buf = 'FOO (x, y)  (x) + (y)'
    runParser(buf)
    buf = 'FOO(x, y)  (x) + (y)'
    runParser(buf)


if __name__ == '__main__':
    main()
