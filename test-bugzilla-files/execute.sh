mkdir /srv/crashtestdata/control/$1
cd /srv/crashtestdata/control/$1
TMPDIR=/srv/crashtestdata/tmpdir /home/buildslave/build/instdir/program/python /home/buildslave/source/dev-tools/test-bugzilla-files/test-bugzilla-files.py --soffice=path:/home/buildslave/build/instdir/program/soffice --userdir=file:///home/buildslave/.config/libreoffice_$1/4 $1 2>&1 | tee /srv/crashtestdata/console_$i.log
rm core*
