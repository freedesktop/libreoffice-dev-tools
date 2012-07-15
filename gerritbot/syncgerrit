#!/bin/bash
date >> /home/gerritbot/syncgerrit.log
git --git-dir=/home/gerritbot/core/.git fetch --all >> /home/gerritbot/syncgerrit.log 2>&1
# this should probably be a repo created with git clone --bare --mirror instead
# so that these checkouts and pulls are not needed anymore.
cd /home/gerritbot/core
git checkout master && git pull -r
git checkout libreoffice-3-5 && git pull -r
git checkout libreoffice-3-6 && git pull -r
git checkout libreoffice-3-5-5 && git pull -r
git --git-dir=/home/gerritbot/core/.git push -f ssh://logerrit/core master:master libreoffice-3-5:libreoffice-3-5 libreoffice-3-6:libreoffice-3-6 libreoffice-3-5-5:libreoffice-3-5-5 >> /home/gerritbot/syncgerrit.log 2>&1
