#!/bin/bash

SPLIT_GIT=/local/libreoffice/master
ONE_GIT=/local/libreoffice/dev-tools/onegit/libo

# list all revisions of the file
function all_revs {
    FILE="$1"
    git rev-list --reverse --objects HEAD -- "$FILE" | while read SHA REST ; do
        TYPE=`git cat-file -t $SHA`
	if [ "$TYPE" = "blob" ] ; then
	    git cat-file -p $SHA
	fi
    done
}

cd "$ONE_GIT"
find . -type f | while read FILE ; do
    all_revs "$FILE" > /tmp/testrev.onegit

    TRY_FILE=`eval "echo $SPLIT_GIT/clone/*/$FILE"`
    DIR="$SPLIT_GIT"
    if [ -f "$TRY_FILE" ] ; then
	DIR="${TRY_FILE%$FILE}"
    fi
    pushd "$DIR" > /dev/null
    all_revs "$FILE" > /tmp/testrev.splitgit
    popd > /dev/null

    echo -n "Trying $FILE ... "
    if diff -uw /tmp/testrev.splitgit /tmp/testrev.onegit ; then
	echo "OK"
    else
	echo "ERROR: $FILE differs"
    fi
done
