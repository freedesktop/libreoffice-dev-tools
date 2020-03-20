#!/usr/bin/env python3
# Version: MPL 1.1 / GPLv3+ / LGPLv3+
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License or as specified alternatively below. You may obtain a copy of
# the License at http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# All Rights Reserved.
#
# For minor contributions see the git repository.
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 3 or later (the "GPLv3+"), or
# the GNU Lesser General Public License Version 3 or later (the "LGPLv3+"),
# in which case the provisions of the GPLv3+ or the LGPLv3+ are applicable
# instead of those above.

import argparse
import sys
import os
import multiprocessing
import tempfile
import time
import subprocess
import logging
from multiprocessing_logging import install_mp_handler

extensions = [ "odt", "doc", "docx", "rtf", "ods", "xls", "xlsx", "odp", "ppt", "pptx" ]

importTimeout = 300

def start_logger(fileName):
    rootLogger = logging.getLogger()
    rootLogger.setLevel(os.environ.get("LOGLEVEL", "INFO"))

    logFormatter = logging.Formatter("[%(asctime)s] %(message)s")
    fileHandler = logging.FileHandler(fileName)
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    streamHandler = logging.StreamHandler(sys.stdout)
    streamHandler.setFormatter(logFormatter)
    rootLogger.addHandler(streamHandler)

    return rootLogger

class DefaultHelpParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

def get_file_names(filesPath):
    auxNames = []
    for fileName in os.listdir(filesPath):
        for ext in extensions:
            if fileName.endswith(ext):
                auxNames.append("file:///" + filesPath + fileName)

                #Remove previous lock files
                lockFilePath = filesPath + '.~lock.' + fileName + '#'
                if os.path.isfile(lockFilePath):
                    os.remove(lockFilePath)

    return auxNames

def launchLibreOffice(fileName, soffice):
    with tempfile.TemporaryDirectory() as tmpdirname:
        profilePath = os.path.join(tmpdirname, 'libreoffice/4')
        userPath = os.path.join(profilePath, 'user')
        os.makedirs(userPath)

        argv = [ soffice + 'instdir/program/soffice',
                "-env:UserInstallation=file://" + userPath,
                "--quickstart=no", "--headless", "--nofirststartwizard",
                "--norestore", "--nologo"]
        argv.append(fileName)

        diffTime = None
        try:
            start_time = time.time()
            subprocess.run(argv, stderr=subprocess.DEVNULL, timeout=importTimeout)
            diffTime = time.time() - start_time
        except subprocess.TimeoutExpired:
            diffTime = importTimeout

        logger.info(fileName + ' - ' + str(diffTime))

if __name__ == '__main__':
    parser = DefaultHelpParser()

    parser.add_argument(
            '--dir', required=True, help="Path to the files directory")
    parser.add_argument(
            '--soffice', required=True, help="Path to the LibreOffice directory")
    argument = parser.parse_args()

    filesPath = os.path.join(argument.dir, '')
    if not os.path.exists(filesPath):
        parser.error(filesPath + " is an invalid directory path")

    liboPath = os.path.join(argument.soffice, '')
    if not os.path.exists(liboPath) or not os.path.exists(liboPath + "instdir/program/"):
        parser.error(liboPath + " is an invalid LibreOffice path")

    listFiles = get_file_names(filesPath)
    listFiles.sort()

    os.environ["OOO_EXIT_POST_STARTUP"] = "1"

    sofficePath = liboPath + "instdir/program/soffice"
    process = subprocess.Popen([sofficePath, "--version"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = process.communicate()[0].decode("utf-8")
    sourceHash = stdout.split(" ")[2].strip()

    logFile = sourceHash + '.log'
    logger = start_logger(logFile)

    previousResults = []
    if os.path.exists(logFile):
        with open(logFile) as f:
            for line in f:
                previousResults.append(line.strip().split(' ')[2])

    install_mp_handler()
    pool = multiprocessing.Pool() # use all CPUs
    manager = multiprocessing.Manager()
    totalCount = 0

    for fileName in listFiles:
        if fileName not in previousResults:
            totalCount += 1
            pool.apply_async(launchLibreOffice, args=(fileName, liboPath))

    pool.close()
    pool.join()

    print()
    if totalCount:
        print(str(totalCount) + " new results added to " + logFile)
    else:
        print("No new results added to " + logFile)

# vim:set shiftwidth=4 softtabstop=4 expandtab:
