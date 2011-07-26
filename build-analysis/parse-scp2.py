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

arg_desc = ""

desc = """
Run this script at the root of OOo source tree."""

# taken from setup_native/source/packinfo/packinfo_office.txt
top_modules = [
    'gid_Module_Optional_Gnome',
    'gid_Module_Optional_Kde',
    'gid_Module_Root',
    'gid_Module_Prg_Wrt_Bin',
    'gid_Module_Prg_Calc_Bin',
    'gid_Module_Prg_Draw_Bin',
    'gid_Module_Prg_Impress_Bin',
    'gid_Module_Prg_Base_Bin',
    'gid_Module_Prg_Math_Bin',
    'gid_Module_Optional_Binfilter',
    'gid_Module_Optional_Grfflt',
    'gid_Module_Oooimprovement',
    'gid_Module_Optional_Testtool',
    'gid_Module_Optional_Oo_English',
    'gid_Module_Optional_Xsltfiltersamples',
    'gid_Module_Optional_Javafilter',
    'gid_Module_Optional_Activexcontrol',
    'gid_Module_Optional_Onlineupdate',
    'gid_Module_Optional_Pyuno',
    'gid_Module_Optional_Pymailmerge',
    'gid_Module_Optional_Headless',
    'gid_Module_Root_Files_Images',
    'gid_Module_Root_Fonts_OOo_Hidden',
    'gid_Module_Oo_Linguistic',
    'gid_Module_Root_Files_2',
    'gid_Module_Root_Files_3',
    'gid_Module_Root_Files_4',
    'gid_Module_Root_Files_5',
    'gid_Module_Root_Files_6',
    'gid_Module_Root_Files_7',
    'gid_Module_Root_Extension_Oooimprovement',
    'gid_Module_Root_Extension_Dictionary_Af',
    'gid_Module_Root_Extension_Dictionary_Ca',
    'gid_Module_Root_Extension_Dictionary_Cs',
    'gid_Module_Root_Extension_Dictionary_Da',
    'gid_Module_Root_Extension_Dictionary_De_AT',
    'gid_Module_Root_Extension_Dictionary_De_CH',
    'gid_Module_Root_Extension_Dictionary_De_DE',
    'gid_Module_Root_Extension_Dictionary_En',
    'gid_Module_Root_Extension_Dictionary_Es',
    'gid_Module_Root_Extension_Dictionary_Et',
    'gid_Module_Root_Extension_Dictionary_Fr',
    'gid_Module_Root_Extension_Dictionary_Gl',
    'gid_Module_Root_Extension_Dictionary_He',
    'gid_Module_Root_Extension_Dictionary_Hu',
    'gid_Module_Root_Extension_Dictionary_It',
    'gid_Module_Root_Extension_Dictionary_Ku_Tr',
    'gid_Module_Root_Extension_Dictionary_Lt',
    'gid_Module_Root_Extension_Dictionary_Ne',
    'gid_Module_Root_Extension_Dictionary_Nl',
    'gid_Module_Root_Extension_Dictionary_No',
    'gid_Module_Root_Extension_Dictionary_Pl',
    'gid_Module_Root_Extension_Dictionary_Pt',
    'gid_Module_Root_Extension_Dictionary_Ro',
    'gid_Module_Root_Extension_Dictionary_Ru',
    'gid_Module_Root_Extension_Dictionary_Sk',
    'gid_Module_Root_Extension_Dictionary_Sl',
    'gid_Module_Root_Extension_Dictionary_Sr',
    'gid_Module_Root_Extension_Dictionary_Sv',
    'gid_Module_Root_Extension_Dictionary_Sw',
    'gid_Module_Root_Extension_Dictionary_Th',
    'gid_Module_Root_Extension_Dictionary_Vi',
    'gid_Module_Root_Extension_Dictionary_Zu',
    'gid_Module_Optional_OGLTrans'
]

class ErrorBase(Exception):
    
    def __init__ (self, name, msg, sev):
        self.value = "%s: %s"%(name, msg)
        self.sev = sev                    # error severity, 0 = least severe

    def __str__ (self):
        return repr(self.value)

class ParseError(ErrorBase):
    
    def __init__ (self, msg, sev = 0):
        ErrorBase.__init__(self, "ParseError", msg, sev)

class DirError(ErrorBase):
    def __init__ (self, msg):
        ErrorBase.__init__(self, "DirError", msg, 0)

class ModuleError(ErrorBase):
    def __init__ (self, msg):
        ErrorBase.__init__(self, "ModuleError", msg, 0)

class LinkedNode(object):
    def __init__ (self, name):
        self.name = name
        self.parent = None
        self.children = []

# ----------------------------------------------------------------------------

def error (msg):
    sys.stderr.write(msg + "\n")

def get_attr_or_fail (name, key, attrs):
    if not attrs.has_key(key):
        raise ParseError("%s doesn't have %s attribute, but expected."%(name, key), 1)
    return attrs[key]

# ----------------------------------------------------------------------------

class Scp2Tokenizer(object):
    """Tokenizer for scp files."""

    def __init__ (self, content):
        self.content = content
        self.tokens = []

    def flush_buffer (self):
        if len(self.buf) > 0:
            self.tokens.append(self.buf)
            self.buf = ''

    def run (self):
        self.tokens = []
        i = 0
        n = len(self.content)
        self.buf = ''
        while i < n:
            c = self.content[i]
            if c in '\t\n':
                c = ' '

            if c in ' ;':
                self.flush_buffer()
                if c == ';':
                    self.tokens.append(c)
            elif c == '"':
                # String literal.  Parse until reaching the closing quote.
                self.flush_buffer()
                i += 1
                c = self.content[i]
                while c != '"':
                    self.buf += c
                    i += 1
                    c = self.content[i]
                self.flush_buffer()
            else:
                self.buf += c
            i += 1

# ----------------------------------------------------------------------------

class Scp2Parser(object):
    """Parser for scp files."""

    class Type:
        File       = 0
        Directory  = 1
        FolderItem = 2

    NodeTypes = [
        'DataCarrier',         # ignored
        'Directory',           # ignored, referenced directly from File
        'File',                # done, linked from within Module
        'Folder',              # ignored
        'FolderItem',          # ignored for now.  windows specific?
        'Installation',        # ignored.  I don't know what this is for.
        'Module',              # done
        'Profile',             # ignored
        'ProfileItem',         # ignored
        'RegistryItem',        # done
        'ScpAction',           # ignored
        'Shortcut',            # linked to File?  Treat this as a child of File for now.
        'StarRegistry',        # ignored, probably for StarOffice only
        'Unixlink',            # done, linked from within Module
        'WindowsCustomAction'  # ignored
    ]

    def __init__ (self, content, filename):
        self.content = content
        self.filename = filename
        self.nodedata = {}

    def tokenize (self):
        tokenizer = Scp2Tokenizer(self.content)
        tokenizer.run()
        self.tokens = tokenizer.tokens

    def next (self):
        self.i += 1

    def token (self):
        return self.tokens[self.i]

    def parse (self):
        if len(self.tokens) == 0:
            # No tokens to parse.  Bail out.
            return
            
        self.i = 0
        self.n = len(self.tokens)
        while self.i < self.n:
            t = self.token()
            if t in Scp2Parser.NodeTypes:
                name, attrs, values = self.__parseEntity()
                attrs['__node_type__'] = t                 # type of node
                attrs['__node_location__'] = self.filename # file where the node is defined
                attrs['__node_values__'] = values          # list of values that are not attributes (i.e. not associated with names)
                if self.nodedata.has_key(name):
                    raise ParseError("node named %s already exists"%name, 1)
                self.nodedata[name] = attrs
            else:
                raise ParseError("Unknown node type: %s"%t)

            self.next()

    def append_nodes (self, nodedata, nodetree):

        for key in self.nodedata.keys():

            if nodedata.has_key(key):
                raise ParseError("node named %s already exists"%key, 1)

            # Transfer all the node attributes to the caller instance.
            nodedata[key] = self.nodedata[key]

            # Now, add linkage data to the parent tree instance.

            if not nodetree.has_key(key):
                # Create a new linked node instance.
                nodetree[key] = LinkedNode(key)

            attrs = self.nodedata[key]

            node_type = attrs['__node_type__']
            if node_type == 'Module':
                self.__link_module_node(key, attrs, nodetree)
            elif node_type == 'RegistryItem':
                # RegistryItem entries have ModuleID to link back to a module.
                self.__link_simple(key, attrs, nodetree, 'ModuleID')
            elif node_type == 'Shortcut':
                self.__link_simple(key, attrs, nodetree, 'FileID')
            elif node_type == 'Profile':
                self.__link_simple(key, attrs, nodetree, 'ModuleID')
            elif node_type == 'ProfileItem':
                self.__link_simple(key, attrs, nodetree, 'ProfileID')
                

    def __link_simple (self, name, attrs, nodetree, pid_attr):
        parentID = get_attr_or_fail(name, pid_attr, attrs)
        if not nodetree.has_key(parentID):
            nodetree[parentID] = LinkedNode(parentID)
        if not nodetree.has_key(name):
            nodetree[name] = LinkedNode(name)

        nodetree[parentID].children.append(nodetree[name])
        if nodetree[name].parent != None:
            raise ParseError("parent node instance already exists for '%s'"%name, 1)
        nodetree[name].parent = nodetree[parentID]


    def __link_files (self, name, files, nodetree):

        # file list strings are formatted like this '(file1,file2,file3,....)'
        if files[0] != '(' or files[-1] != ')':
            raise ParseError("file list string is not formatted correctly: %s"%files)
        files = files[1:-1]
        list = files.split(',')
        for file in list:
            if not nodetree.has_key(file):
                nodetree[file] = LinkedNode(file)
            nodetree[name].children.append(nodetree[file])


    def __link_module_node (self, name, attrs, nodetree):

        if attrs.has_key('ParentID'):
            parentID = attrs['ParentID']

            if not nodetree.has_key(parentID):
                nodetree[parentID] = LinkedNode(parentID)

            nodetree[parentID].children.append(nodetree[name])
            if nodetree[name].parent != None:
                raise ParseError("parent node instance already exists for '%s'"%name, 1)
            nodetree[name].parent = nodetree[parentID]

        if attrs.has_key('Files'):
            self.__link_files(name, attrs['Files'], nodetree)

        if attrs.has_key('Unixlinks'):
            self.__link_files(name, attrs['Unixlinks'], nodetree)


    def __parseEntity (self):
        self.next()
        name = self.token()
        if len(name) == 0:
            raise ParseError("empty name", 1)
        left = True
        attr_name = ''
        attr_value = ''
        attrs = {}
        values = []
        self.next()
        while self.token() != 'End':
            if self.token() == '=':
                if not left:
                    raise ParseError("multiple '='s in a single line")

                if len(attr_name) == 0:
                    raise ParseError("empty attribute name")

                left = False
            
            elif left:
                if self.token() == ';':
                    # Not a valid attribute.  Store it as a 'value'.
                    values.append(attr_name)
                    attr_name = ''
                else:
                    attr_name += self.token()
            else:
                # Parse all the way up to ';'
                attr_value = ''
                while self.token() != ';':
                    attr_value += self.token()
                    self.next()
                attrs[attr_name] = attr_value
                left = True
                attr_name = ''

            self.next()

        return name, attrs, values

# ----------------------------------------------------------------------------

class XMLFunc:

    @staticmethod
    def resolve_vars (s, vars):
        """Replace all ${...}s with their respective values."""

        ret = ''
        
        while True:
            start = s.find('${')
            if start == -1:
                ret += s
                break
    
            end = s.find('}', start+2)
            if end == -1:
                ret += s
                break
    
            key = s[start+2:end]
            if vars.has_key(key):
                ret += s[:start] + vars[key]
            s = s[end+1:]
    
        return ret

    @staticmethod
    def to_xml_name (name):
        """CamelCase to camel-case"""
        s = ''
        n = len(name)
        for i in xrange(0, n):
            c = name[i]
            if 'A' <= c and c <= 'Z':
                if i > 0:
                    s += '-'
                s += c.lower()
            else:
                s += c
        return s

    @staticmethod
    def add_attr (attrs, key):
        s = ''
        if attrs.has_key(key):
            s = " %s=\"%s\""%(XMLFunc.to_xml_name(key), attrs[key])
        return s

    @staticmethod
    def add_attr_localized (attrs, key, locale):
        if attrs.has_key(key):
            # Try non-localized name first.
            return " %s=\"%s\""%(XMLFunc.to_xml_name(key), attrs[key])
        
        key_localized = key + "(%s)"%locale
        if attrs.has_key(key_localized):
            # Try non-localized name first.
            return " %s=\"%s\" locale=\"%s\""%(XMLFunc.to_xml_name(key), attrs[key_localized], locale)

        return ''

    @staticmethod
    def add_attr_vars (attrs, key, vars):
        if not attrs.has_key(key):
            return ''

        s = " %s=\"%s\""%(XMLFunc.to_xml_name(key), XMLFunc.resolve_vars(attrs[key], vars))
        return s


    @staticmethod
    def add_attr_array (attrs, key):

        if not attrs.has_key(key):
            return ''

        raw_str = attrs[key]
        if len(raw_str) == 0 or raw_str[0] != '(' or raw_str[-1] != ')':
            raise ParseError("%s attribute is not formatted properly: '%s'"%(key, raw_str), 1)

        if raw_str == '()':
            return ''

        val = raw_str[1:-1].lower().replace('_', '-')
        s = " %s=\"%s\""%(XMLFunc.to_xml_name(key), val)
        return s



class Scp2Processor(object):
    """Collect all .scp files in scp2 directory, and run preprocessor."""

    tmpin  = "/tmp/parse-scp2.py.cpp"
    tmpout = "/tmp/parse-scp2.py.out"

    SkipList = {
        'scp2/source/ooo/ure_standalone.scp': True,
        'scp2/source/sdkoo/sdkoo.scp': True,
        'scp2/source/ooo/starregistry_ooo.scp': True
    }

    def __init__ (self, cur_dir, mod_output_dir, vars):
        self.cur_dir = cur_dir
        self.mod_output_dir = mod_output_dir
        self.vars = vars
        self.scp_files = []
        self.nodedata = {}
        self.nodetree = {}
        self.locale = 'en-US'

        # Check file paths first.
        if not os.path.isfile("%s/scp2/inc/macros.inc"%self.cur_dir):
            raise ParseError("You don't appear to be at the root of OOo's source tree.")
        if not os.path.isdir("%s/scp2/%s/inc"%(self.cur_dir, self.mod_output_dir)):
            raise ParseError("You don't appear to be at the root of OOo's source tree.")

    def to_relative (self, fullpath):
        i = fullpath.find("/scp2/")
        if i < 0:
            return fullpath
        i += 1 # skip '/' before 'scp2'
        return fullpath[i:]

    def run (self):
        # Collect all .scp files under scp2.
        os.path.walk(self.cur_dir + "/scp2", Scp2Processor.visit, self)

        # Process each .scp file.
        for scp in self.scp_files:
            relpath = self.to_relative(scp)
            if Scp2Processor.SkipList.has_key(relpath):
                error("skipping %s"%scp)
                continue

            self.process_scp(scp)

    def process_scp (self, scp):
        ret = subprocess.call("cp %s %s"%(scp, Scp2Processor.tmpin), shell=True)
        if ret > 0:
            raise ParseError("failed to copy scp file to a temporary location.")

        subprocess.call("gcc -E -I./scp2/inc -I./scp2/%s/inc -DUNX %s 2>/dev/null | grep -v -E \"^\#\" > %s"%
            (self.mod_output_dir, Scp2Processor.tmpin, Scp2Processor.tmpout), shell=True)

        file = open(Scp2Processor.tmpout, 'r')
        content = file.read()
        file.close()
        parser = Scp2Parser(content, self.to_relative(scp))
        parser.tokenize()
        try:
            parser.parse()
            parser.append_nodes(self.nodedata, self.nodetree)
        except ParseError as e:
            # Skip mal-formed files, instead of exit with error.
            error (e.value)
            error ("Error parsing %s"%scp)
            if e.sev > 0:
                # This is a severe error.  Exit right away.
                sys.exit(1)

    def print_summary_flat (self):
        names = self.nodedata.keys()
        names.sort()
        for name in names:
            attrs = self.nodedata[name]
            node_type = attrs['__node_type__']
            print ('-'*70)
            print ("%s (%s)"%(name, node_type))
            print ("[node location: %s]"%attrs['__node_location__'])

            # Print values first.
            values = attrs['__node_values__']
            for value in values:
                print("  %s"%value)

            # Print all attributes.
            attr_names = attrs.keys()
            attr_names.sort()
            for attr_name in attr_names:
                if attr_name in ['__node_type__', '__node_location__', '__node_values__']:
                    # Skip special attributes.
                    continue
                print ("  %s = %s"%(attr_name, attrs[attr_name]))

    def print_summary_tree (self, root):

        if not self.nodetree.has_key(root):
            raise ModuleError("module %s not found."%root)

        node = self.nodetree[root]
        self.__print_summary_tree_node(node, 0)

    def __get_fullpath (self, fileID, locale):
        """Given a file identifier, construct the absolute path for that file."""

        nodedata = self.nodedata[fileID]
        filename = None
        localized = False
        key_localized = "Name(%s)"%locale
        if nodedata.has_key('Name'):
            filename = nodedata['Name']
        elif nodedata.has_key(key_localized):
            filename = nodedata[key_localized]
            localized = True
        else:
            raise DirError("%s doesn't have a name attribute."%fileID)

        if not nodedata.has_key('Dir'):
            raise DirError("file %s doesn't have Dir attribute."%fileID)

        parent_dir_name = nodedata['Dir']

        while parent_dir_name != None:

            if parent_dir_name == 'PREDEFINED_PROGDIR':
                # special directory name
                filename = parent_dir_name + '/' + filename
                break

            if not self.nodedata.has_key(parent_dir_name):
                # directory is referenced but not defined.  Skip it for now.
                raise DirError("directory '%s' is referenced but not defined."%parent_dir_name)
    
            nodedata = self.nodedata[parent_dir_name]
            if nodedata.has_key('DosName'):
                filename = nodedata['DosName'] + "/" + filename
            elif nodedata.has_key('DosName(en-US)'):
                filename = nodedata['DosName(en-US)'] + "/" + filename
            elif nodedata.has_key('HostName'):
                filename = nodedata['HostName'] + "/" + filename
            else:
                raise DirError("directory '%s' does not have either DosName or HostName attribute."%parent_dir_name)

            if nodedata.has_key('ParentID'):
                parent_dir_name = nodedata['ParentID']
            else:
                parent_dir_name = None

        return filename, localized

    def __print_summary_tree_node (self, node, level):

        indent = '    '*level

        if node == None:
            return

        if not self.nodedata.has_key(node.name):
            # This node is referenced but is not defined.  Skip it.
            return

        nodedata = self.nodedata[node.name]
        if not self.nodedata.has_key(node.name):
            raise ParseError("there is no associated node data for '%s'"%node.name)

        node_type = nodedata['__node_type__']

        name = ''
        localized = False
        if node_type in ['File', 'Unixlink', 'Shortcut', 'Profile']:
            try:
                name, localized = self.__get_fullpath(node.name, self.locale)
                name = XMLFunc.resolve_vars(name, self.vars)
            except DirError as e:
                error(e.value)
                return

        s = indent + "<%s id=\"%s\""%(XMLFunc.to_xml_name(node_type), node.name)

        if len(name) > 0:
            s += " name=\"%s\""%name

        if node_type == 'Module':
            s += XMLFunc.add_attr_array(nodedata, 'Styles')

        elif node_type == 'File':
            s += XMLFunc.add_attr(nodedata, 'UnixRights')
            s += XMLFunc.add_attr_array(nodedata, 'Styles')

        elif node_type == 'Profile':
            s += XMLFunc.add_attr_array(nodedata, 'Styles')

        elif node_type == 'ProfileItem':
            s += XMLFunc.add_attr(nodedata, 'Section')
            s += XMLFunc.add_attr(nodedata, 'Key')
            s += XMLFunc.add_attr_vars(nodedata, 'Value', self.vars)

        elif node_type == 'Unixlink':
            s += XMLFunc.add_attr_vars(nodedata, 'Target', self.vars)

        elif node_type == 'RegistryItem':
            val_path = get_attr_or_fail(node.name, 'ParentID', nodedata)
            val_path += '\\' + get_attr_or_fail(node.name, 'Subkey', nodedata)
            s += " path=\"%s\""%val_path
            s += XMLFunc.add_attr_localized(nodedata, 'Value', self.locale)

        if localized:
            s += " locale=\"%s\""%self.locale

        if len(node.children) > 0:
            s += ">"
            print (s)
    
            children = node.children
            children.sort()
            for child in children:
                self.__print_summary_tree_node(child, level+1)
    
            print (indent + "</%s>"%XMLFunc.to_xml_name(node_type))
        else:
            s += "/>"
            print (s)

    @staticmethod
    def visit (arg, dirname, names):
        instance = arg
        for name in names:
            filepath = dirname + "/" + name
            if os.path.splitext(filepath)[1] == '.scp':
                instance.scp_files.append(filepath)

# ----------------------------------------------------------------------------

class OOLstParser(object):
    """Parser for openoffice.lst file."""

    def __init__ (self):
        self.vars = {}

    def __repr__ (self):
        s = ''
        scope_names = self.vars.keys()
        scope_names.sort()
        for scope in scope_names:
            s += "%s\n"%scope
            attrs = self.vars[scope]
            keys = attrs.keys()
            keys.sort()
            for key in keys:
                s += "    %s"%key
                if attrs[key] != None:
                    s += " = %s"%attrs[key]
                else:
                    s += " ="
                s += "\n"

        return s

    def get_vars (self, scopes):
        vars = {}
        for scope in scopes:
            for key in self.vars[scope].keys():
                vars[key] = self.vars[scope][key]
        return vars

    def parse_openoffice_lst (self, lines):
    
        class _Error(ParseError):
            def __init__ (self, msg, sev=0):
                ParseError.__init__(self, "(openoffice.lst) " + msg, sev)
    
        self.ns = [] # namespace stack
        n = len(lines)
        self.last = None
        for i in xrange(0, n):
            words = lines[i].split()
            if len(words) == 0:
                # empty line
                continue
    
            if words[0] == '{':
                # new scope begins
                if len(words) != 1:
                    raise _Error("{ is followed by a token.", 1)
                if self.last == None:
                    raise _Error("fail to find a namespace token in the previous line.", 1)
                if len(self.last) != 1:
                    raise _Error("line contains multiple tokens when only one token is expected.", 1)
                t = self.last[0]
                self.ns.append(t)
    
            elif words[0] == '}':
                # current scope ends
                self.__check_last_line()

                if len(words) != 1:
                    raise _Error("} is followed by a token.", 1)
                self.ns.pop()
    
            else:
                # check the last line
                self.__check_last_line()
    
            self.last = words

    def __check_last_line (self):
        if self.last == None or len(self.last) == 0:
            return

        if self.last[0] in '{}':
            return

        key = self.last[0]
        val = None
        if len(self.last) > 1:
            sep = ' '
            val = sep.join(self.last[1:])
        self.__insert_attr(self.ns, key, val)


    def __insert_attr (self, ns, key, val):
        ns_str = '' # aggregate namespaces, separated by '::'s.
        for name in ns:
            if len(ns_str) == 0:
                ns_str = name
            else:
                ns_str += '::' + name

        if not self.vars.has_key(ns_str):
            # Create this namespace entry.
            self.vars[ns_str] = {}
        self.vars[ns_str][key] = val


# ----------------------------------------------------------------------------

if __name__ == '__main__':

    parser = optparse.OptionParser()
    parser.usage += " " + arg_desc + "\n" + desc
    parser.add_option("", "--module-output-dir", dest="mod_output_dir", default="unxlngi6.pro", metavar="DIR",
        help="Specify the name of module output directory.  The default value is 'unxlngi6.pro'.")
    parser.add_option("-m", "--output-mode", dest="mode", default='tree', metavar="MODE",
        help="Specify output mode.  Allowed values are 'tree' and 'flat.  The default mode is 'tree'.")
    parser.add_option("", "--openoffice-lst", dest="openoffice_lst", default="instsetoo_native/util/openoffice.lst", metavar="FILE",
        help="Specify the location of openoffice.lst file which contains variables used by the scp files.  The default value is 'instsetoo_native/util/openoffice.lst'.")

    options, args = parser.parse_args()

    if not options.mode in ['tree', 'flat']:
        error("unknown output mode '%s'"%options.mode)
        sys.exit(1)

    cur_dir = os.getcwd()
    oo_lst_path = cur_dir + '/' + options.openoffice_lst
    if not os.path.isfile(oo_lst_path):
        error("failed to find the openoffice.lst file at (%s)."%oo_lst_path)
        sys.exit(1)

    oolst_parser = OOLstParser()
    try:
        file = open(oo_lst_path, 'r')
        oolst_parser.parse_openoffice_lst(file.readlines())
        file.close()
    except ParseError as e:
        error(e.value)
        if e.sev > 0:
            sys.exit(1)

    # For now, just pull variables from these two namespaces.
    scopes_to_use = ['Globals::Settings::variables', 'OpenOffice::Settings::variables']
    vars = oolst_parser.get_vars(scopes_to_use)
    if vars.has_key('PRODUCTNAME'):
        # Special variable
        vars['UNIXPRODUCTNAME'] = vars['PRODUCTNAME'].lower()

    try:
        processor = Scp2Processor(cur_dir, options.mod_output_dir, vars)
        processor.run()
        if options.mode == 'tree':
            for module in top_modules:
                try:
                    processor.print_summary_tree(module)
                except ModuleError as e:
                    error(e.value)

        elif options.mode == 'flat':
            processor.print_summary_flat()
        else:
            raise ParseError("unknown output mode '%s'"%options.mode)

    except ParseError as e:
        error (e.value)
        sys.exit(1)
