#!/bin/bash
cd /srv/crashtestdata/
source config.cfg
rm tmpdir/* -r
rm current/* -r
rm control/* -r
rm console_*
cd ~/build/
make clean
cd ~/source/dev-tools/
git pull -r
cd ~/source/libo-core/
git pull -r
SHA=`git rev-parse HEAD`
echo $SHA
mkdir /srv/crashtestdata/logs/$SHA
cd ~/build/
make

if [ "$?" != "0" ]; then
	/srv/crashtestdata/sendEmail -f crashtest.libreoffice@gmail.com -t markus.mohrhard@googlemail.com -o tls=yes -s smtp.gmail.com:587 -u "Crash test build failure" -m "The build failed. Please check!" -xu crashtest.libreoffice -xp $PASSWORD
	/srv/crashtestdata/sendEmail -f crashtest.libreoffice@gmail.com -t vmiklos@collabora.co.uk -o tls=yes -s smtp.gmail.com:587 -u "Crash test build failure" -m "The build failed. Please check!" -xu crashtest.libreoffice -xp $PASSWORD
    exit 1
fi

cd ~/source/dev-tools/test-bugzilla-files/
python3 new-control.py /srv/crashtestdata/files/

if [ "$?" != "0" ]; then
	/srv/crashtestdata/sendEmail -f crashtest.libreoffice@gmail.com -t markus.mohrhard@googlemail.com -o tls=yes -s smtp.gmail.com:587 -u "Crash test failure" -m "The test run failed. Please check!" -xu crashtest.libreoffice -xp $PASSWORD
	/srv/crashtestdata/sendEmail -f crashtest.libreoffice@gmail.com -t vmiklos@collabora.co.uk -o tls=yes -s smtp.gmail.com:587 -u "Crash test failure" -m "The test run failed. Please check!" -xu crashtest.libreoffice -xp $PASSWORD
    exit 1
fi

cd /srv/crashtestdata/
./zip.sh
