#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import os
import signal
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

        self.ui_test.create_doc_in_start_center("calc")

        self.ui_test.load_file(fileName)
        document = self.ui_test.get_component()

        # Ignore read-only files
        if not hasattr(document, 'isReadonly') or document.isReadonly():
            handle_skip()

        try:
            xDoc = self.xUITest.getTopFocusWindow()
            xEdit = xDoc.getChild("grid_window")
        except:
            #In case the mimetype is wrong and the file is open with another component
            handle_skip()

        return xEdit

    def test_remove_all_and_undo(self):
        xEdit = self.load_file()
        if xEdit:
            self.xUITest.executeCommand(".uno:SelectAll")
            xEdit.executeAction("TYPE", mkPropertyValues({"KEYCODE":"DELETE"}))

            self.xUITest.executeCommand(".uno:Undo")

        self.ui_test.close_doc()

    def test_insert_column_and_undo(self):
        xEdit = self.load_file()
        if xEdit:
            self.xUITest.executeCommand(".uno:InsertColumnsBefore")
            self.xUITest.executeCommand(".uno:Undo")

        self.ui_test.close_doc()

    def test_insert_row_and_undo(self):
        xEdit = self.load_file()
        if xEdit:
            self.xUITest.executeCommand(".uno:InsertRowsBefore")
            self.xUITest.executeCommand(".uno:Undo")

        self.ui_test.close_doc()

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

# vim: set shiftwidth=4 softtabstop=4 expandtab:
