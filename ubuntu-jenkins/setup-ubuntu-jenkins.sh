#!/bin/sh
set -e
case "$1" in
	-h | --help)
	cat << EOF
Usage: $(basename "$0") [OPTION]... [PATH]
Installs Jenkins in PATH if given or defaults to '~/.jenkins'

Options:
  -h, --help     display this help and exit
EOF
	exit 0;;
esac
instdir=${1:-~/.jenkins}
mkdir -p "$instdir"
cd "$instdir"
wget http://mirrors.jenkins-ci.org/war/latest/jenkins.war
wget --no-check-certificate https://github.com/downloads/KentBeck/junit/junit-4.9b2.jar
git clone git://anongit.freedesktop.org/libreoffice/contrib/dev-tools dev-tools
mv dev-tools/ubuntu-jenkins/jobs jobs
rm -rf dev-tools
echo "#!/bin/sh" > start-lo-jenkins.sh
echo 'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"' >> start-lo-jenkins.sh
echo 'java -DJENKINS_HOME=$SCRIPT_DIR -jar $SCRIPT_DIR/jenkins.war' >> start-lo-jenkins.sh
chmod u+x start-lo-jenkins.sh
echo "done."
echo "You can start your LibreOffice Ubuntu Jenkins server with: $(pwd)/start-lo-jenkins.sh"
echo "It will then be running at http://localhost:8080"

