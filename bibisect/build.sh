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

BUILDDIR=$1
ARTIFACTDIR=$2

cd ${BUILDDIR}

cat <<EOF > autogen.lastrun
--disable-mozilla
--disable-binfilter
--disable-linkoo
--without-junit
--without-help
--without-myspell-dicts
--with-external-tar=`readlink -f ${BUILDDIR}/../tarfiles`
--with-num-cpus=30
--with-max-jobs=30
EOF

export gb_FULLDEPS=
export CCACHE_DIR=`readlink -f ${BUILDDIR}/../ccache`
export CCACHE_BASEDIR=`readlink -f .`
#export CCACHE_PREFIX=distcc
#export DISTCC_HOSTS="localhost/8 192.168.0.103/8 192.168.0.98/16"
unset DISPLAY

ccache -M 30G
# delete outdated cache to keep the cache small (and in RAM)
find ${CCACHE_DIR} -mmin +120 -type f -delete

./autogen.sh > ${ARTIFACTDIR}/autogen.log 2>&1
git log -1 --pretty=format:"source-hash-%H%n%n" > ${ARTIFACTDIR}/commitmsg
git log -1 --pretty=fuller >> ${ARTIFACTDIR}/commitmsg
make > ${ARTIFACTDIR}/make.log 2>&1
make dev-install > ${ARTIFACTDIR}/dev-install.log 2>&1
# shelve away the ccache, just in case
ccache -s > ${ARTIFACTDIR}/ccache.log
mkdir -p ../ccaches
cp -a ${CCACHE_DIR} ../ccaches/ccache-`git log -1 --pretty=format:%H`
if test -n `find . -name opt -type d`
then
    mv `find . -name opt -type d` ${ARTIFACTDIR}/opt
    if test -f ${ARTIFACTDIR}/opt/program/soffice
    then
        exit 0
    fi
fi
exit 1
