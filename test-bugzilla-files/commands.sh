cd /srv/crashtestdata/
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

if [ "$?" != "0" ]; then
    echo "Please inspect the build" | mail -s "Crash test VM build failure" markus.mohrhard@googlemail.com
    exit 1
fi

cd /srv/crashtestdata/files/
python3 new-control.py
cd /srv/crashtestdata/
./zip.sh
