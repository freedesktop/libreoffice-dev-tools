#!/usr/bin/env python
########################################################################
#
#  Copyright (c) 2010 Kohei Yoshida
#  
#  Permission is hereby granted, free of charge, to any person
#  obtaining a copy of this software and associated documentation
#  files (the "Software"), to deal in the Software without
#  restriction, including without limitation the rights to use,
#  copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following
#  conditions:
#  
#  The above copyright notice and this permission notice shall be
#  included in all copies or substantial portions of the Software.
#  
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#  OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#  NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#  OTHER DEALINGS IN THE SOFTWARE.
#
########################################################################

import sys, os, os.path, optparse, subprocess

class ParseError(Exception): pass

class SingleModeError(Exception): pass

class ViewerError(Exception): pass

arg_desc = "module1 module2 ..."

desc = """
Execute this script at the root directory of your OOo build tree.  It parses
all build.lst files found in the modules and outputs module dependency data 
in the dot compatible format.

When no arguments are given, it prints dependencies of all discovered 
modules.  When module names are given as arguments, it only traces 
dependencies of those modules.

Sometimes modules are referenced in the build.lst but are absent from the 
source tree.  Those missing modules are displayed red in the dependency graph."""

err_missing_modules = """
The following modules are mentioned but not present in the source tree:"""

class Module(object):

    def __init__ (self, name):
        self.name = name
        self.deps  = {} # dependents
        self.precs = {} # precedents

# Store all unique dependency set, with no duplicates.
class DependSet(object):

    def __init__ (self):
        self.modules = {}

    def insert_depend (self, prec, dep):
        if not self.modules.has_key(prec):
            self.modules[prec] = {}
        if dep != None:
            self.modules[prec][dep] = True

class DepsCheker(object):

    def __init__ (self):
        self.modules = {}         # all mentioned modules, whether present or not.
        self.modules_present = {} # modules actually present in the source tree.
        self.modules_used = {}    # modules displayed in the graph.
        self.selected = []        # selected modules from the command line args.

        self.modules_missing = None

    def __normalize_name (self, name):
        # Replace prohibited characters with someone sane.
        name = name.replace('-', '_')
        return name
    
    def __insert_depend (self, mod, dep):

        # precedent to dependent
        if not self.modules.has_key(mod):
            self.modules[mod] = Module(mod)
        obj = self.modules[mod]
        obj.deps[dep] = True

        # dependent to precedent
        if not self.modules.has_key(dep):
            self.modules[dep] = Module(dep)
        obj = self.modules[dep]
        obj.precs[mod] = True

    def __parse_build_lst (self, build_lst):
    
        # Read only the first line
        file = open(build_lst, 'r')
        while True:
            line = file.readline().strip()
            if line[0] != '#':
                break
        file.close()
    
        words = line.split()
        n = len(words)
    
        # Check line format to make sure it's formatted as expected.
        if n < 4:
            raise ParseError()
        if words[2] != ':' and words[2] != '::':
            raise ParseError()
        if words[-1] != 'NULL':
            raise ParseError()
    
        mod_name = self.__normalize_name(words[1])
        depends = words[3:]
        for dep in depends:
            if dep == 'NULL':
                break
    
            names = dep.split(':')
            if len(names) > 2:
                raise ParseError()
            elif len(names) == 2:
                dep = names[1]
    
            dep = self.__normalize_name(dep)
            self.__insert_depend(mod_name, dep)

    def run (self, selected):
    
        # modules we want to print dependency on.
        self.selected = selected

        # Find all build.lst files.
        for mod in os.listdir(os.getcwd()):
            if not os.path.isdir(mod):
                # not a directory
                continue
            
            build_lst = mod + '/prj/build.lst'
            if not os.path.isfile(build_lst):
                # no build.lst found
                continue

            self.modules_present[self.__normalize_name(mod)] = True
            self.__parse_build_lst(build_lst)
            
    def __build_depset_all (self):
        self.dep_set = DependSet() # reset
        if len(self.selected) == 0:
            mods = self.modules.keys()
            for mod in mods:
                deps = self.modules[mod].deps.keys()
                for dep in deps:
                    self.dep_set.insert_depend(mod, dep)
        else:
            # determine involved modules.
            self.__processed_mods = {}
            for selected in self.selected:
                if not self.modules.has_key(selected):
                    raise ParseError()

                if len(self.modules[selected].deps) > 0:
                    self.__trace_deps(self.modules[selected])

    def __build_depset_single (self, mods):
        self.dep_set = DependSet() # reset
        for mod in mods:

            if not self.modules.has_key(mod):
                continue

            obj = self.modules[mod]
            if len(obj.precs) == 0 and len(obj.deps) == 0:
                # No dependencies.  Just print the module.
                self.dep_set.insert_depend(mod, None)
                continue

            for prec in obj.precs.keys():
                self.dep_set.insert_depend(prec, obj.name)
            for dep in obj.deps.keys():
                self.dep_set.insert_depend(obj.name, dep)

    def print_dot_all (self):
        self.__build_depset_all()
        s = "digraph modules {\n"
        s += self.__print_dot_depset()
        s += self.__print_dot_selected()
        s += self.__print_dot_missing_modules()
        s += "}\n"
        return s

    def print_dot_single (self, mods):
        self.__build_depset_single(mods)
        s = "digraph modules {\n"
        s += self.__print_dot_depset()
        s += self.__print_dot_selected()
        s += self.__print_dot_missing_modules()
        s += "}\n"
        return s

    def print_flat_all (self):
        self.__build_depset_all()
        return self.__print_flat_depset()

    def print_flat_single (self, mods):
        self.__build_depset_single(mods)
        return self.__print_flat_depset()

    def __calc_missing_modules (self):
        if self.modules_missing != None:
            # already calculated.
            return

        present = self.modules_present.keys()
        self.modules_missing = {}
        for mod in self.modules.keys():
            if not self.modules_present.has_key(mod):
                self.modules_missing[mod] = True

    def print_missing_modules (self):
        self.__calc_missing_modules()

        if len(self.modules_missing) == 0:
            return

        sys.stderr.write(err_missing_modules + "\n")
        keys = self.modules_missing.keys()
        keys.sort()
        for mod in keys:
            sys.stderr.write("    " + mod + "\n")

    def __trace_deps (self, obj):
        if self.__processed_mods.has_key(obj.name):
            return

        self.__processed_mods[obj.name] = True

        for dep_name in obj.deps.keys():
            if not self.modules.has_key(dep_name):
                raise ParseError()
            self.dep_set.insert_depend(obj.name, dep_name)
            self.__trace_deps(self.modules[dep_name])

    def __print_flat_depset (self):
        s = ''
        mods = self.dep_set.modules.keys()
        mods.sort()
        for mod in mods:
            deps = self.dep_set.modules[mod].keys()
            if len(deps) == 0:
                # this module has no dependency.
                s += "%s\n"%mod
            else:
                deps.sort()
                for dep in deps:
                    s += "%s:%s\n"%(mod, dep)
        return s

    def __print_dot_depset (self):
        s = ''
        mods = self.dep_set.modules.keys()
        for mod in mods:
            deps = self.dep_set.modules[mod].keys()
            if len(deps) == 0:
                # this module has no dependency.
                s += self.__print_dot_dep_line(mod, None)
            else:
                for dep in deps:
                    s += self.__print_dot_dep_line(mod, dep)
        return s

    def __print_dot_selected (self):
        s = ''
        for mod in self.selected:
            if not self.modules_used.has_key(mod):
                continue
            s += "    %s [color=lightblue,style=filled];\n"%mod
        return s


    def __print_dot_missing_modules (self):
        self.__calc_missing_modules()
        s = ''
        for mod in self.modules_missing.keys():
            if not self.modules_used.has_key(mod):
                continue
            s += "    %s [color=red,style=filled];\n"%mod

        return s


    def __print_dot_dep_line (self, prec, dep):
        if prec == None:
            raise ParseError()

        self.modules_used[prec] = True
        if dep == None:
            # this module has no dependency.  I still need to mention the module name.
            return "    %s;\n"%prec
        self.modules_used[dep] = True
        return "    %s -> %s;\n"%(prec, dep)

def exec_exists (cmd):
    retcode = subprocess.call("which %s >/dev/null 2>/dev/null"%cmd, shell=True)
    return retcode == 0

def error (msg):
    sys.stderr.write(msg + "\n")
    sys.exit(1)

def launch_viewer (code):
    tmpfile = '/tmp/check-deps.tmp'
    tmpimage = '/tmp/check-deps-image.png'
    file = open(tmpfile, 'w')
    file.write(code)
    file.close()
    retcode = subprocess.call("dot -Tpng %s -o %s"%(tmpfile, tmpimage), shell=True)
    if retcode != 0:
        raise ViewerError()

    retcode = subprocess.call("eog %s"%tmpimage, shell=True)
    if retcode != 0:
        raise ViewerError()


if __name__ == '__main__':

    # Process commnad line arguments.
    parser = optparse.OptionParser()
    parser.usage += " " + arg_desc + "\n" + desc
    parser.add_option("-m", "--outout-mode", dest="output_mode", default="dot", metavar="MODE",
        help="Specify output format mode.  Supported modes are 'dot' and 'flat'.")
    parser.add_option("-s", "--single", action="store_true", dest="single", default=False,
        help="Print only immediate dependencies of specified modules.")
    parser.add_option("-g", "--gui", action="store_true", dest="gui", default=False,
        help="Display dependency graph in image viewer.")
    options, args = parser.parse_args()

    if options.gui:
        # Check to make sure 'dot' and 'eog' are present.
        if not exec_exists('dot'):
            error("'dot' not found.  Make sure you have 'dot' in your path.")
        if not exec_exists('eog'):
            error("'eog' not found.  Make sure you have 'eog' in your path.")

        # GUI mode requires dot-compatible output.
        options.output_mode = 'dot'

    if options.output_mode != 'dot' and options.output_mode != 'flat':
        error("Unrecognized output mode: %s"%options.output_mode)

    checker = DepsCheker()
    s = ''
    if options.single:
        if len(args) == 0:
            # single mode requires module names.
            raise SingleModeError()
        checker.run(args)
        if options.output_mode == 'dot':
            s = checker.print_dot_single(args)
        else:
            s = checker.print_flat_single(args)

    else:
        checker.run(args)
        if options.output_mode == 'dot':
            s = checker.print_dot_all()
        else:
            s = checker.print_flat_all()

    checker.print_missing_modules()

    if options.gui:
        launch_viewer(s)
    else:
        print (s)

