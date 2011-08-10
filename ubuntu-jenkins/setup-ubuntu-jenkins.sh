#!/bin/sh
set -e
mkdir jenkins
cd jenkins
wget http://mirrors.jenkins-ci.org/war/latest/jenkins.war
wget --no-check-certificate https://github.com/downloads/KentBeck/junit/junit-4.9b2.jar
git clone git://anongit.freedesktop.org/libreoffice/contrib/dev-tools dev-tools
mv dev-tools/ubuntu-jenkins/jobs jobs
rm -rf dev-tools
cd ..
echo "#!bin/sh" > start-lo-jenkins.sh
echo "java -DJENKINS_HOME=$(pwd)/jenkins -jar $(pwd)/jenkins/jenkins.war">> start-lo-jenkins.sh
chmod u+x start-lo-jenkins.sh
echo "done."
echo "You can start your LibreOffice Ubuntu Jenkins server with: $(pwd)/start-lo-jenkins.sh"
echo "It will then be running at http://localhost:8080"

