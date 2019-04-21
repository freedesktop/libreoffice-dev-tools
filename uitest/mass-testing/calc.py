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

    def test_print_preview(self):
        xEdit = self.load_file()
        if xEdit:
            self.xUITest.executeCommand(".uno:PrintPreview")  #open print preview
            self.xUITest.executeCommand(".uno:ClosePreview")  # close print preview

            self.xUITest.getTopFocusWindow()

        self.ui_test.close_doc()

    def test_hide_column_and_undo(self):
        xEdit = self.load_file()
        if xEdit:
            self.xUITest.executeCommand(".uno:HideColumn")
            self.xUITest.executeCommand(".uno:Undo")

        self.ui_test.close_doc()

    def test_hide_row_and_undo(self):
        xEdit = self.load_file()
        if xEdit:
            self.xUITest.executeCommand(".uno:HideRow")
            self.xUITest.executeCommand(".uno:Undo")

        self.ui_test.close_doc()

    def test_copy_sheet_undo_delete_sheet(self):
        xEdit = self.load_file()
        if xEdit:
            document = self.ui_test.get_component()
            nrSheets = document.Sheets.getCount()  #number of sheets in the document
            if nrSheets == 1:
                #copy sheet and undo
                self.ui_test.execute_dialog_through_command(".uno:Move")
                xDialog = self.xUITest.getTopFocusWindow()
                xOKBtn = xDialog.getChild("ok")
                self.ui_test.close_dialog_through_button(xOKBtn)
                self.assertEqual(document.Sheets.getCount(), 2)
                self.xUITest.executeCommand(".uno:Undo")
            else:
                #copy sheet and undo and delete
                #go to first sheet
                for i in range(nrSheets - 1):
                    self.xUITest.executeCommand(".uno:JumpToPrevTable")
                #copy sheet; delete sheet
                for i in range(nrSheets - 1):
                    self.ui_test.execute_dialog_through_command(".uno:Move")
                    xDialog = self.xUITest.getTopFocusWindow()
                    xCopy = xDialog.getChild("copy")
                    xCopy.executeAction("CLICK", tuple())
                    xOKBtn = xDialog.getChild("ok")
                    self.ui_test.close_dialog_through_button(xOKBtn)

                    self.xUITest.executeCommand(".uno:Undo")

                    self.ui_test.execute_dialog_through_command(".uno:Remove")  #delete sheet
                    xDialog = self.xUITest.getTopFocusWindow()
                    xOKButton = xDialog.getChild("yes")
                    xOKButton.executeAction("CLICK", tuple())

            self.assertEqual(document.Sheets.getCount(), 1)

        self.ui_test.close_doc()

    def test_change_text_formatting_and_undo(self):
        xEdit = self.load_file()
        if xEdit:
            self.xUITest.executeCommand(".uno:SelectAll")
            self.xUITest.executeCommand(".uno:Bold")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:Italic")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:Underline")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:UnderlineDouble")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:Strikeout")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:Overline")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:SuperScript")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:SubScript")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:Shadowed")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:OutlineFont")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:Grow")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:Shrink")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:ChangeCaseToUpper")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:ChangeCaseToLower")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:ChangeCaseRotateCase")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:ChangeCaseToSentenceCase")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:ChangeCaseToTitleCase")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:ChangeCaseToToggleCase")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:SmallCaps")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:StyleApply?Style:string=Heading%202&FamilyName:string=ParagraphStyles")
            self.xUITest.executeCommand(".uno:Undo")

        self.ui_test.close_doc()
# vim: set shiftwidth=4 softtabstop=4 expandtab:
