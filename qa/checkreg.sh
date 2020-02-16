#!/bin/bash
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

### DESCRIPTION
#
# This script is for triaging fileopen and filesave bugs in LibreOffice
# using command line conversion.
# It expects a checkreg.config file, where you specify the LibreOffice
# executables, version identifiers and the output directory.
# It produces PDFs with the version identifier appended to the file name.
# In case of filesave, the saved documents are likewise left in the output directory.
# It works in *nix systems and cygwin on Windows. It is not POSIX-compatible (using arrays).
# You can use it with bibisect repos just as well as versions installed in parallel.

usage="
To get PDFs of fileopen with different versions into the specified outdir, run with
./checkreg.sh open /path/to/file.ext
To get PDFs of filesave to original format, run with
./checkreg.sh save /path/to/file.ext
To get PDFs of filesave to a different format, run with a third argument
./checkreg.sh save /path/to/file.ext odt
In cygwin, give input file argument in the format 'c:\users\test\downloads\myfile.docx'
"
if [ ! "$2" ]; then
    echo "$usage"
    exit 1
fi
dir="$(dirname "${BASH_SOURCE[0]}")"
. "$dir"/checkreg.config
convType="$1"
inputFile="$2"
if [[ "$3" && $convType == "save" ]]; then
    fileType="$3"
else
    fileType="${inputFile##*.}"
fi
# file name and path with extension removed
pathNoExt="${inputFile%.*}"
# file name with extension removed
nameNoExt="$(basename "${pathNoExt}")"
# directory name with no filename and no trailing slash
inputDir="$(dirname "${inputFile}")"
# add a trailing slash to outDir, if needed
[[ "${outDir}" != */ ]] && outDir="${outDir}/"
for version in "${!versions[@]}";
do
    verName="${pathNoExt}$version.${inputFile##*.}"
    pdfName="${nameNoExt}.pdf"
    pdfTarget="${nameNoExt}$version.pdf"
    if [[ "$3" && $convType == "save" ]]; then
        verBase="$(basename "${pathNoExt}$version.$fileType")"
    else
        verBase="$(basename "${verName}")"
    fi
    if [[ $convType == "open" ]]; then
        # if version starts with 3, we use a single dash for the switches
        if [[ ${version::1} == "3" ]]; then
            "${versions[$version]}" -headless -nolockcheck -convert-to pdf -outdir "${outDir}" "${inputFile}"
        else
            "${versions[$version]}" --headless --nolockcheck --convert-to pdf --outdir "${outDir}" "${inputFile}"
        fi
        if ! mv "${outDir}${pdfName}" "${outDir}${pdfTarget}"; then
            echo "PDF creation for version $version failed"
            rm "${outDir}.~lock.${nameNoExt}.pdf#"
        fi
    elif [[ $convType == "save" ]]; then
        cp "${inputFile}" "${verName}";
        echo "Converting version $version to ${fileType}"
        if [[ ${version::1} == "3" ]]; then
            "${versions[$version]}" -headless -nolockcheck -convert-to "${fileType}" -outdir "${outDir}" "${verName}"
            "${versions[$version]}" -headless -nolockcheck -convert-to pdf -outdir "${outDir}" "${outDir}${verBase}"
        else
            "${versions[$version]}" --headless --nolockcheck --convert-to "${fileType}" --outdir "${outDir}" "${verName}"
            "${versions[$version]}" --headless --nolockcheck --convert-to pdf --outdir "${outDir}" "${outDir}${verBase}"
        fi
        rm "${verName}"
    fi
done

# vim:set shiftwidth=4 softtabstop=4 expandtab:
