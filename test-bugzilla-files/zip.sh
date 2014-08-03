cd ~/source/libo-core/
SHA=`git rev-parse HEAD`
echo $SHA
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
