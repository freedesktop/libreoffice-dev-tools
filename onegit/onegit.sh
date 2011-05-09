#!/usr/bin/env bash

bin_dir=$(dirname "$0")

GIT_BASE=.
GIT_NAME="libo"
REPOS="artwork base calc components extensions extras filters help impress libs-core libs-extern libs-extern-sys libs-gui postprocess sdk testing ure writer"

usage()
{
cat <<EOF
Usage $0 [options] -g <git_base_url>
Options:
   -C       base directory where to create the onegit repo. the default
            is the current working directory, i.e '.'
   -g       base part of the url to access the libreoffice repos
            for example -g "git://anongit.freedesktop.org/libreoffice"
            or -f "/lo/"
            if the url given is a local directory we expect it
            to be the path of bootstrap. the other repos are expected to be in <path>/clone/
   -n       name of the onegit repo to be created. the default is 'libo'
EOF
}

reset_gitignore()
{
cat <<EOF > .gitignore
# backup and temporary files
*~
.*.sw[op]

# where the 'subrepos' and downloads are located
/clone
/src

# the build directories
/*/unxlng??
/*/unxlng??.pro
/*/unxlng???
/*/unxlng???.pro
/*/wntmsc???
/*/wntmsc???.pro
/*/unxmac??
/*/unxmac??.pro
/*/unx?bsd??
/*/unx?bsd??.pro
/*/unxdfly??
/*/unxdfly??.pro
/*/unxso???
/*/unxso???.pro
/*/unxaig??
/*/unxaig??.pro
/solver/*

# autoconf generated stuff
/aclocal.m4
/autom4te.cache
/autogen.lastrun
/bootstrap
/ChangeLog
/config.log
/config.parms
/config.status
/configure
/Makefile
/makefile.mk
/set_soenv
/visibility.cxx
/post_download
/bin/repo-list
/src.downloaded
/ooo.lst
/instsetoo_native/*

# misc
/set_soenv.last
/set_soenv.stamp
/warn
/build.log
/install
/downloaded
/*.Set.sh
/winenv.set.sh
/ID
/tags
/docs
/autogen.save

/*/*.exe

EOF

git add .gitignore
git commit -m "clean-up .gitignore in preparation for unified git repo"

}

while getopts C:g:hn: opt ; do
    case "$opt" in
	C) GIT_BASE="$OPTARG" ;;
	h) usage; exit ;;
	g) REMOTE_GIT_BASE="$OPTARG" ;;
	n) GIT_NAME="$OPTARG" ;;
    esac
done

if [ -z "$REMOTE_GIT_BASE" ] ; then
    echo "Missing -g arguement. use -h for help" 1>&2
    exit 1
fi

if [ ! -d $GIT_BASE ] ; then
    echo "$GIT_BASE is not a directory, please create it before using it" 1>&2
    exit 1
fi

if [ -e "$GIT_BASE/$GIT_NAME" ] ; then
    echo "$GIT_BASE/$GIT_NAME already exist, cannot create a git repo there" 1>&2
    exit 1
fi

cd $GIT_BASE

echo "== clone bootstrap =="

if [ -d "$REMOTE_GIT_BASE" ] ; then
    git clone "$REMOTE_GIT_BASE" $GIT_NAME
    cp -r "$REMOTE_GIT_BASE/src" "$GIT_NAME/."
    REMOTE_GIT_BASE="$REMOTE_GIT_BASE/clone"
else
    git clone "$REMOTE_GIT_BASE/bootstrap" $GIT_NAME
fi

if [ $? -ne 0 ] ; then
    echo "error cloning bootstrap" 1>&2
    exit 1
fi

cd $GIT_NAME


echo "== add repos =="
for repo in $REPOS ; do
    git remote add $repo "$REMOTE_GIT_BASE/$repo"
    if [ $? -ne 0 ] ; then
	echo "error adding $repo" 1>&2
	exit 1
    fi
done

echo "== fetch repos =="
for repo in $REPOS ; do
    git fetch $repo
    if [ $? -ne 0 ] ; then
	echo "error fetching $repo" 1>&2
	exit 1
    fi
done

echo "== clean-up bootstrap .gitignore =="

reset_gitignore

echo "== merges =="

for repo in $REPOS ; do
    git merge -Xours $repo/master
done

echo "== rm repos =="
for repo in $REPOS ; do
    git remote rm $repo
done




