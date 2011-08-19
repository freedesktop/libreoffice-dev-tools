#!/bin/bash

SPLIT_GIT=/local/libreoffice/master
ONE_GIT=/local/libreoffice/dev-tools/onegit/libo

# list all revisions of the file
function all_revs {
    FILE="$1"

    # first the log (without commit numbers)
    git log --reverse --pretty=format:"Author: %an <%ae>%nDate: %ai%nCommitter: %cn <%ce>%nCommit date: %ci%n%n%B" "$FILE"

    # then all the revisions of the file
    git rev-list --reverse --objects HEAD -- "$FILE" | while read SHA REST ; do
        TYPE=`git cat-file -t $SHA`
        if [ "$TYPE" = "blob" ] ; then
            git cat-file -p $SHA
        fi
    done
}

cd "$ONE_GIT"
for MODULE in .[^.]* * ; do
(
    [ "$MODULE" != ".git" ] && find $MODULE -type f | while read FILE ; do
        all_revs "$FILE" > /tmp/testrev.$MODULE.onegit
    
        TRY_FILE=`eval "echo $SPLIT_GIT/clone/*/$FILE"`
        DIR="$SPLIT_GIT"
        if [ -f "$TRY_FILE" ] ; then
            DIR="${TRY_FILE%$FILE}"
        fi
        pushd "$DIR" > /dev/null
        all_revs "$FILE" > /tmp/testrev.$MODULE.splitgit
        popd > /dev/null
    
        (
            echo -n "Trying $FILE ... "
            if diff -uw /tmp/testrev.$MODULE.splitgit /tmp/testrev.$MODULE.onegit ; then
                echo "OK"
            else
                echo "ERROR: $FILE differs"
            fi
        ) > /tmp/testrev.$MODULE.log

        (
            flock -x 200
            cat /tmp/testrev.$MODULE.log
        ) 200>/tmp/testrev.lock
    done
) &
done

wait
