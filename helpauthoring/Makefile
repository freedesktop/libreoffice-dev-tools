# -*- Mode: makefile-gmake; tab-width: 4; indent-tabs-mode: t -*-
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

default:
	VER=`grep '<version' description.xml | sed -e 's/^.*value="//' -e 's/".*//'` ; \
	    rm -f dist/HelpAuthoring-$$VER.oxt ; \
	    zip -r dist/HelpAuthoring-$$VER.oxt . -x '*.oxt' '.*.sw*' '*.xcf' '*.svg' 'Makefile'

# vim: set noet:
