#! /bin/bash
#
# Version: MPL 1.1 / GPLv3+ / LGPLv3+
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License or as specified alternatively below. You may obtain a copy of
# the License at http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# Major Contributor(s):
# [ Copyright (C) 2011 Bjoern Michaelsen (initial developer) ]
#
# All Rights Reserved.
#
# For minor contributions see the git repository.
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 3 or later (the "GPLv3+"), or
# the GNU Lesser General Public License Version 3 or later (the "LGPLv3+"),
# in which case the provisions of the GPLv3+ or the LGPLv3+ are applicable
# instead of those above.
#

SCRIPTDIR=$( cd "$( dirname "$0" )" && pwd )
BUILDDIR=$1
ARTIFACTDIR=$2

cd ${BUILDDIR}

BUILDCOMMIT=`git rev-list -1 HEAD`

cat <<EOF > autogen.lastrun
--disable-dependency-tracking
--disable-option-checking
--without-junit
--without-help
--without-myspell-dicts
--without-doxygen
--disable-gnome-vfs
--disable-odk
--without-system-jpeg
--with-external-tar=`readlink -f ${BUILDDIR}/../tarfiles`
EOF

export CCACHE_DIR=`readlink -f /root/ccache`
export CCACHE_BASEDIR=`readlink -f .`
unset DISPLAY

ccache -M 8G

./autogen.sh > ${ARTIFACTDIR}/autogen.log 2>&1
git log -1 --pretty=format:"source-hash-%H%n%n" $BUILDCOMMIT > ${ARTIFACTDIR}/commitmsg
git log -1 --pretty=fuller $BUILDCOMMIT >> ${ARTIFACTDIR}/commitmsg
make > ${ARTIFACTDIR}/make.log 2>&1
echo "second try:" >> ${ARTIFACTDIR}/make.log 2>&1
make >> ${ARTIFACTDIR}/make.log 2>&1

ccache -s > ${ARTIFACTDIR}/ccache.log
source ${BUILDDIR}/config_host.mk
echo ${INSTDIR} >> ${ARTIFACTDIR}/instdir.log
if test -f "${INSTDIR}/program/soffice"
then
    echo "found install"
    cp -a ${INSTDIR}/ ${ARTIFACTDIR}/opt
else
    make dev-install > ${ARTIFACTDIR}/dev-install.log 2>&1
    echo "second try:" >> ${ARTIFACTDIR}/make.log 2>&1
    make dev-install >> ${ARTIFACTDIR}/dev-install.log 2>&1
    if test -d ${BUILDDIR}/solver/unxlngx6.pro/installation/opt
    then
        INSTDIR=${BUILDDIR}/solver/unxlngx6.pro/installation/opt
        echo "found install"
        mkdir -p ${ARTIFACTDIR}/opt
        cp -a ${INSTDIR}/ ${ARTIFACTDIR}/opt
    else
        echo "no install found"
        exit 1
    fi
fi
exit 0
