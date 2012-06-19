#!/usr/bin/env python

'''
Created on 19.06.2012

@author: david ostrovsky
'''

from subprocess import check_output, STDOUT
from json import loads
import getopt, sys
#from pprint import pprint

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hs:g:b:p:", ["help", "status=", "gerrit=", "branch=", "project="])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    gerrit_host_name = None
    status = None
    project = None
    branch = None    
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-s", "--status"):
            status = a
        elif o in ("-g", "--gerrit"):
            gerrit_host_name = a
        elif o in ("-p", "--project"):
            project = a
        elif o in ("-b", "--branch"):
            branch = a
        else:
            assert False, "unhandled option"
    if branch == None or gerrit_host_name == None or status == None or project == None or branch == None:
        usage()
        sys.exit(2)
    
    cmd = "ssh " + gerrit_host_name + " gerrit query --format=JSON status:" + status + " project:core branch:master"
    lines = check_output(cmd, shell=True, stderr=STDOUT).strip()
    for chunk in lines.split("\n"):
        data = loads(chunk)
        #pprint(data)
        if 'url' in data.keys():
            print data['url'] + " \"" + data['subject'] + "\" " + data['owner']['email'] 
    
def usage():
    print """gerrit_daily_digest.py
    -g --gerrit (i. e. logerrit or gerrit.libreoffice.org, use alias in your ~/.ssh(config with your public key)
    -s --status (open, merged, abandoned)
    -p --project (i. e. core)
    -b --branch (i. e. master)
    -v --verbose
    -h --help
    Example: gerrit_daily_digest.py -g logerrit -s merged -p core -b master
    """

if __name__ == "__main__":
    main()
