#!/usr/bin/env bash

bin_dir=$(dirname "$0")
pushd "${bin_dir}" > /dev/null
bin_dir=$(pwd)
popd > /dev/null

GIT_BASE=$(pwd)
GIT_NAME="libo"
GIT_TEMP=${GIT_BASE}/gittemp

batch="[main]"
die()
{
    echo "*** $(date +'%Y-%m-%d-%H:%M:%S') $batch $@" | tee -a ${GIT_BASE?}/onegit.msgs >&2
    exit 1
}

log()
{
    echo "=== $(date +'%Y-%m-%d-%H:%M:%S') $batch $@" | tee -a ${GIT_BASE?}/onegit.msgs >&2
}

usage()
{
cat <<EOF
Usage $0 [options] -g <git_base_url>
Options:
   -a       Just apply the patches (this need to be after -C and -n if they are specified)
   -C       base directory where to create the onegit repo. the default
            is the current working directory, i.e '.'
   -g       base part of the url to access the libreoffice repos
            for example -g "https://git.libreoffice.org" or -f "/lo/"
            if the url given is a local directory we expect it
            to be the path of bootstrap. the other repos are expected to be in <path>/clone/
   -n       name of the onegit repo to be created. the default is 'libo'
   -t       temp directory (default the one given by -C + /gittemp). we need a few GB
EOF

}

merge_generic()
{
local r="$1"

(
    flock -x 200
    pushd ${GIT_BASE?}/${GIT_NAME?} > /dev/null

    log "merge $r into onegit"
    git remote add $r "${GIT_TEMP?}/$r" || die "Error adding remote ${GIT_TEMP?}/$r"
    git fetch $r || die "Error fetching $r"
    git fetch --tags $r || die "Error fetching tags from $r"
    git merge -Xours $r/master || die "Error merging $r/master"
    git remote rm $r || die "Error removing remote $r/master"

    popd > /dev/null # GIT_BASE/GIT_NAME
) 200> /tmp/ongit.lockfile
    log "done merging $r"
}

process_generic()
{
local r=$1
shift
local s=$1
shift
local extra=$@

    pushd ${GIT_TEMP?} > /dev/null || die "Error cd-ing to ${GIT_TEMP?}"

    log "fast-import of $r"
    mkdir $r
    pushd $r  > /dev/null || die "Error cd-ing to $r"
    git init
    (cd "${SOURCE_GIT_BASE?}/$s" && git fast-export --signed-tag=strip --branches --tags ) | lo_git_rewrite --prefix "$r:" $extra | git fast-import
    git reset --hard > /dev/null
    for oldtag in $(git tag) ; do git tag "${r}_${oldtag}" "$oldtag" ; git tag -d "${oldtag}" > /dev/null ; done

    log "git gc of $r"
    git gc --prune=now --aggressive || die "Error during git-gc of $r"
    popd > /dev/null # $r

    popd > /dev/null # GIT_TEMP
    log "Done generic processing for $r"
}

merge_bootstrap()
{
    pushd ${GIT_BASE?} > /dev/null
    log "clone bootstrap to onegit"
    git clone "${GIT_TEMP?}/bootstrap" ${GIT_NAME?} || die "Error cloning ${GIT_TEMP?}/bootstrap"

    cp -r "${SOURCE_GIT_BASE?}/src" "${GIT_NAME?}/."

    pushd ${GIT_NAME?} > /dev/null || die "Error cd-ing to $(pwd)/${GIT_NAME?}"
    mkdir clone || die "Error creating $(pwd)/clone directory"
    popd > /dev/null # GIT_NAME

    popd > /dev/null # GIT_BASE
    log "Done merging bootstrap"
}

process_batch1()
{
    batch="[batch1]"

    process_generic bootstrap "."
    merge_bootstrap

    process_generic ure clone/ure
    merge_generic ure

    process_generic calc clone/calc
    merge_generic calc

    process_generic sdk clone/sdk
    merge_generic sdk

    process_generic extras clone/extras
    merge_generic extras

    process_generic impress clone/impress --exclude-suffix "/wntmsci10"
    merge_generic impress

    process_generic artwork clone/artwork --exclude-module external_images
    merge_generic artwork

    process_generic extensions clone/extensions --buffer-size 80
    merge_generic extensions

    # deal with still separate repos, purely untouched like help or translations
    pushd ${GIT_BASE?}/${GIT_NAME?}/clone > /dev/null || die "Error cd.ing to ${GIT_BASE}/${GIT_NAME}/clone from $(pwd)"
    log "clone help"
    git clone "${SOURCE_GIT_BASE?}/clone/help" help || die "Error cloning ${SOURCE_GIT_BASE?}/clone/help"
    log "Done cloning help"

    log "clone transations"
    git clone "${SOURCE_GIT_BASE?}/clone/translations" translations || die "Error cloning ${SOURCE_GIT_BASE?}/clone/translations"
    log "Done cloning translations"
    popd > /dev/null # GIT_BASE/GIT_NAME/clone


    log "Done processing batch1"
}

process_batch2()
{
    batch="[batch2]"

    process_generic writer clone/writer
    merge_generic writer

    process_generic base clone/base
    merge_generic base

    process_generic filters clone/filters --exclude-module binfilter
    merge_generic filters

    process_generic binfilter clone/filters --filter-module binfilter
    log "clone binfilter"
    pushd ${GIT_BASE}/${GIT_NAME?}/clone > /dev/null || die "Error cd-ing to ${GIT_NAME}/clone"
    git clone "${GIT_TEMP?}/binfilter" binfilter || die "Error cloning ${GIT_TEMP?}/binfilter"
    popd > /dev/null # GIT_BASE/GIT_NAME/clone
    log "Done merging binfilter"

    log "Done processing batch2"
}

process_batch3()
{
    batch="[batch3]"

    process_generic libs-gui clone/libs-gui --exclude-suffix "/wntmsci10"
    merge_generic libs-gui

    process_generic components clone/components
    merge_generic components

    process_generic testing clone/testing
    merge_generic testing

    process_generic libs-extern-sys clone/libs-extern-sys --exclude-module dictionaries --exclude-download --buffer-size 80
    merge_generic libs-extern-sys

    process_generic libs-extern clone/libs-extern --exclude-download
    merge_generic libs-extern

    process_generic dictionaries clone/libs-extern-sys --filter-module dictionaries --buffer-size 80

    pushd ${GIT_BASE?}/${GIT_NAME?}/clone > /dev/null || die "Error cd.ing to ${GIT_BASE}/${GIT_NAME}/clone from $(pwd)"
    log "clone dictionaries"
    git clone "${GIT_TEMP?}/dictionaries" dictionaries || die "Error cloning ${GIT_TEMP?}/dictionaries"
    log "Done cloning dictionnaries"
    popd > /dev/null # GIT_BASE/GIT_NAME/clone



    log "Done processing batch3"
}

process_batch4()
{
    batch="[batch4]"

    process_generic libs-core clone/libs-core --exclude-suffix "/wntmsci10"
    merge_generic libs-core

    process_generic postprocess clone/postprocess
    merge_generic postprocess

    log "Done processing batch4"
}

apply_patches()
{
    pushd ${GIT_BASE?}/${GIT_NAME?} > /dev/null || die "Error cd-ing to ${GIT_BASE}/${GIT_NAME}"
    for p in $(ls -1 ${bin_dir}/patches) ; do
	log "Apply patch $p"
	(cat ${bin_dir}/patches/$p | git am -k ) || die "Error applying the patch"
    done
    popd > /dev/null
}

##### main

while getopts aC:g:hn:t: opt ; do
    case "$opt" in
	a) aply_patches; exit ;;
        C) GIT_BASE="$OPTARG" ;;
        g) SOURCE_GIT_BASE="$OPTARG" ;;
        h) usage; exit ;;
        n) GIT_NAME="$OPTARG" ;;
	t) GIT_TEMP="$OPTARG" ;;
    esac
done

# make sure we have a directory to work in (out new git repos will be created there,
# and our workdir for temporary repos
if [ ! -d ${GIT_BASE?} ] ; then
    die "$GIT_BASE is not a directory, please create it before using it"
fi
cat /dev/null > ${GIT_BASE?}/onegit.msgs


# make sure we have a location for the source repos
if [ -z "$SOURCE_GIT_BASE" ] ; then
    die "Missing -g arguement. use -h for help"
fi
if [ ! -d "${SOURCE_GIT_BASE?}" ] ; then
    die "$SOURCE_GIT_BASE is not a directory"
fi

# preferably our target core repo does not exist already
if [ -e "${GIT_BASE?}/${GIT_NAME?}" ] ; then
    die "$GIT_BASE/$GIT_NAME already exist, cannot create a git repo there"
fi

#check that lo_git_rewrite is built
if [ ! -x "${bin_dir?}/../lo_git_rewrite/lo_git_rewrite" ] ; then
    die "${bin_dir?}/../lo_git_rewrite/lo_git_rewrite need to be build"
else
    export PATH="$PATH:${bin_dir?}/../lo_git_rewrite/"
fi

if [ ! -d "${GIT_TEMP?}" ] ; then
    log "create a temporary workarea ${GIT_TEMP?}"
    mkdir "${GIT_TEMP?}" || die "Error creating directory ${GIT_TEMP?}"
fi

log "Start OneGit conversion"

(process_batch1)&
p_batch1=$!

(process_batch2)&
p_batch2=$!

(process_batch3)&
p_batch3=$!

(process_batch4)&
p_batch4=$!

result=0
wait $p_batch1 || result=1
wait $p_batch2 || result=1
wait $p_batch3 || result=1
wait $p_batch4 || result=1

if [ $result -ne 0 ] ; then
    exit $result
fi

log "Tag new repos"

pushd ${GIT_BASE?}/${GIT_NAME?} > /dev/null || die "Error cd-int to ${GIT_BASE}/${GIT_NAME} to tag"
git tag -m "OneGit script applied" MELD_LIBREOFFICE_REPOS || die "Error applying tag on core"

pushd clone/translations > /dev/null
git tag -m "OneGit script applied" MELD_LIBREOFFICE_REPOS || die "Error applying tag on translations"
popd > /dev/null # clone/translation

pushd clone/binfilter > /dev/null
git tag -m "OneGit script applied" MELD_LIBREOFFICE_REPOS || die "Error applying tag on binfilter"
popd > /dev/null # clone/binfilter

pushd clone/help > /dev/null
git tag -m "OneGit script applied" MELD_LIBREOFFICE_REPOS || die "Error applying tag on help"
popd > /dev/null # clone/help

pushd clone/dictionaries > /dev/null
git tag -m "OneGit script applied" MELD_LIBREOFFICE_REPOS || die "Error applying tag on help"
popd > /dev/null # clone/dictionaries

log "Apply patches"
apply_patches

popd > /dev/null # GIT_BASE/GIT_NAME

log "OneGit conversion All Done."

