# -*- tab-width: 4; indent-tabs-mode: nil; py-indent-offset: 4 -*-
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
# Major Contributor(s):
# Copyright (C) 2012 Red Hat, Inc., Michael Stahl <mstahl@redhat.com>
#  (initial developer)
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

import getopt
import os
import subprocess
import sys
import time
import uuid
import datetime

import signal
import threading
try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

try:
    import pyuno
    import uno
    import unohelper
except ImportError:
    print("pyuno not found: try to set PYTHONPATH and URE_BOOTSTRAP variables")
    print("PYTHONPATH=/installation/opt/program")
    print("URE_BOOTSTRAP=file:///installation/opt/program/fundamentalrc")
    raise

try:
    from com.sun.star.document import XDocumentEventListener
except ImportError:
    print("UNO API class not found: try to set URE_BOOTSTRAP variable")
    print("URE_BOOTSTRAP=file:///installation/opt/program/fundamentalrc")
    raise

### utilities ###

def partition(list, pred):
    left = []
    right = []
    for e in list:
        if pred(e):
            left.append(e)
        else:
            right.append(e)
    return (left, right)

def filelist(dir, suffix):
    if len(dir) == 0:
        raise Exception("filelist: empty directory")
    if not(dir[-1] == "/"):
        dir += "/"
    files = [dir + f for f in os.listdir(dir)]
#    print(files)
    return [f for f in files
                    if os.path.isfile(f) and os.path.splitext(f)[1] == suffix]

def getFiles(dirs, suffix):
    print( dirs )
    files = []
    for dir in dirs:
        files += filelist(dir, suffix)
    return files

### UNO utilities ###

class OfficeConnection:
    def __init__(self, args):
        self.args = args
        self.soffice = None
        self.socket = None
        self.xContext = None
        self.pro = None
    def setUp(self):
        (method, sep, rest) = self.args["--soffice"].partition(":")
        if sep != ":":
            raise Exception("soffice parameter does not specify method")
        if method == "path":
                socket = "pipe,name=pytest" + str(uuid.uuid1())
                try:
                    userdir = self.args["--userdir"]
                except KeyError:
                    raise Exception("'path' method requires --userdir")
                if not(userdir.startswith("file://")):
                    raise Exception("--userdir must be file URL")
                self.soffice = self.bootstrap(rest, userdir, socket)
        elif method == "connect":
                socket = rest
        else:
            raise Exception("unsupported connection method: " + method)
        self.xContext = self.connect(socket)

    def bootstrap(self, soffice, userdir, socket):
        argv = [ soffice, "--accept=" + socket + ";urp",
                "-env:UserInstallation=" + userdir,
                "--quickstart=no", "--nofirststartwizard",
                "--norestore", "--nologo", "--headless" ]
        if "--valgrind" in self.args:
            argv.append("--valgrind")
        self.pro = subprocess.Popen(argv)
        print(self.pro.pid)

    def connect(self, socket):
        xLocalContext = uno.getComponentContext()
        xUnoResolver = xLocalContext.ServiceManager.createInstanceWithContext(
                "com.sun.star.bridge.UnoUrlResolver", xLocalContext)
        url = "uno:" + socket + ";urp;StarOffice.ComponentContext"
        print("OfficeConnection: connecting to: " + url)
        while True:
            try:
                xContext = xUnoResolver.resolve(url)
                return xContext
#            except com.sun.star.connection.NoConnectException
            except pyuno.getClass("com.sun.star.connection.NoConnectException"):
                print("NoConnectException: sleeping...")
                time.sleep(1)

    def tearDown(self):
        if self.soffice:
            if self.xContext:
                try:
                    print("tearDown: calling terminate()...")
                    xMgr = self.xContext.ServiceManager
                    xDesktop = xMgr.createInstanceWithContext(
                            "com.sun.star.frame.Desktop", self.xContext)
                    xDesktop.terminate()
                    print("...done")
#                except com.sun.star.lang.DisposedException:
                except pyuno.getClass("com.sun.star.beans.UnknownPropertyException"):
                    print("caught UnknownPropertyException while TearDown")
                    pass # ignore, also means disposed
                except pyuno.getClass("com.sun.star.lang.DisposedException"):
                    print("caught DisposedException while TearDown")
                    pass # ignore
            else:
                self.soffice.terminate()
            ret = self.soffice.wait()
            self.xContext = None
            self.socket = None
            self.soffice = None
            if ret != 0:
                raise Exception("Exit status indicates failure: " + str(ret))
#            return ret
    def kill(self):
        command = "kill " + str(self.pro.pid)
        print("kill")
        print(command)
        os.system(command)

class PersistentConnection:
    def __init__(self, args):
        self.args = args
        self.connection = None
    def getContext(self):
        return self.connection.xContext
    def setUp(self):
        assert(not self.connection)
        conn = OfficeConnection(self.args)
        conn.setUp()
        self.connection = conn
    def preTest(self):
        assert(self.connection)
    def postTest(self):
        assert(self.connection)
    def tearDown(self):
        if self.connection:
            try:
                self.connection.tearDown()
            finally:
                self.connection = None
    def kill(self):
        if self.connection:
            self.connection.kill()

def simpleInvoke(connection, test):
    try:
        connection.preTest()
        test.run(connection.getContext(), connection)
    finally:
        connection.postTest()

def retryInvoke(connection, test):
    tries = 5
    while tries > 0:
        try:
            tries -= 1
            try:
                connection.preTest()
                test.run(connection.getContext(), connection)
                return
            finally:
                connection.postTest()
        except KeyboardInterrupt:
            raise # Ctrl+C should work
        except:
            print("retryInvoke: caught exception")
    raise Exception("FAILED retryInvoke")

def runConnectionTests(connection, invoker, tests):
    try:
        connection.setUp()
        for test in tests:
            invoker(connection, test)
    finally:
        pass
        #connection.tearDown()

class EventListener(XDocumentEventListener,unohelper.Base):
    def __init__(self):
        self.layoutFinished = False
    def documentEventOccured(self, event):
#        print(str(event.EventName))
        if event.EventName == "OnLayoutFinished":
            self.layoutFinished = True
    def disposing(event):
        pass

def mkPropertyValue(name, value):
    return uno.createUnoStruct("com.sun.star.beans.PropertyValue",
            name, 0, value, 0)

### tests ###

def loadFromURL(xContext, url):
    xDesktop = xContext.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.Desktop", xContext)
    props = [("Hidden", True), ("ReadOnly", True)] # FilterName?
    loadProps = tuple([mkPropertyValue(name, value) for (name, value) in props])
    xListener = EventListener()
    xGEB = xContext.ServiceManager.createInstanceWithContext(
        "com.sun.star.frame.GlobalEventBroadcaster", xContext)
    xGEB.addDocumentEventListener(xListener)
    try:
        xDoc = None
        xDoc = xDesktop.loadComponentFromURL(url, "_blank", 0, loadProps)
        time_ = 0
        while time_ < 30:
            if xListener.layoutFinished:
                return xDoc
            print("delaying...")
            time_ += 1
            time.sleep(1)
    except pyuno.getClass("com.sun.star.beans.UnknownPropertyException"):
        xListener = None
        raise # means crashed, handle it later
    except pyuno.getClass("com.sun.star.lang.DisposedException"):
        xListener = None
        raise # means crashed, handle it later
    except pyuno.getClass("com.sun.star.lang.IllegalArgumentException"):
        pass # means could not open the file, ignore it
    except:
        if xDoc:
            print("CLOSING")
            xDoc.close(True)
        raise
    finally:
        if xListener:
            xGEB.removeDocumentEventListener(xListener)

def handleCrash(file, disposed):
    print("File: " + file + " crashed")
    crashLog = open("crashlog.txt", "a")
    crashLog.write('Crash:' + file + ' ')
    if disposed == 1:
        crashLog.write('through disposed\n')
    crashLog.close()
#    crashed_files.append(file)
# add here the remaining handling code for crashed files

def alarm_handler(args):
    args.kill()

class LoadFileTest:
    def __init__(self, file, state):
        self.file = file
        self.state = state
    def run(self, xContext, connection):
        print("Loading document: " + self.file)
        t = None
        try:
            url = "file://" + quote(self.file)
            xDoc = None
            args = [connection]
            t = threading.Timer(45, alarm_handler, args)
            t.start()      
            xDoc = loadFromURL(xContext, url)
            self.state.goodFiles.append(self.file)
            t.cancel()
        except pyuno.getClass("com.sun.star.beans.UnknownPropertyException"):
            print("caught UnknownPropertyException " + self.file)
            if not t.is_alive():
                print("TIMEOUT!")
                self.state.timeoutFiles.append(self.file)
            else:
                t.cancel()
                handleCrash(self.file, 0)
                self.state.badPropertyFiles.append(self.file)
            connection.tearDown()
            connection.setUp()
        except pyuno.getClass("com.sun.star.lang.DisposedException"):
            print("caught DisposedException " + self.file)
            if not t.is_alive():
                print("TIMEOUT!")
                self.state.timeoutFiles.append(self.file)
            else:
                t.cancel()
                handleCrash(self.file, 1)
                self.state.badDisposedFiles.append(self.file)
            connection.tearDown()
            connection.setUp()
        finally:
            if t.is_alive():
                t.cancel()
            try:
                if xDoc:
                    xDoc.close(True)
            except pyuno.getClass("com.sun.star.beans.UnknownPropertyException"):
                print("caught UnknownPropertyException while closing")
                self.state.badPropertyFiles.append(self.file)
                connection.tearDown()
                connection.setUp()
            except pyuno.getClass("com.sun.star.lang.DisposedException"):
                print("caught DisposedException while closing")
                self.state.badDisposedFiles.append(self.file)
                connection.tearDown()
                connection.setUp()
            print("...done with: " + self.file)

class State:
    def __init__(self):
        self.goodFiles = []
        self.badDisposedFiles = []
        self.badPropertyFiles = []
        self.timeoutFiles = []

            
def writeReport(state, startTime):
    goodFiles = open("goodFiles.log", "w")
    goodFiles.write("All files tested which opened perfectly:\n")
    goodFiles.write("Starttime: " + startTime.isoformat() +"\n")
    for file in state.goodFiles:
        goodFiles.write(file)
        goodFiles.write("\n")
    goodFiles.close()
    badDisposedFiles = open("badDisposedFiles.log", "w")
    badDisposedFiles.write("All files tested which crashed:\n")
    badDisposedFiles.write("Starttime: " + startTime.isoformat() + "\n")
    for file in state.badDisposedFiles:
        badDisposedFiles.write(file)
        badDisposedFiles.write("\n")
    badDisposedFiles.close()
    badPropertyFiles = open("badPropertyFiles.log", "w")
    badPropertyFiles.write("All files tested which crashed:\n")
    badPropertyFiles.write("Starttime: " + startTime.isoformat() + "\n")
    for file in state.badPropertyFiles:
        badPropertyFiles.write(file)
        badPropertyFiles.write("\n")
    badPropertyFiles.close()
    timeoutFiles = open("timeoutFiles.log", "w")
    timeoutFiles.write("All files tested which timed out:\n")
    timeoutFiles.write("Starttime: " + startTime.isoformat() + "\n")
    for file in state.timeoutFiles:
        timeoutFiles.write(file)
        timeoutFiles.write("\n")
    timeoutFiles.close()


validFileExtensions = [ ".docx" , ".rtf", ".odt", ".fodt", ".doc" ]

def runLoadFileTests(opts, dirs):
    startTime = datetime.datetime.now()
    try:
        files = []
        for suffix in validFileExtensions:
            files.extend(getFiles(dirs, suffix))
        files.sort()
        state = State()
        tests = (LoadFileTest(file, state) for file in files)
        connection = PersistentConnection(opts)
        runConnectionTests(connection, simpleInvoke, tests)
    finally:
        connection.kill()
        writeReport(state, startTime)

def parseArgs(argv):
    (optlist,args) = getopt.getopt(argv[1:], "hr",
            ["help", "soffice=", "userdir=", "valgrind"])
#    print optlist
    return (dict(optlist), args)

def usage():
    message = """usage: {program} [option]... [directory]..."
 -h | --help:      print usage information
 --soffice=method:location
                   specify soffice instance to connect to
                   supported methods: 'path', 'connect'
 --userdir=URL     specify user installation directory for 'path' method
 --valgrind        pass --valgrind to soffice for 'path' method"""
    print(message.format(program = os.path.basename(sys.argv[0])))


if __name__ == "__main__":
    (opts,args) = parseArgs(sys.argv)
    if len(args) == 0:
        usage()
        sys.exit(1)
    if "-h" in opts or "--help" in opts:
        usage()
        sys.exit()
    elif "--soffice" in opts:
        runLoadFileTests(opts, args)
    else:
        usage()
        sys.exit(1)

# vim:set shiftwidth=4 softtabstop=4 expandtab:

