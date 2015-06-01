#!/bin/sh

# To Remove Thumbnail with its respective file entry in manifest.xml from LibreOffice Test Documents to conserve space
# Usage: "./optimize.sh" "file_name.odt" Add relevant addresses if files are not in current working directory
# Caution: Please make a copy of original file for backup. This script directly alters the original file
# After running this script observe the change in size
set -e
cmdfolder=$(realpath "$1")
echo $cmdfolder
zip -d "$cmdfolder" "Thumbnails/*"
TMPDIR=$(mktemp -d)
unzip -j "$cmdfolder" "META-INF/manifest.xml" -d "$TMPDIR/META-INF/"
cd "$TMPDIR/META-INF/"
mv manifest.xml temp.xml
grep -v "thumbnail" temp.xml > manifest.xml
rm temp.xml
cd ..
zip -u "$cmdfolder" "META-INF/manifest.xml"
rm -rf "$TMPDIR"
