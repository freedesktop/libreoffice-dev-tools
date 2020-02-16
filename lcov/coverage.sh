#!/bin/bash

# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

# Run this script in the toplevel directory of a LibreOffice checkout.

coverage()
{
    srcmodule="$1"
    srcdir="$2"
    srcfiles="$3"
    testmodule="$4"
    tests="$5"

    set -ex
    rm -rf workdir/CxxObject/$srcmodule/$srcdir/$srcfiles.{gcda,gcno} libreoffice.info coverage
    cd $srcmodule
    touch $srcdir/$srcfiles
    make -sr -j$parallelism gb_GCOV=YES
    cd ../$testmodule
    make -sr -j$parallelism $tests
    cd ..
    lcov --directory workdir/CxxObject/$srcmodule/$srcdir --capture --output-file libreoffice.info
    genhtml -o coverage libreoffice.info
}

parallelism=$(make -s cmd cmd='echo $(PARALLELISM)'|tail -n 1)

case "$1" in
    sw_docxexport)
        # Writer DOCX export
        coverage sw source/filter/ww8 'docx*' sw CppunitTest_sw_ooxmlexport
    ;;
    sw_rtfimport)
        # Writer RTF import
        coverage writerfilter source/rtftok '*' sw 'CppunitTest_sw_rtfimport CppunitTest_sw_rtfexport CppunitTest_sw_rtfexport2 CppunitTest_sw_rtfexport3'
    ;;
    sw_rtfpaste)
        # Writer RTF paste
        coverage sw source/filter/rtf '*' sw CppunitTest_sw_uiwriter
    ;;
    sw_rtfexport)
        # Writer RTF export
        coverage sw source/filter/ww8 'rtf*' sw 'CppunitTest_sw_rtfexport CppunitTest_sw_rtfexport2 CppunitTest_sw_rtfexport3 CppunitTest_sw_uiwriter'
    ;;
    sw_epubexport)
        # Writer EPUB export
        rm -rf workdir/CxxObject/writerperfect/source/writer/exp/*.{gcda,gcno}
        touch writerperfect/source/writer/exp/*
        coverage writerperfect source/writer/ 'EPUB*' writerperfect 'CppunitTest_writerperfect_epubexport UITest_writerperfect_epubexport'
    ;;
    *)
        echo "Unknown code area. The currently supported ones are:"
        echo
        echo "sw_docxexport"
        echo "sw_rtfexport"
        echo "sw_rtfimport"
        echo "sw_rtfpaste"
        echo "sw_epubexport"
    ;;
esac

# vi:set shiftwidth=4 expandtab:
