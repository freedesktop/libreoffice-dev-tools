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
import time
import fcntl
import tempfile
import multiprocessing
from multiprocessing_logging import install_mp_handler

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

def kill_soffice():
    p = Popen(['ps', '-A'], stdout=PIPE)
    out, err = p.communicate()
    for line in out.splitlines():
        if b'soffice' in line:
            pid = int(line.split(None, 1)[0])
            print("Killing process: " + str(pid))
            os.kill(pid, signal.SIGKILL)

def start_logger(name):
    rootLogger = logging.getLogger()
    rootLogger.setLevel(os.environ.get("LOGLEVEL", "INFO"))

    logFormatter = logging.Formatter("%(asctime)s %(message)s")
    fileHandler = logging.FileHandler(name)
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    streamHandler = logging.StreamHandler(sys.stdout)
    rootLogger.addHandler(streamHandler)

    return rootLogger

def get_file_names(filesPath):
    auxNames = []
    for fileName in os.listdir(filesPath):
        for key, val in extensions.items():
            extension = os.path.splitext(fileName)[1][1:]
            if extension in val:
                auxNames.append("file:///" + filesPath + fileName)

                #Remove previous lock files
                lockFilePath = filesPath + '.~lock.' + fileName + '#'
                if os.path.isfile(lockFilePath):
                    os.remove(lockFilePath)
                break

    return auxNames

def launchLibreOffice(logger, fileName, sofficePath, component, countInfo, isDebug):
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
                    './uitest/test_main.py',
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
        fileInterval = 30
        testInterval = 20
        timeout = time.time() + fileInterval
        notLoaded = True
        while True:
            time.sleep(0.1)

            if time.time() > timeout:
                if notLoaded:
                    logger.info(countInfo + " - SKIP: " + fileName)
                else:
                    logger.info(countInfo + " - TIMEOUT: " + fileName)

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
                        logger.info(countInfo + " - SKIP: " + fileName + " : " + importantInfo)

                        # kill popen process
                        os.killpg(process.pid, signal.SIGKILL)

                        break
                    elif message == 'loaded':
                        notLoaded = False

                        #Extend timeout
                        timeout += testInterval

                elif 'Execution time' in line:
                    importantInfo = line.split('for ')[1]

                elif importantInfo and 'error' == line.lower() or 'fail' == line.lower():
                    isFailure = True

            if importantInfo:
                if isFailure:
                    logger.info(countInfo + " - FAIL: " + fileName + " : " + importantInfo)
                else:
                    # No error found between the Execution time line and the end of stdout
                    logger.info(countInfo + " - PASS: " + fileName + " : " + str(importantInfo))

            if process.poll() is not None:
                break

def run_tests_and_get_results(sofficePath, listFiles, isDebug):

    process = Popen([sofficePath, "--version"], stdout=PIPE, stderr=PIPE)
    stdout = process.communicate()[0].decode("utf-8")
    sourceHash = stdout.split(" ")[2].strip()

    if not os.path.exists('./logs'):
        os.makedirs('./logs')

    logName = './logs/' + sourceHash + ".log"
    logger = start_logger(logName)

    previousLog = ""
    if os.path.exists(logName):
        with open(logName, 'r') as file:
            previousLog = file.read()

    kill_soffice()
    cpuCount = multiprocessing.cpu_count() #use all CPUs
    chunkSplit = cpuCount * 16
    chunks = [listFiles[x:x+chunkSplit] for x in range(0, len(listFiles), chunkSplit)]
    totalCount = len(listFiles)

    count = 0
    for chunk in chunks:
        install_mp_handler()
        pool = multiprocessing.Pool(cpuCount)
        for fileName in chunk:
            count += 1
            countInfo = str(count) + '/' + str(totalCount)

            if fileName in previousLog:
                print(countInfo + " - SKIP: " + fileName)
                continue

            extension = os.path.splitext(fileName)[1][1:]

            for key, val in extensions.items():
                if extension in val:
                    component = key
                    break

            pool.apply_async(launchLibreOffice,
                    args=(logger, fileName, sofficePath, component, countInfo, isDebug))

        pool.close()
        pool.join()

        kill_soffice()


if __name__ == '__main__':
    currentPath = os.path.dirname(os.path.realpath(__file__))
    uitestPath = os.path.join(currentPath, 'uitest/test_main.py')
    if not os.path.exists(uitestPath):
        print("ERROR: " + uitestPath + " doesn't exists. " + \
                "Copy uitest folder from LibreOffice codebase and paste it here")
        sys.exit(1)

    parser = DefaultHelpParser()

    parser.add_argument(
            '--dir', required=True, help="Path to the files directory")
    parser.add_argument(
            '--soffice', required=True, help="Path to the LibreOffice directory")
    parser.add_argument(
            '--debug', action='store_true', help="Flag to print output")

    argument = parser.parse_args()

    filesPath = os.path.join(argument.dir, '')
    if not os.path.exists(filesPath):
        parser.error(filesPath + " is an invalid directory path")

    sofficePath = argument.soffice
    if not os.path.exists(sofficePath) or not sofficePath.endswith('/soffice'):
        parser.error(sofficePath + " is an invalid LibreOffice path")

    os.environ["PYTHONPATH"] = sofficePath.split('/soffice')[0]
    os.environ["URE_BOOTSTRAP"] = "file://" + sofficePath.split('/soffice')[0] + '/fundamentalrc'
    os.environ["SAL_USE_VCLPLUGIN"] = "gen"

    listFiles = get_file_names(filesPath)
    listFiles.sort()

    run_tests_and_get_results(sofficePath, listFiles, argument.debug)

# vim: set shiftwidth=4 softtabstop=4 expandtab:
