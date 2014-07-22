cd /srv/crashtestdata/
rm nohup.put
rm tmpdir/* -r
rm current/* -r
rm control/* -r
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
cd /srv/crashtestdata/files/
python3 new-control.py
cd /srv/crashtestdata/control/
zip -r control.zip */*
mv control.zip /srv/crashtestdata/logs/$SHA/.
cd /srv/crashtestdata/current/srv/crashtestdata/files/
zip -r validation.zip */*.log
mv validation.zip /srv/crashtestdata/logs/$SHA/.
cd /srv/crashtestdata/logs/$SHA
unzip control.zip
unzip validation.zip -d validation
rm *.zip
cp ~/source/dev-tools/test-bugzilla-files/analyze-logs.py .
cp ../*.csv .
python3 analyze-logs.py
cp *.csv ../.
cd ..
zip -r current.zip $SHA/*
scp current.zip upload@gimli.documentfoundation.org:/srv/www/dev-builds.libreoffice.org/crashtest/.
ssh upload@gimli.documentfoundation.org 'bash -s' << 'ENDSSH'
cd /srv/www/dev-builds.libreoffice.org/crashtest/
unzip current.zip
ENDSSH
