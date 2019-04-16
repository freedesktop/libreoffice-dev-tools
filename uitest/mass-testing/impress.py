#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import os
from uitest.framework import UITestCase
from libreoffice.uno.propertyvalue import mkPropertyValues
import time

def handle_skip():
    #Kill the process so we don't have to open the same file for each test
    print("skipped")
    os.killpg(os.getpid(), signal.SIGINT)

class massTesting(UITestCase):

    def load_file(self):
        #TODO: Ignore password protected files

        fileName = os.environ["TESTFILENAME"]

        self.ui_test.create_doc_in_start_center("impress")

        self.ui_test.load_file(fileName)
        document = self.ui_test.get_component()

        # Ignore read-only files
        if not hasattr(document, 'isReadonly') or document.isReadonly():
            handle_skip()

        # Go to the normal view
        self.xUITest.executeCommand(".uno:NormalMultiPaneGUI")

        try:
            xDoc = self.xUITest.getTopFocusWindow()
            xEdit = xDoc.getChild("impress_win")
        except:
            #In case the mimetype is wrong and the file is open with another component
            handle_skip()

        return xEdit

    def test_copy_all_paste_undo(self):
        xEdit = self.load_file()
        if xEdit:
            self.xUITest.executeCommand(".uno:SelectAll")

            self.xUITest.executeCommand(".uno:Copy")

            for i in range(5):
                self.xUITest.executeCommand(".uno:Paste")

            for i in range(5):
                self.xUITest.executeCommand(".uno:Undo")
        self.ui_test.close_doc()

    def test_traverse_all_slides_and_delete_and_undo(self):
        xEdit = self.load_file()
        if xEdit:
            document = self.ui_test.get_component()
            slideCount = document.DrawPages.getCount()

            for i in range(slideCount):
                xEdit.executeAction("TYPE", mkPropertyValues({"KEYCODE":"PAGEDOWN"}))

                self.xUITest.executeCommand(".uno:SelectAll")

                xEdit.executeAction("TYPE", mkPropertyValues({"KEYCODE":"DELETE"}))

                self.xUITest.executeCommand(".uno:Undo")
        self.ui_test.close_doc()

    def test_duplicate_all_slides_and_undo(self):
        xEdit = self.load_file()
        if xEdit:
            # Go to the slide sorter view
            self.xUITest.executeCommand(".uno:DiaMode")

            xDoc = self.xUITest.getTopFocusWindow()
            xEdit = xDoc.getChild("slidesorter")

            self.xUITest.executeCommand(".uno:SelectAll")

            self.xUITest.executeCommand(".uno:DuplicatePage")

            self.xUITest.executeCommand(".uno:Undo")
        self.ui_test.close_doc()

    def test_remove_all_slides_and_undo(self):
        xEdit = self.load_file()
        if xEdit:
            # Go to the slide sorter view
            self.xUITest.executeCommand(".uno:DiaMode")

            xDoc = self.xUITest.getTopFocusWindow()
            xEdit = xDoc.getChild("slidesorter")

            self.xUITest.executeCommand(".uno:SelectAll")

            xEdit.executeAction("TYPE", mkPropertyValues({"KEYCODE":"DELETE"}))

            self.xUITest.executeCommand(".uno:Undo")
        self.ui_test.close_doc()

# vim: set shiftwidth=4 softtabstop=4 expandtab:
