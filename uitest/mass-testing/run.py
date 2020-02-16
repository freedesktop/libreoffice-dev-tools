#!/usr/bin/env python3
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#

import os
import argparse
from subprocess import Popen, PIPE, TimeoutExpired
import sys
import signal
import logging
from shutil import copyfile
import pickle
import time
import fcntl
import tempfile

extensions = {
    'writer' : [ "odt", "doc", "docx", "rtf" ],
    'calc' : [ "ods", "xls", "xlsx" ],
    'impress' : [ "odp", "ppt", "pptx" ]
    }

def signal_handler(sig, frame):
        print('Ctrl+C pressed! Killing it!')
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

class DefaultHelpParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

def start_logger(component):
    rootLogger = logging.getLogger()
    rootLogger.setLevel(os.environ.get("LOGLEVEL", "INFO"))

    logFormatter = logging.Formatter("%(asctime)s %(message)s")
    fileHandler = logging.FileHandler("./logs/" + component + ".log")
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    streamHandler = logging.StreamHandler(sys.stdout)
    rootLogger.addHandler(streamHandler)

    return rootLogger

def get_file_names(component, filesPath):
    auxNames = []
    for fileName in os.listdir(filesPath):
        for ext in extensions[component]:
            if fileName.endswith(ext):
                auxNames.append("file:///" + filesPath + fileName)

                #Remove previous lock files
                lockFilePath = filesPath + '.~lock.' + fileName + '#'
                if os.path.isfile(lockFilePath):
                    os.remove(lockFilePath)

    return auxNames

def run_tests_and_get_results(liboPath, listFiles, isDebug, isResume):

    results = {
        'pass' : 0,
        'fail' : 0,
        'timeout' : 0,
        'skip' : 0}

    sofficePath = liboPath + "instdir/program/soffice"
    process = Popen([sofficePath, "--version"], stdout=PIPE, stderr=PIPE)
    stdout = process.communicate()[0].decode("utf-8")
    sourceHash = stdout.split(" ")[2].strip()

    #Keep track of the files run
    filesRun = {}

    if isResume:
        pklFile = './logs/' + component + '.pkl'
        if os.path.exists(pklFile):
            with open(pklFile, 'rb') as pickle_in:
                filesRun = pickle.load(pickle_in)

        if sourceHash not in filesRun:
            filesRun[sourceHash] = {'files': []}

        if 'results' in filesRun[sourceHash]:
            results = filesRun[sourceHash]['results']

    for fileName in listFiles:

        if isResume:
            if fileName in filesRun[sourceHash]['files']:
                print("SKIP: " + fileName)
                continue

        #Create temp directory for the user profile
        with tempfile.TemporaryDirectory() as tmpdirname:
            profilePath = os.path.join(tmpdirname, 'libreoffice/4')
            userPath = os.path.join(profilePath, 'user')
            os.makedirs(userPath)

            # Replace the profile file with
            # 1. DisableMacrosExecution = True
            # 2. IgnoreProtectedArea = True
            # 3. AutoPilot = False
            copyfile(os.getcwd() + '/registrymodifications.xcu', userPath + '/registrymodifications.xcu')

            #TODO: Find a better way to pass fileName parameter
            os.environ["TESTFILENAME"] = fileName

            process = Popen(["python3",
                        liboPath + "uitest/test_main.py",
                        "--debug",
                        "--soffice=path:" + sofficePath,
                        "--userdir=file://" + profilePath,
                        "--file=" + component + ".py"], stdin=PIPE, stdout=PIPE, stderr=PIPE,
                        preexec_fn=os.setsid)

            # Do not block on process.stdout
            fcntl.fcntl(process.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)

            # Kill the process if:
            # 1. The file can't be loaded in 'fileInterval' seconds
            # 2. The test can't be executed in 'testInterval' seconds
            fileInterval = 10
            testIternval = 20
            timeout = time.time() + fileInterval
            notLoaded = True
            while True:
                time.sleep(1)

                if time.time() > timeout:
                    if notLoaded:
                        logger.info("SKIP: " + fileName)
                        results['skip'] += 1
                    else:
                        logger.info("TIMEOUT: " + fileName)
                        results['timeout'] += 1

                    # kill popen process
                    os.killpg(process.pid, signal.SIGKILL)
                    break

                try:
                    outputLines = process.stdout.readlines()
                except IOError:
                    pass

                importantInfo = ''
                isFailure = False
                for line in outputLines:
                    line = line.decode("utf-8").strip()

                    if not line:
                        continue

                    if isDebug:
                        print(line)

                    if line.startswith("mass-uitesting:"):
                        message = line.split(":")[1]
                        if message == 'skipped':
                            logger.info("SKIP: " + fileName + " : " + importantInfo)
                            results['skip'] += 1

                            # kill popen process
                            os.killpg(process.pid, signal.SIGKILL)

                            break
                        elif message == 'loaded':
                            notLoaded = False

                            #Extend timeout
                            timeout += testIternval

                    elif 'Execution time' in line:
                        importantInfo = line.split('for ')[1]

                    elif importantInfo and 'error' == line.lower() or 'fail' == line.lower():
                        isFailure = True

                if importantInfo:
                    if isFailure:
                        logger.info("FAIL: " + fileName + " : " + importantInfo)
                        results['fail'] += 1
                    else:
                        # No error found between the Execution time line and the end of stdout
                        logger.info("PASS: " + fileName + " : " + str(importantInfo))
                        results['pass'] += 1

                if process.poll() is not None:
                    break

            if isResume:
                filesRun[sourceHash]['files'].append(fileName)

                filesRun[sourceHash]['results'] = results

                with open(pklFile, 'wb') as pickle_out:
                    pickle.dump(filesRun, pickle_out)


    totalTests = sum(results.values())
    if totalTests > 0:
        logger.info("")
        logger.info("Total Tests: " + str(totalTests))
        logger.info("\tPASS: " + str(results['pass']))
        logger.info("\tSKIP: " + str(results['skip']))
        logger.info("\tTIMEOUT: " + str(results['timeout']))
        logger.info("\tFAIL: " + str(results['fail']))
        logger.info("")
    else:
        print("No test run!")

if __name__ == '__main__':
    parser = DefaultHelpParser()

    parser.add_argument(
            '--dir', required=True, help="Path to the files directory")
    parser.add_argument(
            '--soffice', required=True, help="Path to the LibreOffice directory")
    parser.add_argument(
            '--debug', action='store_true', help="Flag to print output")
    parser.add_argument(
            '--resume', action='store_true', help="Flag to resume previous runs")
    parser.add_argument(
            '--component', required=True, help="The component to be used. Options: " + \
                    " ".join("[" + x + "]" for x in extensions.keys()))

    argument = parser.parse_args()

    component = argument.component.lower()
    if component not in extensions.keys():
        parser.error(component + " is an invalid component.")

    filesPath = os.path.join(argument.dir, '')
    if not os.path.exists(filesPath):
        parser.error(filesPath + " is an invalid directory path")

    liboPath = os.path.join(argument.soffice, '')
    if not os.path.exists(liboPath) or not os.path.exists(liboPath + "instdir/program/"):
        parser.error(liboPath + " is an invalid LibreOffice path")

    os.environ["PYTHONPATH"] = liboPath + "instdir/program/"
    os.environ["URE_BOOTSTRAP"] = "file://" + liboPath + "instdir/program/fundamentalrc"
    os.environ["SAL_USE_VCLPLUGIN"] = "gen"

    if not os.path.exists('./logs'):
        os.makedirs('./logs')

    logger = start_logger(component)

    listFiles = get_file_names(component, filesPath)
    listFiles.sort()

    run_tests_and_get_results(liboPath, listFiles, argument.debug, argument.resume)

# vim: set shiftwidth=4 softtabstop=4 expandtab:
