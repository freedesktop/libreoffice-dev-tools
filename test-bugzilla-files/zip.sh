cd ~/source/libo-core/
SHA=`git rev-parse HEAD`
echo $SHA
cd /srv/crashtestdata/
source config.cfg
cd /srv/crashtestdata/control/
mkdir -p /srv/crashtestdata/logs/$SHA/backtraces
for a in */core*; do gdb ~/build/instdir/program/soffice.bin $a -ex "thread apply all backtrace full" --batch > /srv/crashtestdata/logs/$SHA/backtraces/`dirname "$a"`-`basename "$a"`.backtrace; done
cat */crashlog.txt > /srv/crashtestdata/logs/$SHA/crashlog.txt
cat */exportCrash.txt > /srv/crashtestdata/logs/$SHA/exportCrash.txt
cd /srv/crashtestdata/current/srv/crashtestdata/files/
zip -r -q validation.zip */*.log
mv validation.zip /srv/crashtestdata/logs/$SHA/.
cd /srv/crashtestdata/logs/$SHA
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
cd /srv/crashtestdata/
./sendEmail -f "Crashtest VM <crashtest.libreoffice@gmail.com>" -t libreoffice@lists.freedesktop.org -o tls=yes -s smtp.gmail.com:587 -u "Crash test update" -m "New crashtest update available at https://dev-builds.libreoffice.org/crashtest/$SHA/" -a logs/*.csv -xu crashtest.libreoffice -xp $PASSWORD
