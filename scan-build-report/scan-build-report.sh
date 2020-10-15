#!/usr/bin/env bash
# -*- tab-width : 4; indent-tabs-mode : nil -*-
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

[ "$DEBUG" ] && set -xv

# save stdout and stderr
exec 3>&1 4>&2 >/tmp/foo.log

# redirect to log file
exec > /tmp/scan-build-report.log 2>&1

#
# Functions
#


die()
{
	MESSAGE="$*"
	echo "Error: $MESSAGE" >&2
	exit 1;
}

usage()
{
	# restore stdout and stderr
	exec 1>&3 2>&4

	echo >&2 "Usage: scan-build-report -s [SOURCECODE DIRECTORY] -o [OUTPUT DIRECTORY]"
	echo >&2 "-s source code directory"
	echo >&2 "-o output directory"

	exit 1
}

init()
{
	# Check if scan-build is available, and in the right version.
	which scan-build >/dev/null 2>&1 || die "Failed to find 'scan-build'"
	scan-build --help | grep "\--exclude" >/dev/null 2>&1 || die "'scan-build' version does not seem to support the '--exclude' option. Install a newer version of llvm/clang/scan-build (version 9 or higher)."

	# Verify LO_SRC_DIR is set to something.
	if [ -z "$LO_SRC_DIR" -o "$LO_SRC_DIR" = "" -o "$LO_SRC_DIR" = "/" ]
	then
		die "Sourcecode directory not set correctly."
	fi

	# Prepare output directory for the report
	if [ -z "$OUTPUT_DIR" -o "$OUTPUT_DIR" = "" -o "$OUTPUT_DIR" = "/" ]
	then
		die "Output directory for reports 'OUTPUT_DIR' not set correctly."
	fi

	if [ -d "$OUTPUT_DIR" ]
	then
		rm -rf "$OUTPUT_DIR" || die "Failed to remove output directory $OUTPUT_DIR"
		mkdir "$OUTPUT_DIR" || die "Failed to create output directory $OUTPUT_DIR"
	else
		mkdir "$OUTPUT_DIR" || die "Failed to create output directory $OUTPUT_DIR"
	fi
}

get_lo_src()
{
	if [ ! -d "$LO_SRC_DIR" ]
	then
		git clone "$LO_GIT_URL" "$LO_SRC_DIR" || die "Failed to git clone $LO_GIT_URL in $LO_SRC_DIR"
	else
		if [ ! -d "$LO_SRC_DIR"/.git ]
		then
			die "$LO_SRC_DIR is not a git repository"
		else
			pushd "$LO_SRC_DIR" >/dev/null || die "Failed to change directory to $LO_SRC_DIR"
			git pull || die "Failed to update git repository $LO_SRC_DIR"
			popd > /dev/null || die "Failed to change directory out of $LO_SRC_DIR"
		fi
	fi
}

run_scan_build()
{
	pushd "$LO_SRC_DIR" > /dev/null || die "Failed to change directory to $LO_SRC_DIR"

	if [ -f "$LO_SRC_DIR"/Makefile ]
	then
		make clean || die "Failed to run make clean in $LO_SRC_DIR"
	fi

	scan-build --use-cc=clang --use-c++=clang++ ./autogen.sh --disable-ccache --enable-debug --without-system-libs --without-system-headers || die "Failed to run scan-build ./autogen.sh"
	scan-build --use-cc=clang --use-c++=clang++ --html-title="LibreOffice: SHA1=$COMMIT_SHA1, DATE=$COMMIT_DATE, TIME=$COMMIT_TIME" -o "$OUTPUT_DIR" --exclude "$LO_SRC_DIR"/*/UnpackedTarball/* --exclude "$LO_SRC_DIR"/workdir/* --exclude "$LO_SRC_DIR"/instdir/* --exclude "$LO_SRC_DIR"/external/ make	|| die "Failed to run scan-build make"

	mv "$OUTPUT_DIR"/* "$REPORT_FIXED_DIR_NAME" || die "Failed to move $OUTPUT_DIR/* to $REPORT_FIXED_DIR_NAME."

	popd > /dev/null || die "Failed to change directory out of $LO_SRC_DIR"
}

lcov_get_commit()
{
	pushd "$LO_SRC_DIR" > /dev/null || die "Failed to change directory to $LO_SRC_DIR"

	COMMIT_SHA1=$(git log --date=iso | head -3 | awk '/^commit/ {print $2}')
	COMMIT_DATE=$(git log --date=iso | head -3 | awk '/^Date/ {print $2}')
	COMMIT_TIME=$(git log --date=iso | head -3 | awk '/^Date/ {print $3}')

	popd > /dev/null || die "Failed to change directory out of $LO_SRC_DIR"
}





#
# Main
#


export PYTHONIOENCODING=UTF-8

export LANG=en_US.UTF-8
export LC_CTYPE="en_US.UTF-8"
export LC_NUMERIC="en_US.UTF-8"
export LC_TIME="en_US.UTF-8"
export LC_COLLATE="en_US.UTF-8"
export LC_MONETARY="en_US.UTF-8"
export LC_MESSAGES="en_US.UTF-8"
export LC_PAPER="en_US.UTF-8"
export LC_NAME="en_US.UTF-8"
export LC_ADDRESS="en_US.UTF-8"
export LC_TELEPHONE="en_US.UTF-8"
export LC_MEASUREMENT="en_US.UTF-8"
export LC_IDENTIFICATION="en_US.UTF-8"
export LC_ALL="en_US.UTF-8"


LO_GIT_URL=https://gerrit.libreoffice.org/core/

if [ "$#" != "4" ]
then
	usage
fi

while getopts ":s:o:" opt
do
	case "$opt" in
	s)
		LO_SRC_DIR="$OPTARG"
		;;
	o)
		OUTPUT_DIR="$OPTARG"/output/
		REPORT_FIXED_DIR_NAME="$OUTPUT_DIR"/scan-build-report/
		;;
	*)
		usage
		;;
	esac
done


init
get_lo_src
lcov_get_commit
run_scan_build
