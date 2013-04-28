#!/usr/bin/env bash
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# creates a working submodule based checkout using using bundles
function usage {
    cat << EOF
Usage:
$0 -h|--help|-?
$0 [-d downloaddir] [-t targetdir] [SUBMODULES]
$0 -a [-d downloaddir] [-t targetdir] SUBMODULES

    -h,--help,-? show this help
    -d <path>    download directory, defaults to working directory
                 (»$download_dir«) - tries to use existing bundle files
                 in this directory before downloading them
                 (directory must exist)
    -t <path>    target directory, defaults to »$target_dir« (directory must
		 not yet exist unless used with -a, then an existing directory
                 must be specified)
    -a           add submodules to an existing checkout without
                 submodules (be careful with that one)
    SUBMODULES   the submodules to include.
        none            only download the core repository (default)
        all             include dictionaries, helpcontent2 and translations
        h[elpcontent2]  helpcontent2 (can be combined)
        d[ictionaries]  dictionaries (can be combined)
        t[ranslations]  translations (can be combined)

As relative paths are used when using this script, the resulting directory can be
moved around at will without breaking git's references.

Examples:
    »$0 h d«
Setup the repository in »$target_dir« with the helpcontent2 and dictionaries
submodules, downloads go to the current working directory

    »$0 -d /path/to/directory all«
Setup the repository in »$target_dir« with all submodules (dictionaries,
helpcontent2, translations), downloads are looked for/stored in
/path/to/directory

    »$0 -t /desired/path«
Setup the repository in »/desired/path« with no submodules.

    »$0 -a -t /existing/checkout translations«
Add the translations submodule to the existing git checkout in /existing/checkout
Only use this one if you didn't initialize the specified submodules with git already.
EOF
    exit 0
}

bundleurl="http://dev-www.libreoffice.org/bundles"

#defaults
target_dir="libo-core"
download_dir="."
core=true
dictionaries=false
help=false
translations=false
add_to_existing=false
superrepo="libo"

function download {
    if ${!1}; then
        cd "$download_dir"
        wget -nc "$bundleurl/libreoffice-$1.tar.bz2"
        cd "$workdir"
    fi
}
function checkout {
    if ${!1}; then
        reponame=$1
        repodir=${2:-$1}
        echo "extracting $1"
        tar -xjf "$download_dir/libreoffice-$reponame.tar.bz2"
        echo "checking out files"
        cd "$repodir"
        git checkout -- .
        cd "$workdir"
    fi
}
function submodulesetup {
        if ${!1}; then
        reponame=$1
        directory=${2:-$1}
        echo "setting up submodule for $directory"
        cd "$workdir"
        rmdir $superrepo/$directory
        mv $reponame/.git $superrepo/.git/modules/$directory
        mv $reponame $superrepo/$directory
        echo "gitdir: ../.git/modules/$directory" > $superrepo/$directory/.git
        sed -e "/logallrefupdates/a\\\tworktree = ../../../$directory" -e 's#anongit\.freedesktop\.org/libreoffice/#gerrit.libreoffice.org/#' -i $superrepo/.git/modules/$directory/config
        cat <<EOF >> $superrepo/.git/config
[submodule "$directory"]
	url = git://gerrit.libreoffice.org/$reponame
EOF
        cd "$workdir"
    fi
}
##
# commandline options
while [ "${1:-}" != "" ] ; do
    case "$1" in
        -h|--help|-\?) usage;;
        -a) add_to_existing=true core=false;;
        -d) shift; download_dir="$1";;
        -t) shift; target_dir="$1";;
        all)dictionaries=true ; help=true; translations=true;;
        h*) help=true;;
        d*) dictionaries=true;;
        t*) translations=true;;
        none) ;;
        *) echo "Invalid argument: $1 Run the »$0 -h« for help"; exit 1;;
    esac
    shift
done

currentdir=$(pwd)
if $add_to_existing ; then
    if [ ! -e "$target_dir" ] ; then
        echo "target directory »$target_dir« does not exist, cannot add to it - aborting"
        exit 1
    else
        cd $target_dir
        superrepo=$(pwd)
        cd $currentdir
    fi
elif [ -e "$target_dir" ] ; then
    echo "target directory »$target_dir« exists - aborting"
    exit 1
fi

workdir=$(mktemp -d --tmpdir="$currentdir" git_from_bundle_XXX)
if [ -z "$workdir" ] ; then
    echo "creating workdir failed - trying in temporary directory"
    workdir=$(mktemp -d --tmpdir git_from_bundle_XXX)
    if [ -z "$workdir" ] ; then echo "giving up "; exit 1; fi
fi

set -e
cd "$download_dir"
download_dir=$(pwd)
cd "$workdir"
# fetch all bundles at once, so network is only needed once
download "core"
download "dictionaries"
download "help"
download "translations"

checkout "core" "libo"
if [ ! -d $superrepo/.git/modules ] ; then mkdir $superrepo/.git/modules ; fi

checkout "dictionaries"
submodulesetup "dictionaries"

checkout "help"
submodulesetup "help" "helpcontent2"

checkout "translations"
submodulesetup "translations"

cd "$currentdir"
if ! $add_to_existing ; then mv "$workdir/libo" "$target_dir" ; fi

rmdir "$workdir" || ( echo "could not clean up?! delete »$workdir« manually please" ; exit 1 )

echo "verifying setup - git should not report any problems"
cd "$target_dir"
git status
git submodule status

cd $currentdir
echo "everything done - your clone is in »$target_dir«"
echo "do »git pull« (and »git submodule update«) to get the latest changes"
