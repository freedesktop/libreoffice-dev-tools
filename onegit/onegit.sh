#!/usr/bin/env bash

bin_dir=$(dirname "$0")
pushd "${bin_dir}"
bin_dir=$(pwd)
popd > /dev/null

GIT_BASE=$(pwd)
GIT_NAME="libo"
GIT_TEMP=${GIT_BASE}/gittemp
REPOS="base bootstrap calc components extensions extras filters impress libs-core libs-extern libs-extern-sys libs-gui postprocess sdk testing ure writer"
UNTOUCHED_REPOS="artwork help translations"

die()
{
    echo "*** $@" >&2
    exit 1
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
/*/wntgcc?
/*/wntgcc?.pro
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
/*/unxand?
/*/unxand?.pro
/*/unxios?
/*/unxios?.pro
/solver/*

# autoconf generated stuff
/aclocal.m4
/autom4te.cache
/autogen.lastrun
/bootstrap
/ChangeLog
/config.guess
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

clone_generic()
{
    echo "== clone a copy of $repo =="
    git clone "${REMOTE_GIT_AUX_BASE?}/$repo" $r || die "Errro cloning  $REMOTE_GIT_AUX_BASE/$r"
}

clone_artwork()
{
    clone_generic artwork
}

clone_bootstrap()
{
    echo "== clone a copy of bootstrap =="
    if [ -d "${REMOTE_GIT_BASE?}" ] ; then
        git clone "${REMOTE_GIT_BASE?}" bootstrap || die "Errro cloning  $REMOTE_GIT_BASE"
    else
        git clone "${REMOTE_GIT_AUX_BASE?}/bootstrap" bootstrap || die "Errro cloning  $REMOTE_GIT_AUX_BASE"
    fi
}

clone_base()
{
    clone_generic base
}

clone_calc()
{
    clone_generic calc
}

clone_components()
{
    clone_generic components
}

clone_extensions()
{
    clone_generic extensions
}

clone_extras()
{
    clone_generic extras
}

clone_filters()
{
    echo "== clone a copy of filters =="
    git clone "${REMOTE_GIT_AUX_BASE?}/filters" filters-base || die "*** Error cloning $REMOTE_GIT_AUX_BASE/filters"
    git clone filters-base filters-no-binfilter || die "*** Error cloning filters-base"
    git clone filters-base filters-binfilter-only  || die "*** Error cloning filters-base"
}

clone_help()
{
    clone_generic help
}

clone_impress()
{
    clone_generic impress
}

clone_libs-core()
{
    clone_generic libs-core
}

clone_libs-extern()
{
    echo "== clone a copy of libs-extern =="
    git clone "${REMOTE_GIT_AUX_BASE?}/libs-extern" libs-extern-base || die "Errro cloning  $REMOTE_GIT_AUX_BASE/libs-extern"
    git clone libs-extern-base libs-extern-no-bloat || die "*** Error clonign libs-extern-base"
}

clone_libs-extern-sys()
{

    echo "== clone a copy of libs-extern-sys =="
    git clone "${REMOTE_GIT_AUX_BASE?}/libs-extern-sys" libs-extern-sys-base || die "Errro cloning  $REMOTE_GIT_AUX_BASE/libs-extern-sys"
    git clone libs-extern-sys-base libs-extern-sys-no-dict-work || die "*** Error clonign libs-extern-sys-base"
    git clone libs-extern-sys-base libs-extern-sys-dict-work || die "*** Error clonign libs-extern-sys-base"
}

clone_libs-gui()
{
    clone_generic libs-gui
}

clone_postprocess()
{
    clone_generic postprocess
}

clone_sdk()
{
    clone_generic sdk
}

clone_testing()
{
    clone_generic testing
}

clone_ure()
{
    clone_generic ure
}

clone_writer()
{
    clone_generic writer
}


process_generic()
{
    r=$1

    echo "== generic processing for $r =="
    pushd $r || die "*** Error cd-ing to $r"
    for oldtag in $(git tag) ; do git tag "${r}_${oldtag}" "$oldtag" ; git tag -d "${oldtag}" > /dev/null ; done
    git filter-branch --prune-empty --tag-name-filter cat --tree-filter 'find . -type f | xargs -n 100 clean_spaces ' -- --all
    popd > /dev/null
}

process_bootstrap()
{
    echo "== generic processing for bootstrap =="
    pushd bootstrap || die "*** Error cd-ing to bootstrap"
    git filter-branch --prune-empty --tag-name-filter cat --tree-filter 'find . -type f | xargs -n 100 clean_spaces ' -- --all
    popd > /dev/null
}

process_artwork()
{
    process_generic artwork
}

process_base()
{
    process_generic base
}

process_calc()
{
    process_generic calc
}

process_components()
{
    process_generic components
}

process_extensions()
{
    process_generic extensions
}

process_extras()
{
    process_generic extras
}

process_filters()
{
    echo "== filter out binfilter from filters =="
    (
        cd filters-no-binfilter  || die "cd-ing to filters-no-binfilter"
        echo "=== filter-out binfilter"
        git filter-branch --prune-empty --tag-name-filter 'xargs -I{} echo "filters_{}"' --index-filter 'git rm -q -r --cached --ignore-unmatch  binfilter' -- --all && ( git tag | grep -v "filters_" | xargs -n 1 git tag -d > /dev/null ) || die "*** Error filtering out binfilter"
        git filter-branch -f --prune-empty --tag-name-filter cat --tree-filter 'find . -type f | xargs -n 100 clean_spaces ' -- --all
    ) &
    p1=$!

    echo "== extract binfilter from filters =="
    (
        cd filters-binfilter-only  || die "cd-ing to filters-binfilter-only"
        echo "=== filter-out evertything but binfilter"
        git filter-branch --prune-empty --tag-name-filter cat --index-filter 'git rm -q -r --cached --ignore-unmatch filter hwpfilter lotuswordpro oox unoxml writerfilter writerperfect xmerge' -- --all || die "*** Error extracting binfilter out of filters"
        git filter-branch -f --prune-empty --tag-name-filter cat --tree-filter 'find . -type f | xargs -n 100 clean_spaces ' -- --all
    )&
    p2=$!

    result=0
    wait $p1 || result=1
    wait $p2 || result=1
    if [ $result -eq 1 ] ; then
	exit $result
    fi

    git clone filters-binfilter-only binfilter || die "*** Error cloning filters-binfilter-only"
    git clone filters-no-binfilter filters || die "*** Error cloning filters-binfilter-only"
    rm -fr filters-no-binfilter
    rm -fr filters-binfilter-only
    rm -fr filters-base

    echo "== gc binfilter =="
    pushd binfilter || die "*** Error cd-ing to binfilter"
    git gc --aggressive --prune=now || die "*** Error compacting the binfilter repo"
    popd > /dev/null

    echo "== gc filters =="
    pushd filters || die "*** Error cd-ing to filters"
    git gc --aggressive --prune=now || die "*** Error compacting the clean filters repo"
    popd > /dev/null
}

process_help()
{
    process_generic help
}

process_impress()
{
    process_generic impress
}

process_libs-core()
{
    process_generic libs-core
}

process_libs-extern()
{
    echo "== create a lean libs-extern =="
    pushd libs-extern-no-bloat || die "*** Error cd-ing to libs-extern-no-bloat"
    echo "== filter-out bloat =="
    git filter-branch --prune-empty --tag-name-filter 'xargs -I{} echo "libs-extern_{}"' --index-filter 'git rm -q -r --cached --ignore-unmatch "*/download/*.tar.gz"' -- --all &&  ( git tag | grep -v "libs-extern_" | xargs -n 1 git tag -d > /dev/null ) || die "*** Error filteroing out bloat from libs-extern"
    git filter-branch -f --prune-empty --tag-name-filter cat --tree-filter 'find . -type f | xargs -n 100 clean_spaces ' -- --all
    popd > /dev/null
    git clone libs-extern-no-bloat libs-extern || die "*** Error cloning libs-extern-no-bloat"
    rm -fr libs-extern-no-bloat
    rm -fr libs-extern-base
    echo "== gc libs-extern =="
    pushd libs-extern || die "*** Error cd-ing to libs-extern"
    git gc --aggressive --prune=now || die "*** Error compacting the clean libs-extern repo"
    popd > /dev/null
}

process_libs-extern-sys()
{

(
    echo "== create a lean libs-extern-sys =="
    pushd libs-extern-sys-no-dict-work || die "*** Error cd-ing to libs-extern-sys-no-dict-work"
    echo "== filter-out dictionaries and bloat=="
    for oldtag in $(git tag) ; do git tag "libs-extern-sys_${oldtag}" "$oldtag" ; git tag -d "${oldtag}" > /dev/null ; done
    git filter-branch --prune-empty --tag-name-filter cat --index-filter 'git rm -q -r --cached --ignore-unmatch dictionaries */download' -- --all || die "*** Error filtering out dictionaries from libs-extern-sys"
    git filter-branch -f --prune-empty --tag-name-filter cat --tree-filter 'find . -type f | xargs -n 100 clean_spaces ' -- --all
    popd > /dev/null
    git clone libs-extern-sys-no-dict-work libs-extern-sys || die "*** Error cloning libs-extern-sys-no-dict-work"
    rm -fr libs-extern-sys-no-dict-work
    echo "== gc libs-extern-sys =="
    pushd libs-extern-sys|| die "*** Error cd-ing to libs-extern-sys"
    git gc --aggressive --prune=now || die "*** Error compacting the clean libs-extern-sys repo"
    popd > /dev/null
)&
p1=$!

(
    echo "extract dictionaries as stand-alone to be fusionned with translations"
    pushd libs-extern-sys-dict-work || die "*** Error cd-ing to libs-extern-sys-dict-work"
    echo "== filter-out everything but dictionaries =="
    git filter-branch --prune-empty --tag-name-filter 'xargs -I{} echo "dictionaries_{}"' --index-filter 'git rm -q -r --cached --ignore-unmatch berkeleydb  boost  cairo  curl expat  graphite  hunspell  icu  jpeg  libxml2  libxslt  more_fonts  moz  neon  nss  python  saxon  stax  zlib bitstream_vera_fonts' -- --all && ( git tag | grep -v "dictionaries_" | xargs -n 1 git tag -d > /dev/null ) || die "*** Error extracting dictionaries out of libs-extern-sys"
    git filter-branch -f --prune-empty --tag-name-filter cat --tree-filter 'find . -type f | xargs -n 100 clean_spaces ' -- --all
    popd > /dev/null

    git clone libs-extern-sys-dict-work dictionaries || die "*** Error cloning libs-extern-sys-dict-work"
    rm -fr libs-extern-sys-dict-work
    rm -fr libs-extern-sys-base

    echo "== gc dictionaries =="
    pushd dictionaries || die "*** Error cd-ing to dictionaries"
    git gc --aggressive --prune=now || die "*** Error compacting the dictionaries repo"
    popd > /dev/null
)&
p2=$!

   result=0
   wait $p1 || result=1
   wait $p2 || result=1
   exit $result
}

process_libs-gui()
{
    process_generic libs-gui
}

process_postprocess()
{
    process_generic postprocess
}

process_sdk()
{
    process_generic sdk
}

process_testing()
{
    process_generic testing
}

process_ure()
{
    process_generic ure
}

process_writer()
{
    process_generic writer
}


##### main

while getopts C:g:hn:t: opt ; do
    case "$opt" in
        C) GIT_BASE="$OPTARG" ;;
        h) usage; exit ;;
        g) REMOTE_GIT_BASE="$OPTARG" ;;
        n) GIT_NAME="$OPTARG" ;;
    t) GIT_TEMP="$OPTARG" ;;
    esac
done

# make sure we have a location for the source repos
if [ -z "$REMOTE_GIT_BASE" ] ; then
    echo "*** Missing -g arguement. use -h for help" 1>&2
    exit 1
fi

# make sure we have a directory to work in (out new git repos will be created there,
# and our workdir for temporary repos
if [ ! -d ${GIT_BASE?} ] ; then
    echo "*** $GIT_BASE is not a directory, please create it before using it" 1>&2
    exit 1
fi

# preferably our target core repo does not exist already
if [ -e "${GIT_BASE?}/${GIT_NAME?}" ] ; then
    echo "*** $GIT_BASE/$GIT_NAME already exist, cannot create a git repo there" 1>&2
    exit 1
fi

#check that clea_spaces is built
if [ ! -x "${bin_dir?}/../clean_spaces/clean_spaces" ] ; then
    echo "${bin_dir?}/../clean_spaces/clean_spaces need to be build" 1>&2
    exit 1
else
    export PATH="$PATH:${bin_dir?}/../clean_spaces/"
fi

if [ -d "${REMOTE_GIT_BASE?}" ] ; then
    REMOTE_GIT_AUX_BASE="${REMOTE_GIT_BASE?}/clone"
else
    REMOTE_GIT_AUX_BASE="${REMOTE_GIT_BASE?}"
fi

# we could verify that the workdir is clean too... to avoid disagreement later ?

pushd $GIT_BASE || die "*** Error cd-ing to ${GIT_BASE}"


echo "== create a temporary workarea ${GIT_TEMP?} =="
(
    if [ ! -d "${GIT_TEMP?}" ] ; then
        mkdir "${GIT_TEMP?}" || die "*** Error creating directory ${GIT_TEMP?}"
    fi
    cd "${GIT_TEMP?}" || die "*** Error cd-ing to ${GIT_TEMP?}"

    pids=()
    nb_task=0
    result=0

    for repo in $REPOS ; do
            clone_${repo} || die
            process_${repo} &
            pids[$nb_task]=$!
            let nb_task=$nb_task+1
    done
    for job in ${pids[@]} ; do
            wait $job || result=1
    done
    exit $result;
) || die

echo "== clone bootstrap =="

git clone "${GIT_TEMP?}/bootstrap" ${GIT_NAME?} || die "*** Error cloning ${GIT_TEMP?}/bootstrap"

if [ -d "${REMOTE_GIT_BASE?}/src" ] ; then
    cp -r "${REMOTE_GIT_BASE?}/src" "${GIT_NAME?}/."
fi

# clone untouched repos
(
    cd ${GIT_NAME} || dir "*** Error cd-ing to $(pwd)/${GIT_NAME?}"
    mkdir clone || die "*** Error creating $(pwd)/clone directory"

    cd clone || die "*** Error cd-ing to $(pwd)/clone"
    for repo in ${UNTOUCHED_REPOS?} ; do
        git clone "${REMOTE_GIT_AUX_BASE?}/$repo" $repo || die "*** Error cloning ${REMOTE_GIT_AUX_BASE?}/$repo"
) || die


(
    cd $GIT_NAME || die "*** Error cd-ing to $(pwd)/${GIT_NAME?}"

    echo "== add repos =="
    for repo in $REPOS ; do
        if [ "$repo" != "bootstrap" ] ; then
                echo "== Add remote ${GIT_TEMP?}/$repo =="
                git remote add $repo "${GIT_TEMP?}/$repo" || die "*** Error adding remote ${GIT_TEMP?}/$repo"
        fi
    done

    echo "== fetch repos =="
    for repo in $REPOS ; do
        if [ "$repo" != "bootstrap" ] ; then
                git fetch $repo || die "*** Error fetching $repo"
                git fetch -t $repo || die "*** Error fetching tags for $repo"
        fi
    done

    echo "== merges =="

    for repo in $REPOS ; do
        if [ "$repo" != "bootstrap" ] ; then
                git merge -Xours $repo/master || die "*** Error merging $repo/master"
        fi
    done

    echo "== rm repos =="
    for repo in $REPOS ; do
        if [ "$repo" != "bootstrap" ] ; then
                git remote rm $repo || die "*** Error removing remote $repo/master"
        fi
    done


    echo "== import dictionaries into translation =="
    (
        cd clone || die "*** Error cd-ing to $(pwd)/clone"
        cd translations || die "*** Error cd-ing to $(pwd)/translations"

        # merge the extracted 'dictionaries' into the translations repo
        git remote add dictionaries "${GIT_TEMP?}/dictionaries" || die "*** Error adding remote ${GIT_TEMP?}/dictionaries"
        git fetch  dictionaries || die "*** Error fetching dictionaries"
        git fetch -t dictionaries || die "*** Error fetching dictionaries"
        git merge -Xours dictionaries/master || die "*** Error merging dictionaries"
        git remote rm dictionaries || die "*** Error removing remote dictionaries"

    ) || die


    echo "== copy binfilters in clone/binfilters =="
    (
        cd clone
        git clone "${GIT_TEMP?}/binfilter" binfilter || die "*** Error cloning ${GIT_TEMP?}/binfilter"
    )
    echo "== clean-up bootstrap .gitignore =="

    reset_gitignore


    echo "== tag repos == "
    git tag -m "OneGit script applied" MELD_LIBREOFFICE_REPOS || die "*** Error applying tag on core"
    ( cd clone/translations && git tag -m "OneGit script applied" MELD_LIBREOFFICE_REPOS ) || die "*** Error applying tag on translations"
    ( cd clone/binfilter && git tag -m "OneGit script applied" MELD_LIBREOFFICE_REPOS ) || die "*** Error applying tag on binfilter"

) || die

