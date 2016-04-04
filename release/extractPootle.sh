#!/bin/bash

echo "********** POOTLE EXTRACT SCRIPT **********"
echo "*** This script will generate 2 files:"
echo "*** /tmp/ui.tar.bz2   (all ui po files)"
echo "*** /tmp/help.tar.bz2 (all help po files)"

# prompt for input if no arguments
if [ $# -eq 1 ]
then
    ver=$1
else
    echo -n "Input project version (e.g 51) to extract ? "
    read ver
fi
ver="libo${ver}"
echo ">>>>>>>>>> extracting projects ${ver}_[ui|help]"

file="/var/www/sites/translations.documentfoundation.org"
if [ ! -d "${file}" ]; then
  echo ">>>>>>>>>> cannot locate site directory (${file})!"
  exit -1
fi
tran="${file}/translations/${ver}"
if [ ! -d "${tran}_ui" -o ! -d "${tran}_help" ]; then
  echo ">>>>>>>>>> cannot locate project ui!"
  exit -1
fi

echo ">>>>>>>>>> setup pootle environment"
cd $file
pwd
source ./env/bin/activate

echo ">>>>>>>>> Sync pootle db with files"
python src/manage.py list_languages --project=${ver}_ui   |xargs -P 14 -I onelang python src/manage.py sync_stores --force --overwrite  --project=${ver}_ui   --language=onelang -v 1
python src/manage.py list_languages --project=${ver}_help |xargs -P 14 -I onelang python src/manage.py sync_stores --force --overwrite  --project=${ver}_help --language=onelang -v 1


echo ">>>>>>>>> backup po files"
rm /tmp/*bz2
tar cjf /tmp/ui.tar.bz2 translations/${ver}_ui/ && tar cjf /tmp/help.tar.bz2 translations/${ver}_help/

echo ">>>>>>>>> finished"
