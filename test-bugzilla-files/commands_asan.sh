#!/bin/bash
cd /srv/crashtestdata/
source config.cfg
rm tmpdir/* -r
rm current/* -r
rm control/* -r
rm console_*
cd ~/source/libo-core/
SHA=`git rev-parse HEAD`
echo $SHA
mkdir -p /srv/crashtestdata/logs_asan/$SHA

cd ~/source/dev-tools/test-bugzilla-files/
python3 new-control.py --asan /srv/crashtestdata/files/ 

cd /srv/crashtestdata/
