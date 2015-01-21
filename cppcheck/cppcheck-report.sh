#!/usr/bin/env bash
# -*- tab-width : 4; indent-tabs-mode : nil -*-
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

[ "$DEBUG" ] && set -xv

# save stdout and stderr
exec 3>&1 4>&2 >/tmp/foo.log 2>&1

# redirect to log file
exec > /tmp/cppcheck-report.log
exec 2>&1

#
# Functions
#

die()
{
    [ "$DEBUG" ] && set -xv

    MESSAGE="$@"
    echo "Error:" "${MESSAGE?}" >&2
    mail_failure "${MESSAGE?}"
    exit -1;
}

run_cppcheck()
{
    [ "$DEBUG" ] && set -xv

    pushd "${SRC_DIR?}" > /dev/null || die "Failed to change directory to ${SRC_DIR?}"

    echo "unusedFunction" > "${DATA_DIR?}"/cppcheck_supp.txt

    "${CPPCHECK_DIR?}"/cppcheck -i external/ -i workdir/ --xml --suppressions-list="${DATA_DIR?}"/cppcheck_supp.txt --enable=all --max-configs=25 ./ 2> "${DATA_DIR?}"/err.xml \
    || die "Failed to run cppcheck."

    "${CPPCHECK_DIR?}"/htmlreport/cppcheck-htmlreport --file="${DATA_DIR?}"/err.xml --title="LibreOffice ${COMMIT_DATE_LO?} ${COMMIT_TIME_LO?} ${COMMIT_SHA1_LO?}, CppCheck ${COMMIT_DATE_CPPCHECK?} ${COMMIT_TIME_CPPCHECK?} ${COMMIT_SHA1_CPPCHECK?}" --report-dir="${HTML_DIR?}" --source-dir=. \
    || die "Failed to run cppcheck-htmlreport."

    popd > /dev/null || die "Failed to change directory out of ${SRC_DIR?}"
}

get_cppcheck_src()
{
    [ "$DEBUG" ] && set -xv

    if [ ! -d "${CPPCHECK_DIR?}" ]; then
        git clone "${CPPCHECK_GIT_URL?}" "${CPPCHECK_DIR?}" || die "Failed to git clone ${CPPCHECK_GIT_URL?} in ${CPPCHECK_DIR?}"
    else
        if [ ! -d "${CPPCHECK_DIR?}"/.git ] ; then
            die "${CPPCHECK_DIR?} is not a git repository"
        else
            pushd "${CPPCHECK_DIR?}" || die "Failed to change directory to ${CPPCHECK_DIR?}"
            git pull || die "Failed to update git repository ${CPPCHECK_DIR?}"
            popd > /dev/null || die "Failed to change directory out of ${CPPCHECK_DIR?}"
        fi
    fi
}

get_lo_src()
{
    [ "$DEBUG" ] && set -xv

    if [ ! -d "${SRC_DIR?}" ]; then
        git clone "${LO_GIT_URL?}" "${SRC_DIR?}" || die "Failed to git clone ${LO_GIT_URL?} in ${SRC_DIR?}"
    else
        if [ ! -d "${SRC_DIR?}"/.git ] ; then
            die "${SRC_DIR?} is not a git repository"
        else
            pushd "${SRC_DIR?}" || die "Failed to change directory to ${SRC_DIR?}"
            git pull || die "Failed to update git repository ${SRC_DIR?}"
            popd > /dev/null || die "Failed to change directory out of ${SRC_DIR?}"
        fi
    fi
}

build_cppcheck()
{
    [ "$DEBUG" ] && set -xv

    pushd "${CPPCHECK_DIR?}" > /dev/null || die "Failed to change directory to ${CPPCHECK_DIR?}"
    make all || die "Failed to build cppcheck."
    popd > /dev/null || die "Failed to change directory out of ${CPPCHECK_DIR?}"
}

get_commit_lo()
{
    [ "$DEBUG" ] && set -xv

    pushd "${SRC_DIR?}" > /dev/null || die "Failed to change directory to ${SRC_DIR?}"

    COMMIT_SHA1_LO=$(git log --date=iso | head -3 | awk '/^commit/ {print $2}')
    COMMIT_DATE_LO=$(git log --date=iso | head -3 | awk '/^Date/ {print $2}')
    COMMIT_TIME_LO=$(git log --date=iso | head -3 | awk '/^Date/ {print $3}')

    popd > /dev/null || die "Failed to change directory out of ${SRC_DIR?}"
}

get_commit_cppcheck()
{
    [ "$DEBUG" ] && set -xv

    pushd "${CPPCHECK_DIR?}" > /dev/null || die "Failed to change directory to ${CPPCHECK_DIR?}"

    COMMIT_SHA1_CPPCHECK=$(git log --date=iso | head -3 | awk '/^commit/ {print $2}')
    COMMIT_DATE_CPPCHECK=$(git log --date=iso | head -3 | awk '/^Date/ {print $2}')
    COMMIT_TIME_CPPCHECK=$(git log --date=iso | head -3 | awk '/^Date/ {print $3}')

    popd > /dev/null || die "Failed to change directory out of ${CPPCHECK_DIR?}"
}

upload_report()
{
    [ "$DEBUG" ] && set -xv

    ssh upload@dev-builds.libreoffice.org rm -rf "${UPLOAD_DIR?}" || die "Failed to remove directory ${UPLOAD_DIR?}"
    ssh upload@dev-builds.libreoffice.org mkdir -p "${UPLOAD_DIR?}" || die "Failed to create directory ${UPLOAD_DIR?}"
    scp -r "${HTML_DIR?}"/* upload@dev-builds.libreoffice.org:"${UPLOAD_DIR?}"/ || die "Failed to upload report to ${UPLOAD_DIR?}"
}

mail_success()
{
    [ "$DEBUG" ] && set -xv

    which mailx >/dev/null 2>&1
    if [ "$?" = "0" ] ; then

mailx -s "CppCheck Report update" "${MAILTO?}" <<EOF

A new cppcheck report is available at : http://dev-builds.libreoffice.org/cppcheck_reports/master/

This job was run at `date +%Y-%d-%m_%H:%M:%S` with user `whoami` at host `cat /etc/hostname` as $MY_NAME

EOF

    fi
}

mail_failure()
{
    [ "$DEBUG" ] && set -xv
    MESSAGE="$@"

    if [ -f /tmp/cppcheck-report.log ] ; then
        cp -f /tmp/cppcheck-report.log ~/cppcheck-report.log
        rm -f ~/cppcheck-report.log.gz
        gzip ~/cppcheck-report.log
    fi

    which mailx >/dev/null 2>&1
    if [ "$?" = "0" ] ; then

mailx -s "CppCheck Report: Failure" "${MAILTO?}" <<EOF
`uuencode /home/buildslave/cppcheck-report.log.gz /home/buildslave/cppcheck-report.log.gz`

The cppcheck job failed with message: "${MESSAGE?}"

This job was run at `date +%Y-%d-%m_%H:%M:%S` with user `whoami` at host `cat /etc/hostname` as $MY_NAME

EOF

    fi
}

usage()
{
    [ "$DEBUG" ] && set -xv

    # restore stdout and stderr
    exec 1>&3 2>&4

    echo >&2 "Usage: lcov-report.sh -s [DIRECTORY] -w [DIRECTORY]
        -s    source code directory
        -w    html (www) directory
        -c    ccpcheck (git) directory."
    exit 1
}

#
# Main
#

if [ "$#" = "0" ] ; then
    usage
fi

SRC_DIR=
HTML_DIR=
CPPCHECK_DIR=
DATA_DIR=/tmp
CPPCHECK_GIT_URL="git://github.com/danmar/cppcheck.git"
LO_GIT_URL="git://anongit.freedesktop.org/libreoffice/core.git"
UPLOAD_DIR=/srv/www/dev-builds.libreoffice.org/cppcheck_reports/master
MAILTO=libreoffice@lists.freedesktop.org
MY_NAME=`dirname $0`
MESSAGE=

while getopts ":s:w:c:" opt ; do
    case "$opt" in
    s)
        SRC_DIR="${OPTARG?}"
        ;;
    w)
        HTML_DIR="${OPTARG?}"
        ;;
    c)
        CPPCHECK_DIR="${OPTARG?}"
        ;;
    *)
        usage
        ;;
    esac
done


get_lo_src
get_cppcheck_src
get_commit_cppcheck
get_commit_lo
build_cppcheck
run_cppcheck
upload_report
mail_success
