#!/bin/sh
set -e
mkdir ${HOME}/.jenkins
cd ${HOME}/.jenkins
wget http://mirrors.jenkins-ci.org/war/latest/jenkins.war
wget --no-check-certificate https://github.com/downloads/KentBeck/junit/junit-4.9b2.jar
git clone git://anongit.freedesktop.org/libreoffice/contrib/dev-tools dev-tools
mv dev-tools/ubuntu-jenkins/jobs jobs
rm -rf dev-tools
echo "done."
echo "You can start your LibreOffice Ubuntu Jenkins server with: java -jar ~/.jenkins/jenkins.war"
echo "It will then be running at http://localhost:8080"
