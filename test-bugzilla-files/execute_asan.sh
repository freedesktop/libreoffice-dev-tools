dir_name=$(basename $1)
mkdir /srv/crashtestdata/control/$dir_name
cd /srv/crashtestdata/control/$dir_name
TMPDIR=/srv/crashtestdata/tmpdir /srv/crashtestdata/build/instdir/program/python /home/buildslave/source/dev-tools/test-bugzilla-files/test-bugzilla-files.py --asan --soffice=path:/srv/crashtestdata/build/instdir/program/soffice --userdir=file:///home/buildslave/.config/libreoffice_$dir_name/4 $1 2>&1 | tee /srv/crashtestdata/console_$dir_name.log
rm core*
