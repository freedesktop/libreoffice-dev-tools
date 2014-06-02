#!/usr/bin/env python

import os
import sys
import subprocess
import getopt

dirs = [ "doc", "docx", "fods", "fodt", "ods", "odt", "rtf", "xls", "xlsx" ]

calc = [ "fods", "ods", "xls", "xlsx" ]

writer = [ "doc", "docx", "fodt", "odt", "rtf" ]

impress = [ "ppt", "pptx", "odp", "fodp" ]

draw = [ "odg", "fodg" ]

reverse = [ "wpd", "vsd", "pub", "cdr", "vdx" ]

def get_execute_scripts(opts):
    top_dir = os.getcwd()
    valid_dirs = []
    if "--writer" in opts:
        valid_dirs.extend( [ os.path.join(top_dir, dir) for dir in writer if os.path.isdir(os.path.join(top_dir,dir)) ] )
    if "--calc" in opts:
        valid_dirs.extend( [ os.path.join(top_dir, dir) for dir in calc if os.path.isdir(os.path.join(top_dir,dir)) ] )
    if "--impress" in opts:
        valid_dirs.extend( [ os.path.join(top_dir, dir) for dir in impress if os.path.isdir(os.path.join(top_dir,dir)) ] )
    if "--draw" in opts:
        valid_dirs.extend( [ os.path.join(top_dir, dir) for dir in draw if os.path.isdir(os.path.join(top_dir,dir)) ] )
    if "--reverse" in opts:
        valid_dirs.extend( [ os.path.join(top_dir, dir) for dir in reverse if os.path.isdir(os.path.join(top_dir,dir)) ] )
    #print valid_dirs
    valid_execute_files = { dir: os.path.join(dir, "execute.sh") for dir in valid_dirs if os.path.isfile(os.path.join(dir, "execute.sh")) }
    #print valid_execute_files
    return valid_execute_files

def execute_scripts(opts):
    valid_execute_scripts = get_execute_scripts(opts)
    for dir, file in valid_execute_scripts.iteritems():
        print("start script in " + dir)
        command = "nohup " + file
        os.chdir(dir)
        print(file)
        print(os.getcwd())
        subprocess.Popen("nohup ./execute.sh&", shell=True)
        pass

def parseArgs(argv):
    (optlist,args) = getopt.getopt(argv[1:], "h",
                        ["help", "calc", "writer", "impress", "draw", "reverse"])
    #    print optlist
    return (dict(optlist), args)

def usage():
    message = """usage: {program} [option]"
-h | --help: print usage information
--calc: test all files
--calc: test calc files
--writer: test writer files
--impress: test impress files
--draw: test draw files
--reverse: test reverse engineered file formats"""
    print(message.format(program = (os.path.basename(sys.argv[0]))))

if __name__ == "__main__":
    print(sys.argv)
    (opts,args) = parseArgs(sys.argv)
    if "-h" in opts or "--help" in opts:
        usage()
        sys.exit()
    elif len(opts) == 0:
        usage()
        sys.exit()
    elif "--writer" in opts or "--calc" in opts or "--impress" in opts or "--draw" in opts or "--reverse" in opts or "--all" in opts:
        print(os.getcwd())
        print(os.listdir(os.getcwd()))
        execute_scripts(opts)
