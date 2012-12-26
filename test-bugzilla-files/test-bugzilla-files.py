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

def partition(list, pred): #defineer functie 'partition' met argumenten list en pred
    left = [] #nieuwe lijst left
    right = [] #nieuwe lijst rechts
    for e in list: #voor elke e in list
        if pred(e): #als 
            left.append(e) #linkse kant toevoegen aan lijst links
        else:
            right.append(e) #rechtse kant toevoegen aan lijst rechts
    return (left, right) #geef linkse en rechtse lijst terug

def filelist(dir, suffix): #defineer functie 'filelist' met argumenten dir en suffix
    if len(dir) == 0: #als de lengte van het argument dir gelijk is aan nul
        raise Exception("filelist: empty directory") #geef melding dat directory leeg is
    if not(dir[-1] == "/"): #als de directory niet met een / begint, een / voorzetten
        dir += "/"
    files = [dir + f for f in os.listdir(dir)] #lijst files is dir + f voor elke f die in os.listdir(dir) is
#    print(files)
    return [f for f in files 
                    if os.path.isfile(f) and os.path.splitext(f)[1] == suffix]

def getFiles(dirs, suffix): #defineer functie 'getfiles' met argumenten dirs en suffix
    print( dirs )
    files = [] #lege lijst
    for dir in dirs: #voor elke directory in dirs
        files += filelist(dir, suffix) #resultaat optellen bij files
    return files #files teruggeven

### UNO utilities ###

class OfficeConnection:
    def __init__(self, args):
        self.args = args
        self.soffice = None
        self.socket = None
        self.xContext = None
    def setUp(self):
        (method, sep, rest) = self.args["--soffice"].partition(":")
        if sep != ":": #als seperator niet gelijk is aan ":" 
            raise Exception("soffice parameter does not specify method") #soffice parameter is nt gespecifieerd
        if method == "path": #als methode gelijk is aan path
                socket = "pipe,name=pytest" + str(uuid.uuid1())
                try:
                    userdir = self.args["--userdir"] #probeer userdir 
                except KeyError:
                    raise Exception("'path' method requires --userdir") #userdir moet opgegeven worden
                if not(userdir.startswith("file://")): #als er geen URL wordt opgegeven
                    raise Exception("--userdir must be file URL") #melding URL nodig
                self.soffice = self.bootstrap(rest, userdir, socket)
        elif method == "connect": #als methode connect is
                socket = rest #socket laten rusten
        else: # andere methoden worden niet 
            raise Exception("unsupported connection method: " + method)
        self.xContext = self.connect(socket)

    def bootstrap(self, soffice, userdir, socket): #defineer fctie 'bootstrap' met soffice, userdir, socket
        argv = [ soffice, "--accept=" + socket + ";urp",
                "-env:UserInstallation=" + userdir,
                "--quickstart=no", "--nofirststartwizard",
                "--norestore", "--nologo", "--headless" ] 
        if "--valgrind" in self.args: #als valgrind voorkomt in argS
            argv.append("--valgrind") #valgrid toevoegen aan argv
        return subprocess.Popen(argv) #waarde argv teruggeven 'Execute a child program in a new process.'

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
                    xDesktop.terminate() #afsluiten
                    print("...done")
#                except com.sun.star.lang.DisposedException:
                except pyuno.getClass("com.sun.star.beans.UnknownPropertyException"):
                    print("caught UnknownPropertyException")
                    print("crashed")
                    pass # ignore, also means disposed
                except pyuno.getClass("com.sun.star.lang.DisposedException"):
                    print("caught DisposedException")
                    print("crashed")
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

class PerTestConnection:
    def __init__(self, args):
        self.args = args
        self.connection = None
    def getContext(self):
        return self.connection.xContext
    def setUp(self):
        assert(not(self.connection))
    def preTest(self):
        conn = OfficeConnection(self.args)
        conn.setUp()
        self.connection = conn
    def postTest(self):
        if self.connection:
            try:
                self.connection.tearDown()
            finally:
                self.connection = None
    def tearDown(self):
        assert(not(self.connection))

class PersistentConnection:
    def __init__(self, args):
        self.args = args
        self.connection = None
    def getContext(self):
        return self.connection.xContext
    def setUp(self):
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
        connection.tearDown()

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
# we need to check if this method returns after loading or after invoking the loading
# depending on this we might need to put a timeout around it
        xDoc = None
        xDoc = xDesktop.loadComponentFromURL(url, "_blank", 0, loadProps)
        time_ = 0
        while time_ < 30:
            if xListener.layoutFinished:
                return xDoc
            print("delaying...")
            time_ += 1
            time.sleep(1)
        print("timeout: no OnLayoutFinished received")
        return xDoc
    except pyuno.getClass("com.sun.star.beans.UnknownPropertyException"):
        raise # means crashed, handle it later
    except pyuno.getClass("com.sun.star.lang.DisposedException"):
        raise # means crashed, handle it later
    except:
        if xDoc:
            print("CLOSING")
            xDoc.close(True)
        raise
    finally:
        if xListener:
            xGEB.removeDocumentEventListener(xListener)

def handleCrash(file):
    print("File: " + file + " crahsed")
# add here the remaining handling code for crashed files

class LoadFileTest:
    def __init__(self, file):
        self.file = file
    def run(self, xContext, connection):
        print("Loading document: " + self.file)
        try:
            url = "file://" + quote(self.file)
            xDoc = None
            xDoc = loadFromURL(xContext, url)
        except pyuno.getClass("com.sun.star.beans.UnknownPropertyException"):
            print("caught UnknownPropertyException " + self.file)
            connection.setUp()
            handleCrash(file)
        except pyuno.getClass("com.sun.star.lang.DisposedException"):
            print("caught DisposedException " + self.file)
            connection.setUp()
            handleCrash(file)
        finally:
            if xDoc:
                xDoc.close(True)
            print("...done with: " + self.file)

def runLoadFileTests(opts, dirs, suffix):
    files = getFiles(dirs, suffix)
    tests = (LoadFileTest(file) for file in files)
    connection = PersistentConnection(opts)
#    connection = PerTestConnection(opts)
    runConnectionTests(connection, simpleInvoke, tests)

def parseArgs(argv):
    (optlist,args) = getopt.getopt(argv[1:], "hr",
            ["help", "soffice=", "userdir=", "valgrind"])
#    print optlist
    return (dict(optlist), args)

def usage(): #te gebruiken tags
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
    if len(args) == 0: #als lengte van args nul is -> afsluiten
        usage() #print de verschillende mogelijkheden
        sys.exit(1)
    if "-h" in opts or "--help" in opts: #
        usage() #print de verschillende mogelijkheden
        sys.exit() #als -h of --help wordt ingegeven -> ?
    elif "--soffice" in opts: #als --soffice in opts voorkomt
        runLoadFileTests(opts, args, ".odt")
    else:
        usage()
        sys.exit(1)

# vim:set shiftwidth=4 softtabstop=4 expandtab:

