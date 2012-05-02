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

#apply patches between 3c5353256bb94ba99fea94939cf06ba723737c10 and 6a0972ced879259e7f960e7bb852b0e175a05b7a
if test ! `git merge-base ${BUILDCOMMIT} 6a0972ced879259e7f960e7bb852b0e175a05b7a` = 6a0972ced879259e7f960e7bb852b0e175a05b7a
then
if test `git merge-base ${BUILDCOMMIT} 3c5353256bb94ba99fea94939cf06ba723737c10` = 3c5353256bb94ba99fea94939cf06ba723737c10
then
    echo "This is newer than 3c5353256bb94ba99fea94939cf06ba723737c10, cherrypicking." > ${ARTIFACTDIR}/patch.log
    git cherry-pick 6a0972ced879259e7f960e7bb852b0e175a05b7a >> ${ARTIFACTDIR}/patch.log 2>&1
    git cherry-pick 6963de9536cfca1145685a611a6c88c5160d9a1c >> ${ARTIFACTDIR}/patch.log 2>&1
    git rm solenv/gbuild/templates/makefile.mk  >> ${ARTIFACTDIR}/patch.log 2>&1
    git commit -C 6963de9536cfca1145685a611a6c88c5160d9a1c >> ${ARTIFACTDIR}/patch.log 2>&1
    git cherry-pick b1c3e8ae28fcd84c7182f4898c3250e18ed92f1a >> ${ARTIFACTDIR}/patch.log 2>&1
    git rm tail_build/prj/makefile.mk  >> ${ARTIFACTDIR}/patch.log 2>&1
    git rm solenv/inc/gbuildbridge.mk  >> ${ARTIFACTDIR}/patch.log 2>&1
    git commit -C b1c3e8ae28fcd84c7182f4898c3250e18ed92f1a  >> ${ARTIFACTDIR}/patch.log 2>&1
    git cherry-pick 0bd553e8629104fbc37ac574017519b3f3752cb3 >> ${ARTIFACTDIR}/patch.log 2>&1

    if test ! `git merge-base ${BUILDCOMMIT} f3653d3c1e93a7e92a546b770e418b8cf5c06c54` = f3653d3c1e93a7e92a546b770e418b8cf5c06c54
    then
        echo "This is older than f3653d3c1e93a7e92a546b770e418b8cf5c06c54, codemaker is still dmake." >> ${ARTIFACTDIR}/patch.log
        touch codemaker/prj/dmake
    fi
    if test ! `git merge-base ${BUILDCOMMIT} a57b6347999889bbbcf55e704ac480482fdc5497` = a57b6347999889bbbcf55e704ac480482fdc5497
    then
        echo "This is older than a57b6347999889bbbcf55e704ac480482fdc5497, unodevtools is still dmake." >> ${ARTIFACTDIR}/patch.log
        touch unodevtools/prj/dmake
    fi
    if test ! `git merge-base ${BUILDCOMMIT} bed6580ec330fea6bc7ee015adf1baf6298ed3fb` = bed6580ec330fea6bc7ee015adf1baf6298ed3fb
    then
        echo "This is older than bed6580ec330fea6bc7ee015adf1baf6298ed3fb, idlc is still dmake." >> ${ARTIFACTDIR}/patch.log
        touch idlc/prj/dmake
    fi
    if test ! `git merge-base ${BUILDCOMMIT} 5342bc073b6dff059f9e60ad5fea6905752f0f9c` = 5342bc073b6dff059f9e60ad5fea6905752f0f9c
    then
        echo "This is older than 5342bc073b6dff059f9e60ad5fea6905752f0f9c, cpputools is still dmake." >> ${ARTIFACTDIR}/patch.log
        touch cpputools/prj/dmake
    fi
    if test ! `git merge-base ${BUILDCOMMIT} f55eed29c68205f69dd263f8a9657ac407a73ee3` = f55eed29c68205f69dd263f8a9657ac407a73ee3
    then
        echo "This is older than f55eed29c68205f69dd263f8a9657ac407a73ee3, rdbmaker is still dmake." >> ${ARTIFACTDIR}/patch.log
        touch rdbmaker/prj/dmake
    fi
fi
fi

cat <<EOF > autogen.lastrun
--disable-dependency-tracking
--disable-mozilla
--disable-binfilter
--disable-linkoo
--without-junit
--without-help
--without-myspell-dicts
--without-doxygen
--with-external-tar=`readlink -f ${BUILDDIR}/../tarfiles`
EOF

export CCACHE_DIR=`readlink -f ${BUILDDIR}/../ccache`
export CCACHE_BASEDIR=`readlink -f .`
#export CCACHE_PREFIX=distcc
#export DISTCC_HOSTS="localhost/8 192.168.0.103/8 192.168.0.98/16"
unset DISPLAY

ccache -M 8G
# delete outdated cache to keep the cache small (and in RAM)
#find ${CCACHE_DIR} -mmin +120 -type f -delete

./autogen.sh > ${ARTIFACTDIR}/autogen.log 2>&1
git log -1 --pretty=format:"source-hash-%H%n%n" $BUILDCOMMIT > ${ARTIFACTDIR}/commitmsg
git log -1 --pretty=fuller $BUILDCOMMIT >> ${ARTIFACTDIR}/commitmsg
make > ${ARTIFACTDIR}/make.log 2>&1
echo "second try:" >> ${ARTIFACTDIR}/make.log 2>&1
make > ${ARTIFACTDIR}/make.log 2>&1
make dev-install > ${ARTIFACTDIR}/dev-install.log 2>&1
echo "second try:" >> ${ARTIFACTDIR}/make.log 2>&1
make dev-install > ${ARTIFACTDIR}/dev-install.log 2>&1
# shelve away the ccache, just in case
ccache -s > ${ARTIFACTDIR}/ccache.log
#mkdir -p ../ccaches
#cp -a ${CCACHE_DIR} ../ccaches/ccache-`git log -1 --pretty=format:%H`
if test -n `find . -name opt -type d`
then
    mv `find . -name opt -type d` ${ARTIFACTDIR}/opt
    if test -f ${ARTIFACTDIR}/opt/program/soffice
    then
        exit 0
    fi
fi
exit 1
