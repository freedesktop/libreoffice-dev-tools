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
    echo "Error: ${MESSAGE?}" >&2
    mail_failure "${MESSAGE?}"
    exit -1;
}

run_cppcheck()
{
    [ "$DEBUG" ] && set -xv

    pushd "${LO_SRC_DIR?}" > /dev/null || die "Failed to change directory to ${LO_SRC_DIR?}"

    echo "unusedFunction" > "${DATA_DIR?}"/cppcheck_supp.txt

    "${CPPCHECK_DIR?}"/cppcheck -i external/ -i workdir/ --xml --suppressions-list="${DATA_DIR?}"/cppcheck_supp.txt --enable=all --max-configs=25 ./ 2> "${DATA_DIR?}"/err.xml \
    || die "Failed to run cppcheck."

    "${CPPCHECK_DIR?}"/htmlreport/cppcheck-htmlreport --file="${DATA_DIR?}"/err.xml --title="LibreOffice ${COMMIT_DATE_LO?} ${COMMIT_TIME_LO?} ${COMMIT_SHA1_LO?}, CppCheck ${COMMIT_DATE_CPPCHECK?} ${COMMIT_TIME_CPPCHECK?} ${COMMIT_SHA1_CPPCHECK?}" --report-dir="${HTML_DIR?}" --source-dir=. \
    || die "Failed to run cppcheck-htmlreport."

    popd > /dev/null || die "Failed to change directory out of ${LO_SRC_DIR?}"
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

    if [ ! -d "${LO_SRC_DIR?}" ]; then
        git clone "${LO_GIT_URL?}" "${LO_SRC_DIR?}" || die "Failed to git clone ${LO_GIT_URL?} in ${LO_SRC_DIR?}"
    else
        if [ ! -d "${LO_SRC_DIR?}"/.git ] ; then
            die "${LO_SRC_DIR?} is not a git repository"
        else
            pushd "${LO_SRC_DIR?}" || die "Failed to change directory to ${LO_SRC_DIR?}"
            git pull || die "Failed to update git repository ${LO_SRC_DIR?}"
            popd > /dev/null || die "Failed to change directory out of ${LO_SRC_DIR?}"
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

    pushd "${LO_SRC_DIR?}" > /dev/null || die "Failed to change directory to ${LO_SRC_DIR?}"

    COMMIT_SHA1_LO=$(git log --date=iso | head -5 | awk '/^commit/ {print $2}')
    COMMIT_DATE_LO=$(git log --date=iso | head -5 | awk '/^Date/ {print $2}')
    COMMIT_TIME_LO=$(git log --date=iso | head -5 | awk '/^Date/ {print $3}')

    popd > /dev/null || die "Failed to change directory out of ${LO_SRC_DIR?}"
}

get_commit_cppcheck()
{
    [ "$DEBUG" ] && set -xv

    pushd "${CPPCHECK_DIR?}" > /dev/null || die "Failed to change directory to ${CPPCHECK_DIR?}"

    COMMIT_SHA1_CPPCHECK=$(git log --date=iso | head -5 | awk '/^commit/ {print $2}')
    COMMIT_DATE_CPPCHECK=$(git log --date=iso | head -5 | awk '/^Date/ {print $2}')
    COMMIT_TIME_CPPCHECK=$(git log --date=iso | head -5 | awk '/^Date/ {print $3}')

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

cat > "$EMAIL_BODY" <<EOF

A new cppcheck report is available at : http://dev-builds.libreoffice.org/cppcheck_reports/master/

This job was run at `date +%Y-%d-%m_%H:%M:%S` with user `whoami` at host `cat /etc/hostname` as $MY_NAME $MY_ARGS

EOF


    "$SENDEMAIL" -o message-file="$EMAIL_BODY" -f "$MAILFROM" -t "$MAILTO" -o tls=yes -s smtp.gmail.com:587 -xu cppcheck.libreoffice@gmail.com -xp "$SMTP_PWD" -u "CppCheck Report Update"

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

cat > "$EMAIL_BODY" <<EOF

The cppcheck job failed with message: "${MESSAGE?}"

This job was run at `date +%Y-%d-%m_%H:%M:%S` with user `whoami` at host `cat /etc/hostname` as $MY_NAME $MY_ARGS

EOF

    "$SENDEMAIL" -o message-file="$EMAIL_BODY" -f "$MAILFROM" -t "$MAILTO" -o tls=yes -s smtp.gmail.com:587 -xu cppcheck.libreoffice@gmail.com -xp "$SMTP_PWD" -u "CppCheck Report Failure" -a /home/buildslave/cppcheck-report.log.gz

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

# Set some defaults here
LO_SRC_DIR=~/source/libo-core
HTML_DIR=~/tmp/www
CPPCHECK_DIR=~/source/cppcheck
DATA_DIR=~/tmp
CPPCHECK_GIT_URL="git://github.com/danmar/cppcheck.git"
LO_GIT_URL="git://anongit.freedesktop.org/libreoffice/core.git"
UPLOAD_DIR=/srv/www/dev-builds.libreoffice.org/cppcheck_reports/master
MAILTO=libreoffice@lists.freedesktop.org
MAILFROM=cppcheck.libreoffice@gmail.com
MY_NAME=`readlink -f $0`
MY_ARGS=$@
MESSAGE=
SENDEMAIL=~/source/buildbot/bin/sendEmail
EMAIL_BODY=~/tmp/email_body
# Dont forget to set SMTP_PWD in your ~/.cppcheckrc !
SMTP_PWD=
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
export LC_ALL=en_US.UTF-8

if [ -f ~/.cppcheckrc ]; then
    # override all default vars with entries in ~/.cppcheckrc
    source ~/.cppcheckrc
else
    die "Failed to locate ~/.cppcheckrc"
fi


# override cppcheckrc and defaults with commandline settings
while getopts ":s:w:c:" opt ; do
    case "$opt" in
    s)
        LO_SRC_DIR="${OPTARG?}"
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


if [ ! -f "$SENDEMAIL" ] ; then
    echo "Error: sendEmail command $SENDEMAIL not found." >&2
    exit -1;
fi


get_lo_src
get_cppcheck_src
get_commit_cppcheck
get_commit_lo
build_cppcheck
run_cppcheck
upload_report
mail_success
