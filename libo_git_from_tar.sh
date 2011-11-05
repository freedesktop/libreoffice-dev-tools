#!/usr/bin/env bash

# This script purpose is to simplify the setup of a git environment for libre-office development
# using tar.bz2 package of the individual git repos accessible via http
# This is needed because direct initial download of large git repositories via anongit can
# be slow and suceptible to interruption in case of un-reliable internet connection
#
# (C) 2011 Norbert Thiebaud <nthiebaud@gmail.com>
# Licence: GPLv3  see: http://www.gnu.org/licenses/gpl-3.0.txt
#

temp_dir=/tmp
core_path=libo
active=true
resume=false

do_core=false
do_binfilter=false
do_translations=false
do_help=false
do_dictionaries=false

die()
{
    echo "Error: $@"
    exit 1
}

usage()
{
    echo "usage: $0 [-h] [-d <path>] [-t <path>] [all | dev | [core] [help] [tr[anslations]] [binfilter] [dict[ionaries]]"
    echo ""
    echo "    -h        Display this help."
    echo "    -d <path> The location of the core repository for libreoffice. Default: ./libo"
    echo "    -p        Pretend. display what would be done, but do not actually do it."
    echo "    -resume   try to re-use already downloaded/partially downloaded tar.bz2"
    echo "    -t <path> The location of the temporary directory used to download and extract repositories. Default: /tmp"
    echo ""
    echo "The arguments name the repositories to be downloaded, 'all' means... all of them. 'dev' means all but translations, which is the default."
    echo "You cannot re-clone an existing core repository, but for the other repositories, if they already exist they will be removed and replace by a fresh new clone"
    echo "Beware: a fresh new clone will be on the 'master' branch regardless of the branch core is on, or of the branch the replaced repo was on."
    echo ""
    echo "Do not abuse this script. Once you have downloaded a set of git repos, it is much more efficient, for you and for us, to use ./g pull -r to refresh your git repositories"
    echo ""
    echo "Example:"
    echo "$0 # will clone the core repo in ./libo (right now: $(pwd)/libo) and clone binfilter, help and dictionaries in ./libo/clone"
    echo ""
    echo "$0 -d ~/core # clone the core repo in ~/core and clone binfilter, help and dictionaries in ~/core/clone"
    echo ""
    echo "$0 -d ~/libo translations # remove ~/libo/clone/translations if it exist, and clone a new translations repo there"
}

###
# Make sure that the basic tools of the trade are available
#
sanity_check()
{
    which wget > /dev/null 2>&1 || die "This script need wget in the PATH to function"
    which tar > /dev/null 2>&1 || die "This script need tar in the PATH to function"
    which bzip2 > /dev/null 2>&1 || die "This script need bzips in the PATH to function"
}

###
# Wrapper to execute a command respecting the 'pretend' mode
#
do_action()
{
local description_message="$1"
shift
local die_message="$1"
shift

   if [ -n "$description_message" ] ; then echo "--> $description_message" ; fi
   if $active ; then
       $@ || die "$die_message"
   fi
}

###
# Create the links, if needed, in the core repo for a given child repos
#
relink()
{
local repo="$1"

    for link in $(ls clone/$repo) ; do
        if [ ! -e "$link" ] ; then
            echo "Creating missing link $link"
            ln -s "clone/$repo/$link" "$link"
        fi
    done
}

###
# - download the tar.bz2 associated with a given git repository
# - remove the existing copy if any
# - untar the new copy
# - reset the working view to origin/master's HEAD
# - create the links in core if needed
#
# Note:
# This function assume that the working directory is
# the directory of the core repository
# This function is meant to be used only for 'child' repositories
# i.e the ones that live in clone/.
#
process_child_repo()
{
local repo="$1"

    if ! $resume ; then do_action "Remove old copy of $repo tar.bz2 file, if any" "removing ${temp_dir}/libreoffice-$repo.tar.bz2"  rm -f ${temp_dir}/libreoffice-$repo.tar.bz2 ; fi
    do_action "Download the $repo repo tar.bz2 file" "downloading package for the $repo repo" wget -c http://dev-www.libreoffice.org/bundles/libreoffice-$repo.tar.bz2 -P ${temp_dir}

    if [ -e ./clone/$repo ] ; then
        do_action "Remove the current $repo repo" "removing ./clone/$repo" rm -fr ./clone/$repo
    fi
    do_action "unpack the $repo tar.bz2 file" "unpacking the $repo tar.bz2 file" tar -xf ${temp_dir}/libreoffice-$repo.tar.bz2 -C clone
    do_action "" "cannot cd to clone/$repo" pushd ./clone/$repo > /dev/null
    do_action "restore the working view of the $repo repo" "restoring the working view of $repo" git reset --hard
    do_action "" "pop-ing up to the previous directory" popd > /dev/null
    do_action "re-create the links in core for $repo if needed" "" relink $repo

}

while [ "${1:-}" != "" ] ; do
    case "$1" in
        -h|--help) usage; exit 0;;
        -d) shift; core_path="$1" ;;
        -t) shift; temp_dir="$1" ;;
        -p) active=false ;;
        --resume) resume=true ;;
        all)  do_core=true ; do_binfilter=true; do_help=true; do_dictionaries=true ; do_translations=true;;
        dev)  do_core=true ; do_binfilter=true; do_help=true; do_dictionaries=true ;;
        core) do_core=true ;;
        help) do_help=true ;;
        bin*) do_binfilter=true ;;
        dict*) do_dictionaries=true ;;
        tr*) do_translations=true ;;
        *) die "Invalid argument: $1 Run the command with -h for help";;
    esac
    shift
done

sanity_check

if  ! ${do_core} && ! ${do_binfilter} && ! ${do_translations} &&  ! ${do_help} && ! ${do_dictionaries}  ; then
    do_core=true
    do_binfilter=true
    do_help=true
    do_dictionaries=true
fi

if [ -e ${core_path?} ] ; then
    if [ -d ${core_path} ] ; then
        if $do_core ; then
            die "$core_path exist, I cannot download a new core repo there."
        else
            if [ ! \( -d $core_path/.git  -a  -d $core_path/sw  -a ! -L $core_path/sw \)  ] ; then
                die "$core_path exist, but does not appear to be a valid core git repository, I cannot add sub-repositores there."
            fi
        fi
    else
        die "$core_path exist, I cannot download a new core repo there."
    fi
else
    base_path=$(dirname ${core_path})
    if [ ! -d ${base_path} ] ; then
        die "$base_path does not exist"
    fi
fi

if [ ! -d $temp_dir ] ; then
    die "temp dir : $temp_dir does not exist. The default is /tmp, override with -t <path>"
fi


if $do_core ; then
    if ! $resume ; then do_action "Remove any old copy of core tar.bz2 file, if any" "removing ${temp_dir}/libreoffice-core.tar.bz2"  rm -f ${temp_dir}/libreoffice-core.tar.bz2 ; fi
    do_action "Download the core repo tar.bz2 file" "downloading package for the core repo" wget -c http://dev-www.libreoffice.org/bundles/libreoffice-core.tar.bz2 -P ${temp_dir}
    do_action "" "cannot create the directory ${core_path}" mkdir ${core_path?}
    do_action "" "cannot cd to ${core_path?}" pushd ${core_path?} > /dev/null
    do_action "Unpack the core repo tar.bz2 file to ${core_path}" "unpacking the core tar.bz2 file" tar --strip-components=1 -xf ${temp_dir}/libreoffice-core.tar.bz2
    do_action "" "cannot create the directory clone" mkdir clone
    do_action "Restore the working view of the core repo" "restoring the working view of core" git reset --hard
else
    do_action "" "cannot cd to ${core_path?}" pushd ${core_path?} > /dev/null
fi

$do_translations && process_child_repo translations
$do_dictionaries && process_child_repo dictionaries
$do_binfilter && process_child_repo binfilter
$do_help && process_child_repo help

echo "Done."
