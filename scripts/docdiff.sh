#!/bin/sh
########################################################################
#
#  Copyright (c) 2010 Thorsten Behrens, Miklos Vajna
#  
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation
#  files (the "Software"), to deal in the Software without
#  restriction, including without limitation the rights to use,
#  copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following
#  conditions:
#  
#  The above copyright notice and this permission notice shall be
#  included in all copies or substantial portions of the Software.
#  
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#  OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#  NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#  OTHER DEALINGS IN THE SOFTWARE.
#
#  This little hack is much inspired by Caolan McNamara's original
#  OpenOffice.org convwatch work
#
########################################################################

# check for required gs
which gs >/dev/null 2>&1 || { 
	echo "need gs"; exit 1 
}

# check for required imagemagick tools
which composite >/dev/null 2>&1 || { 
	echo "need imagemagick's composite"; exit 1 
}
which identify >/dev/null 2>&1 || { 
	echo "need imagemagick's identify"; exit 1 
}

usage ()
{
echo "Usage: $0 [options] <input1>.ps <input2>.ps"
echo ""
echo "Generates graphical comparison between input1 & input2"
echo "and outputs count of different pixel values to stdout"
echo ""
echo "Options:"
echo "-r<num>    Set image resolution to <num> dpi (defaults to 75)"
echo "-t<tmpdir> Set tmpdir location to use (defaults to /tmp)"
echo "-s         Sort output by number of increasing differences"
echo "-k         Keep temp images"
echo "-h         This help information"
echo "-q         Be quiet"
}

RES=75
TMP=/tmp
SORT=cat
GS="gs"

# Parse command line options
while getopts r:t:skhq opt ; do
	case "$opt" in
		r) RES="$OPTARG" ;;
		t) TMP="$OPTARG" ;;
		s) SORT="sort -n -k2,2" ;;
		k) KEEP=1 ;;
		q) QUIET=1; GS="gs -q";;
		h) usage; exit ;;
		?) usage; exit ;;
	esac
done

shift $(($OPTIND - 1))

mkdir $TMP/$$.cmpdir

test -z "$QUIET" && echo "Generating bitmap renderings of $1 ..."
$GS -dNOPROMPT -dBATCH -sDEVICE=jpeg -r$RES -dNOPAUSE -sOutputFile=$TMP/$$.cmpdir/file1.%04d.jpeg $1

test -z "$QUIET" && echo "Generating bitmap renderings of $2 ..."
$GS -dNOPROMPT -dBATCH -sDEVICE=jpeg -r$RES -dNOPAUSE -sOutputFile=$TMP/$$.cmpdir/file2.%04d.jpeg $2

test -z "$QUIET" && echo "Generating differences..."
for file in $TMP/$$.cmpdir/file1.*; do test -z "$QUIET" && echo -n "$file: "; num=`echo $file | sed -e ' s/.*\.\(.*\)\..*/\1/'`; composite -compose difference $file $TMP/$$.cmpdir/file2.$num.jpeg - | identify -format %k -; done | $SORT

if test -n "$KEEP"; then
	echo "Keeping temp images at $TMP/$$.cmpdir" >&2
else
    rm -rf $TMP/$$.cmpdir
fi
