#!/bin/bash

#Sample: ./buildReleasesRepository.sh 6.3.0.0.alpha1 6.3.0.0.beta1 6.3.0.0.beta2 6.3.0.1 6.3.0.2 6.3.0.3 6.3.0.4

#Path to the folder where the tar.gz files are downloaded
rootDir=

#Path to the folder where 'bibisect-linux-64-releases' is
targetDir=

for var in "$@"
do
    date
    cd $rootDir
    input=$var
    if [[ $input = *"alpha"* ||  $input = *"beta"* ]]; then
        name="LibreOfficeDev_${input}_Linux_x86-64_deb"
        folder="libreofficedev"${input::3}
    else
        name="LibreOffice_${input}_Linux_x86-64_deb"
        folder="libreoffice"${input::3}
    fi
    file=${name}.tar.gz
    if [ ! -f $rootDir/$file ]; then
        echo "File $rootDir/$file not found!"
        url="https://downloadarchive.documentfoundation.org/libreoffice/old/${input}/deb/x86_64/${file}"
        echo "*** Downloading "
        wget -c ${url} -O $rootDir/${file}.tmp
        mv $rootDir/${file}.tmp $rootDir/${file}
    fi
    echo "*** Uncompressing file"
    tar -xvzf $rootDir/${file}
    echo "*** Uncompressing debs"
    for i in $rootDir/$name/DEBS/*.deb; do dpkg-deb -x $i $rootDir/$name/DEBS/ ; done
    echo "*** Moving files to opt/"
    mv $rootDir/$name/DEBS/opt/$folder/* $rootDir/$name/DEBS/opt/
    rm -r $rootDir/$name/DEBS/opt/$folder
    rm $rootDir/$name/DEBS/*.deb
    echo "*** Removing unneeded files"
    cd ${targetDir}
    LANG=C diff -qr ${rootDir}/$name/DEBS/opt ${targetDir}/opt | grep -w "Only in ${targetDir}/opt" | sed -r -e 's/^.*Only in //' -e 's@: @/@' | xargs git rm -r
    echo "*** Moving files to bibisect/"
    cd $rootDir
    cp -rf $rootDir/$name/DEBS/* ${targetDir}/
    echo "*** Removing files in origin"
    rm -rf $name
    cd ${targetDir}
    par1=libreoffice-$input
    echo "*** Creating commit $par1"
    git add opt/
    git commit . -m $par1 -m $file
    git clean -ffxd
    git tag -d $par1
    git tag -a $par1 -m $par1
done

git gc
