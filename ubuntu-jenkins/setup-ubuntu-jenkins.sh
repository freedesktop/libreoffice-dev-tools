#!/bin/sh
mkdir ${HOME}/.jenkins
cd ${HOME}/.jenkins
wget http://mirrors.jenkins-ci.org/war/latest/jenkins.war
wget https://github.com/downloads/KentBeck/junit/junit-4.9b2.jar
git archive --remote=git://anongit.freedesktop.org/libreoffice/contrib/dev-tools ubuntu-jenkins/jobs |tar x
echo "done."
echo "You can start your LibreOffice Ubuntu Jenkins server with: java -jar ~/.jenkins/jenkins.war"
echo "It will then be running at http://localhost:8080"
