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
   -C       base directory where to create the onegit repo. the default
            is the current working directory, i.e '.'
   -g       base part of the url to access the libreoffice repos
            for example -g "git://anongit.freedesktop.org/libreoffice"
            or -f "/lo/"
            if the url given is a local directory we expect it
            to be the path of bootstrap. the other repos are expected to be in <path>/clone/
   -n       name of the onegit repo to be created. the default is 'libo'
   -t       temp directory (default the one given by -C + /gittemp). we need a few GB
EOF

}

merge_generic()
{
local r="$1"

    pushd ${GIT_BASE?}/${GIT_NAME?} > /dev/null

    log "merge $r into onegit"
    git remote add $r "${GIT_TEMP?}/$r" || die "Error adding remote ${GIT_TEMP?}/$r"
    git fetch $r || die "Error fetching $r"
#    git fetch -t $r
    git merge -Xours $r/master || die "Error merging $r/master"
    git remote rm $r || die "Error removing remote $r/master"

    popd > /dev/null # GIT_BASE/GIT_NAME
    log "done merging $r"
}

process_generic()
{
local r=$1

    pushd ${GIT_TEMP?} > /dev/null || die "Error cd-ing to ${GIT_TEMP?}"

    log "clone a copy of $r"
    git clone "${REMOTE_GIT_AUX_BASE?}/$r" $r || die "Errro cloning  $REMOTE_GIT_AUX_BASE/$r"

    log "generic processing for $r"
    pushd $r  > /dev/null || die "Error cd-ing to $r"
    for oldtag in $(git tag) ; do git tag "${r}_${oldtag}" "$oldtag" ; git tag -d "${oldtag}" > /dev/null ; done
    git filter-branch --prune-empty --tag-name-filter cat --tree-filter 'git ls-files | clean_spaces -p 1 ' -- --all || die "Error filtering $r"

    log "git gc of $r"
    git gc --prune=now --aggressive || die "Error during git-gc of $r"
    popd > /dev/null # $r

    popd > /dev/null # GIT_TEMP
    log "Done generic processing for $r"
}

process_generic_mp()
{
local r=$1

    pushd ${GIT_TEMP?} > /dev/null || die "Error cd-ing to ${GIT_TEMP?}"

    log "clone a copy of $r"
    git clone "${REMOTE_GIT_AUX_BASE?}/$r" $r || die "Errro cloning  $REMOTE_GIT_AUX_BASE/$r"

    log "generic processing_mp for $r"
    pushd $r  > /dev/null || die "Error cd-ing to $r"
    for oldtag in $(git tag) ; do git tag "${r}_${oldtag}" "$oldtag" ; git tag -d "${oldtag}" > /dev/null ; done
    git filter-branch --prune-empty --tag-name-filter cat --tree-filter 'git ls-files | clean_spaces ' -- --all || die "Error filtering $r"

    log "git gc of $r"
    git gc --prune=now --aggressive || die "Error during git-gc of $r"
    popd > /dev/null # $r

    popd > /dev/null # GIT_TEMP
    log "Done generic mp processing for $r"
}

process_light()
{
local r=$1

    pushd ${GIT_TEMP?} > /dev/null || die "Error cd-ing to ${GIT_TEMP?}"

    log "clone a copy of $r"
    git clone "${REMOTE_GIT_AUX_BASE?}/$r" $r || die "Errro cloning  $REMOTE_GIT_AUX_BASE/$r"

    log "light processing for $r"
    pushd $r > /dev/null || die "Error cd-ing to $r"
    for oldtag in $(git tag) ; do git tag "${r}_${oldtag}" "$oldtag" ; git tag -d "${oldtag}" > /dev/null ; done

    log "git gc of $r"
    git gc --prune=now --aggressive
    popd > /dev/null # $r

    popd > /dev/null # GIT_TEMP
    log "Done light processing for $r"
}


process_bootstrap()
{
    pushd ${GIT_TEMP?} > /dev/null || die "Error cd-ing to ${GIT_TEMP?}"

    log "clone a copy of bootstrap"
    if [ -d "${REMOTE_GIT_BASE?}" ] ; then
        git clone "${REMOTE_GIT_BASE?}" bootstrap || die "Errro cloning  $REMOTE_GIT_BASE"
    else
        git clone "${REMOTE_GIT_AUX_BASE?}/bootstrap" bootstrap || die "Errro cloning  $REMOTE_GIT_AUX_BASE"
    fi
    log "processing for bootstrap"
    pushd bootstrap > /dev/null || die "Error cd-ing to bootstrap"
    git filter-branch --prune-empty --tag-name-filter cat --tree-filter 'git ls-files | clean_spaces -p 1' -- --all || die "Error filtering bootstrap"
    log "git gc of bootstrap"
    git gc --prune=now --aggressive || die "Error during git-gc of bootstrap"
    popd > /dev/null # bootstrap

    popd > /dev/null # GIT_TEMP
    log "Done processing for bootstrap"
}

process_filters()
{
    pushd ${GIT_TEMP?} > /dev/null || die "Error cd-ing to ${GIT_TEMP?}"

    log "clone a copy of filters"
    git clone "${REMOTE_GIT_AUX_BASE?}/filters" filters-base || die "Error cloning $REMOTE_GIT_AUX_BASE/filters"
    git clone filters-base filters-no-binfilter || die "Error cloning filters-base"
    git clone filters-base filters-binfilter-only  || die "Error cloning filters-base"
    log "filter out binfilter from filters"
    pushd filters-no-binfilter > /dev/null || die "cd-ing to filters-no-binfilter"
    log "filter-out binfilter"
    git filter-branch --prune-empty --tag-name-filter 'xargs -I{} echo "filters_{}"' --index-filter 'git rm -q -r --cached --ignore-unmatch  binfilter' -- --all && ( git tag | grep -v "filters_" | xargs -n 1 git tag -d > /dev/null ) || die "Error filtering out binfilter"
    git filter-branch -f --prune-empty --tag-name-filter cat --tree-filter 'git ls-files | clean_spaces -p 1' -- --all || die "Error cleaning filters"
    popd > /dev/null # filters-no-binfilter

    log "extract binfilter from filters"
    pushd filters-binfilter-only > /dev/null  || die "cd-ing to filters-binfilter-only"
    log "filter-out evertything but binfilter"
    git filter-branch --prune-empty --tag-name-filter cat --index-filter 'git rm -q -r --cached --ignore-unmatch filter hwpfilter lotuswordpro oox unoxml writerfilter writerperfect xmerge' -- --all || die "Error extracting binfilter out of filters"
    git filter-branch -f --prune-empty --tag-name-filter cat --tree-filter 'git ls-files | clean_spaces -p 1' -- --all || die "Error cleaning binfilter"
    popd > /dev/null # filters-binfilter-only

    git clone filters-binfilter-only binfilter || die "Error cloning filters-binfilter-only"
    git clone filters-no-binfilter filters || die "Error cloning filters-binfilter-only"
    rm -fr filters-no-binfilter
    rm -fr filters-binfilter-only
    rm -fr filters-base

    log "gc binfilter"
    pushd binfilter > /dev/null || die "Error cd-ing to binfilter"
    git gc --aggressive --prune=now || die "Error compacting the binfilter repo"
    popd > /dev/null # binfilter

    log "gc filters"
    pushd filters > /dev/null || die "Error cd-ing to filters"
    git gc --aggressive --prune=now || die "Error compacting the clean filters repo"
    popd > /dev/null # filters

    popd > /dev/null # GIT_TEMP
    log "Done processing for filters"
}

process_libs-extern()
{
    pushd ${GIT_TEMP?} > /dev/null || die "Error cd-ing to ${GIT_TEMP?}"

    log "clone a copy of libs-extern"
    git clone "${REMOTE_GIT_AUX_BASE?}/libs-extern" libs-extern-base || die "Errro cloning  $REMOTE_GIT_AUX_BASE/libs-extern"
    git clone libs-extern-base libs-extern-no-bloat || die "Error clonign libs-extern-base"

    log "create a lean libs-extern"
    pushd libs-extern-no-bloat > /dev/null || die "Error cd-ing to libs-extern-no-bloat"

    log "filter-out bloat"
    git filter-branch --prune-empty --tag-name-filter 'xargs -I{} echo "libs-extern_{}"' --index-filter 'git rm -q -r --cached --ignore-unmatch "*/download/*.tar.gz"' -- --all &&  ( git tag | grep -v "libs-extern_" | xargs -n 1 git tag -d > /dev/null ) || die "Error filteroing out bloat from libs-extern"
    git filter-branch -f --prune-empty --tag-name-filter cat --tree-filter 'git ls-files | clean_spaces -p 1' -- --all || die "Error cleaning libs-extern"
    popd > /dev/null # libs-extern-no-bloat

    git clone libs-extern-no-bloat libs-extern || die "Error cloning libs-extern-no-bloat"
    rm -fr libs-extern-no-bloat
    rm -fr libs-extern-base

    log "gc libs-extern"
    pushd libs-extern > /dev/null || die "Error cd-ing to libs-extern"
    git gc --aggressive --prune=now || die "Error compacting the clean libs-extern repo"
    popd > /dev/null # libs-extern

    popd > /dev/null # GIT_TEMP
    log "Done processing for libs-extern"
}

process_libs-extern-sys()
{

    pushd ${GIT_TEMP?} > /dev/null || die "Error cd-ing to ${GIT_TEMP?}"

    log "clone a copy of libs-extern-sys"
    git clone "${REMOTE_GIT_AUX_BASE?}/libs-extern-sys" libs-extern-sys-base || die "Errro cloning  $REMOTE_GIT_AUX_BASE/libs-extern-sys"
    git clone libs-extern-sys-base libs-extern-sys-no-dict-work || die "Error clonign libs-extern-sys-base"
    git clone libs-extern-sys-base libs-extern-sys-dict-work || die "Error clonign libs-extern-sys-base"

    log "create a lean libs-extern-sys"
    pushd libs-extern-sys-no-dict-work > /dev/null || die "Error cd-ing to libs-extern-sys-no-dict-work"

    log "filter-out dictionaries and bloat"
    for oldtag in $(git tag) ; do git tag "libs-extern-sys_${oldtag}" "$oldtag" ; git tag -d "${oldtag}" > /dev/null ; done
    git filter-branch --prune-empty --tag-name-filter cat --index-filter 'git rm -q -r --cached --ignore-unmatch dictionaries "*/download/*"' -- --all || die "Error filtering out dictionaries from libs-extern-sys"
    git filter-branch -f --prune-empty --tag-name-filter cat --tree-filter 'git ls-files | clean_spaces -p 1' -- --all || die "Error cleaning libs-extern-sys"
    popd > /dev/null # libs-extern-sys-no-dict-work

    git clone libs-extern-sys-no-dict-work libs-extern-sys || die "Error cloning libs-extern-sys-no-dict-work"
    rm -fr libs-extern-sys-no-dict-work

    log "gc libs-extern-sys"
    pushd libs-extern-sys > /dev/null || die "Error cd-ing to libs-extern-sys"
    git gc --aggressive --prune=now || die "Error compacting the clean libs-extern-sys repo"
    popd > /dev/null # libs-extern-sys

    log "extract dictionaries as stand-alone to be fusionned with translations"
    pushd libs-extern-sys-dict-work > /dev/null || die "Error cd-ing to libs-extern-sys-dict-work"
    log "filter-out everything but dictionaries"

    everything_but="bitstream-vera-fonts"
    for f in $(ls -1 | grep -v "dictionaries") ; do
	everything_but="$everything_but $f"
    done
    cmd="git rm -q -r --cached --ignore-unmatch ${everything_but?}"
    git filter-branch --prune-empty --tag-name-filter 'xargs -I{} echo "dictionaries_{}"' --index-filter "$cmd" -- --all && ( git tag | grep -v "dictionaries_" | xargs -n 1 git tag -d > /dev/null ) || die "Error extracting dictionaries out of libs-extern-sys"
    git filter-branch -f --prune-empty --tag-name-filter cat --tree-filter 'git ls-files | clean_spaces -p 1' -- --all || die "Error cleaning dictionaries"
    popd > /dev/null # lib-extern-sys-dict-work

    git clone libs-extern-sys-dict-work dictionaries || die "Error cloning libs-extern-sys-dict-work"
    rm -fr libs-extern-sys-dict-work
    rm -fr libs-extern-sys-base

    log "gc dictionaries"
    pushd dictionaries > /dev/null || die "Error cd-ing to dictionaries"
    git gc --aggressive --prune=now || die "Error compacting the dictionaries repo"
    popd > /dev/null # dictionaries

    popd > /dev/null # GIT_TEMP
    log "Done processing for libs-extern-sys"
}

merge_libs-extern-sys()
{
    merge_generic libs-extern-sys

    # work on still external repos
    pushd ${GIT_BASE?}/${GIT_NAME?}/clone > /dev/null || die "Error cd-ing to ${GIT_BASE}/${GIT_NAME}/clone from $(pwd)"

    log "clone transation"
    git clone "${REMOTE_GIT_AUX_BASE?}/translations" translations || die "Error cloning ${REMOTE_GIT_AUX_BASE?}/translations"
    pushd translations > /dev/null || die "Error cd-ing to translations"

    log "merge dictionaries into translation"
    # merge the extracted 'dictionaries' into the translations repo
    git remote add dictionaries "${GIT_TEMP?}/dictionaries" || die "Error adding remote ${GIT_TEMP?}/dictionaries"
    git fetch  dictionaries || die "Error fetching dictionaries"
#    git fetch -t dictionaries
    git merge -Xours dictionaries/master || die "Error merging dictionaries"
    git remote rm dictionaries || die "Error removing remote dictionaries"
    popd > /dev/null # translation

    popd > /dev/null # GIT_BASE/GIT_NAME/clone
    log "Done merging for libs-extern-sys and related"
}

merge_bootstrap()
{
    pushd ${GIT_BASE?} > /dev/null
    log "clone bootstrap to onegit"
    git clone "${GIT_TEMP?}/bootstrap" ${GIT_NAME?} || die "Error cloning ${GIT_TEMP?}/bootstrap"

    if [ -d "${REMOTE_GIT_BASE?}/src" ] ; then
	cp -r "${REMOTE_GIT_BASE?}/src" "${GIT_NAME?}/."
    fi
    pushd ${GIT_NAME?} > /dev/null || die "Error cd-ing to $(pwd)/${GIT_NAME?}"
    mkdir clone || die "Error creating $(pwd)/clone directory"
    popd > /dev/null # GIT_NAME

    popd > /dev/null # GIT_BASE
    log "Done merging bootstrap"
}

merge_filters()
{
    merge_generic filters

    log "clone binfilter"
    pushd ${GIT_BASE}/${GIT_NAME?}/clone > /dev/null || die "Error cd-ing to ${GIT_NAME}/clone"
    git clone "${GIT_TEMP?}/binfilter" binfilter || die "Error cloning ${GIT_TEMP?}/binfilter"
    popd > /dev/null # GIT_BASE/GIT_NAME/clone

    log "Done merging filters and related"
}

process_batch1()
{
    batch="[batch1]"

    process_bootstrap
    merge_bootstrap

    process_generic ure
    merge_generic ure

    process_generic calc
    merge_generic calc

    process_generic impress
    merge_generic impress

    process_generic base
    merge_generic base

    log "Done processing batch1"
}

process_batch2()
{
    batch="[batch2]"

    process_generic writer
    merge_generic writer

    process_filters
    merge_filters

    process_generic sdk
    merge_generic sdk

    log "Done processing batch2"
}

process_batch3()
{
    batch="[batch3]"

    process_generic libs-gui
    merge_generic libs-gui

    process_generic components
    merge_generic components

    process_generic testing
    merge_generic testing

    process_generic extensions
    merge_generic extensions

    process_generic extras
    merge_generic extras

    # lib-extern-sys deal also with translation by virtue of
    # adding dictionaries to it
    process_libs-extern-sys
    merge_libs-extern-sys

    pushd ${GIT_BASE?}/${GIT_NAME?}/clone > /dev/null || die "Error cd.ing to ${GIT_BASE}/${GIT_NAME}/clone from $(pwd)"
    log "clone help"
    git clone "${REMOTE_GIT_AUX_BASE?}/help" help || die "Error cloning ${REMOTE_GIT_AUX_BASE?}/help"
    popd > /dev/null # GIT_BASE/GIT_NAME/clone

    process_libs-extern
    merge_generic libs-extern

    process_generic postprocess
    merge_generic postprocess

    process_light artwork
    merge_generic artwork

    log "Done processing batch3"
}

process_batch4()
{
    batch="[batch4]"

    process_generic_mp libs-core
# alternate for debugging to avoid re-processing libs-core
#    sleep 5000
#    cp -r /fast/saved/libs-core /fast/gittemp/libs-core
    merge_generic libs-core

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

while getopts aC:e:g:hn:s:t: opt ; do
    case "$opt" in
	a) aply_patches; exit ;;
	e) END_PHASE="$OPTARG" ;;
        C) GIT_BASE="$OPTARG" ;;
        h) usage; exit ;;
        g) REMOTE_GIT_BASE="$OPTARG" ;;
        n) GIT_NAME="$OPTARG" ;;
	s) START_PHASE="$OPTARG" ;;
	t) GIT_TEMP="$OPTARG" ;;
    esac
done

# make sure we have a directory to work in (out new git repos will be created there,
# and our workdir for temporary repos
if [ ! -d ${GIT_BASE?} ] ; then
    die "$GIT_BASE is not a directory, please create it before using it"
fi
cat /dev/null > ${GIT_BASE?}/onegit.msgs

if [ -z ${START_PHASE} ] ; then
    START_PHASE=0
else
    case "$START_PHASE" in
	init) START_PHASE=0 ;;
	process) START_PHASE=1 ;;
	patch) START_PHASE=2 ;;
	tag)  START_PHASE=3 ;;
	*) die "Invalid -s arguemtn, expecting init, process, patch or tag" ;;
    esac
fi

if [ -z ${END_PHASE} ] ; then
    END_PHASE=3
else
    case "$END_PHASE" in
	init) END_PHASE=0 ;;
	process) END_PHASE=1 ;;
	patch) END_PHASE=2 ;;
	tag)  END_PHASE=3 ;;
	*) die "Invalid -e arguement, expecting init, process, patch or tag" ;;
    esac
fi

if [ $START_PHASE -gt $END_PHASE ] ; then
    die "-s and -e do not have compatible value"
fi

if [ $START_PHASE -lt 2 ] ; then
    # make sure we have a location for the source repos
    if [ -z "$REMOTE_GIT_BASE" ] ; then
	die "Missing -g arguement. use -h for help"
    fi
    if [ -d "${REMOTE_GIT_BASE?}" ] ; then
	REMOTE_GIT_AUX_BASE="${REMOTE_GIT_BASE?}/clone"
    else
	REMOTE_GIT_AUX_BASE="${REMOTE_GIT_BASE?}"
    fi
fi

if [ $START_PHASE -lt 2 ] ; then

    # preferably our target core repo does not exist already
    if [ -e "${GIT_BASE?}/${GIT_NAME?}" ] ; then
	die "$GIT_BASE/$GIT_NAME already exist, cannot create a git repo there"
    fi

    #check that clean_spaces is built
    if [ ! -x "${bin_dir?}/../clean_spaces/clean_spaces" ] ; then
	die "${bin_dir?}/../clean_spaces/clean_spaces need to be build"
    else
	export PATH="$PATH:${bin_dir?}/../clean_spaces/"
    fi
else
    # if we start after process the target repos is supposed to be here
    if [ ! -e "${GIT_BASE?}/${GIT_NAME?}" ] ; then
	die "$GIT_BASE/$GIT_NAME does not exist, cannot skip the process phase"
    fi
fi

if [ ! -d "${GIT_TEMP?}" ] ; then
    log "create a temporary workarea ${GIT_TEMP?}"
    mkdir "${GIT_TEMP?}" || die "Error creating directory ${GIT_TEMP?}"
fi

if [ $START_PHASE -le 1 -a $END_PHASE -ge 1  ] ; then

    log "Start OneGit conversion"

    (process_batch4)&
    p_batch4=$!

    (process_batch1)&
    p_batch1=$!

    (process_batch2)&
    p_batch2=$!

    (process_batch3)&
    p_batch3=$!

    result=0
    wait $p_batch1 || result=1
    wait $p_batch2 || result=1
    wait $p_batch3 || result=1
    wait $p_batch4 || result=1

    if [ $result -ne 0 ] ; then
	exit $result
    fi
fi

if [ $START_PHASE -le 2 -a $END_PHASE -ge 2  ] ; then
    log "Apply patches"
    apply_patches
fi

if [ $START_PHASE -le 3 -a $END_PHASE -ge 3  ] ; then

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

    popd > /dev/null # GIT_BASE/GIT_NAME

fi
log "OneGit conversion All Done."

