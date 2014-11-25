#!/bin/bash

# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

# Run this script in the toplevel directory of a LibreOffice checkout.

scan()
{
    srcmodule="$1"
    srcdir="$2"
    srcfiles="$3"

    set -ex
    rm -rf scan-build
    mkdir scan-build
    (cd $srcmodule && touch $srcdir/$srcfiles)
    scan-build --use-cc=clang --use-c++=clang++ -o $(pwd)/scan-build make $srcmodule
}

parallelism=$(make -s cmd cmd='echo $(PARALLELISM)'|tail -n 1)

case "$1" in
    sw_docxexport)
        # Writer DOCX export
        scan sw source/filter/ww8 'docx*'
    ;;
    sw_rtfimport)
        # Writer RTF import
        scan writerfilter source/rtftok '*'
    ;;
    sw_rtfpaste)
        # Writer RTF paste
        scan sw source/filter/rtf '*'
    ;;
    sw_rtfexport)
        # Writer RTF export
        scan sw source/filter/ww8 'rtf*'
    ;;
    *)
        echo "Unknown code area. The currently supported ones are:"
        echo
        echo "sw_docxexport"
        echo "sw_rtfexport"
        echo "sw_rtfimport"
        echo "sw_rtfpaste"
    ;;
esac

# vi:set shiftwidth=4 expandtab:
