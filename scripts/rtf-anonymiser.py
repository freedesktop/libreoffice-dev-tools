#!/usr/bin/env python2
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#


import sys, getopt

def usage(code):
    print("Usage: %s [-i|--inline] input.rtf" % sys.argv[0])
    sys.exit(code)

class RtfParser:
    """This is meant to be a lightweight generic RTF parser. The purpose of
    this class is to provide methods to be overloaded for subclasses."""
    def __init__(self, input, inline):
        self.sock = open(input)
        self.out = []
        self.hexCount = 0

        while True:
            ch = self.sock.read(1)
            if not len(ch):
                break
            if ch in ("{", "}", chr(0x0d), chr(0x0a)):
                self.out.append(ch)
            elif ch == "\\":
                self.handleKeyword()
            else:
                self.handleChar(ch)

        self.sock.close()

        if not inline:
            sys.stdout.write("".join(self.out))
        else:
            self.sock = open(input, "w")
            self.sock.write("".join(self.out))
            self.sock.close()

    def handleKeyword(self):
        ch = self.sock.read(1)
        if not len(ch):
            return
        self.out.append("\\")
        if not ch.isalpha():
            if ch == "'":
                self.hexCount = 2
            self.out.append(ch)
            return
        while ch.isalpha():
            self.out.append(ch)
            ch = self.sock.read(1)
        if ch == "-":
            self.out.append(ch)
            ch = self.sock.read(1)
        if ch.isdigit():
            while ch.isdigit():
                self.out.append(ch)
                ch = self.sock.read(1)
        if ch == " ":
            self.handleChar(ch)
        else:
            self.sock.seek(self.sock.tell() - 1)

    def handleHexChar(self, ch):
        self.hexCount -= 1
        self.out.append(ch)

    def handleChar(self, ch):
        if self.hexCount > 0:
            self.handleHexChar(ch)
        else:
            self.out.append(ch)

class RtfAnonymiser(RtfParser):
    """This class only overloads handleChar() -- hopefully this removes all
    sensitive contents."""
    def __init__(self, input, inline):
        RtfParser.__init__(self, input, inline)

    def handleChar(self, ch):
        if self.hexCount > 0:
            self.handleHexChar(ch)
        else:
            if ch.isupper():
                self.out.append("X")
            else:
                self.out.append("x")

# opt parsing
inline = False
argv = sys.argv[1:]
try:
    opts, args = getopt.getopt(argv, "i", ["inline"])
except getopt.GetoptError:
    usage(0)
optind = 0
for opt, arg in opts:
    if opt in ("-i", "--inline"):
        inline = True
    optind += 1

if optind < len(argv):
    input = argv[optind]
else:
    usage(0)

RtfAnonymiser(input, inline)

# vim:set filetype=python shiftwidth=4 softtabstop=4 expandtab:
