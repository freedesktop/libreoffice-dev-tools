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

class massTesting(UITestCase):

    def load_file(self):
        #TODO: Ignore password protected files

        fileName = os.environ["TESTFILENAME"]

        self.ui_test.create_doc_in_start_center("writer")

        self.ui_test.load_file(fileName)
        document = self.ui_test.get_component()

        # Ignore read-only files
        if not hasattr(document, 'isReadonly') or document.isReadonly():
            print("mass-uitesting:skipped", flush=True)
            return

        try:
            xDoc = self.xUITest.getTopFocusWindow()
            xEdit = xDoc.getChild("writer_edit")
        except:
            #In case the mimetype is wrong and the file is open with another component
            print("mass-uitesting:skipped", flush=True)
            return

        print("mass-uitesting:loaded", flush=True)

        return xEdit

    def test_remove_all_and_undo(self):
        xEdit = self.load_file()
        if xEdit:
            self.xUITest.executeCommand(".uno:SelectAll")
            xEdit.executeAction("TYPE", mkPropertyValues({"KEYCODE":"DELETE"}))

            self.xUITest.executeCommand(".uno:Undo")

        self.ui_test.close_doc()

    def test_insert_returns_and_undo(self):
        xEdit = self.load_file()
        if xEdit:
            for i in range(60):
                xEdit.executeAction("TYPE", mkPropertyValues({"KEYCODE":"RETURN"}))

            for i in range(60):
                self.xUITest.executeCommand(".uno:Undo")

        self.ui_test.close_doc()

    def test_insert_pageBreaks_and_undo(self):
        xEdit = self.load_file()
        if xEdit:
            for i in range(5):
                self.xUITest.executeCommand(".uno:InsertPagebreak")

            for i in range(5):
                self.xUITest.executeCommand(".uno:Undo")

        self.ui_test.close_doc()

    def test_insert_remove_header(self):
        xEdit = self.load_file()
        if xEdit:
            document = self.ui_test.get_component()

            #Insert Default header if it doesn't exists
            if not document.StyleFamilies.PageStyles.Standard.HeaderIsOn:
                self.xUITest.executeCommand(
                        ".uno:InsertPageHeader?PageStyle:string=Default%20Style&On:bool=true")

            self.assertEqual(document.StyleFamilies.PageStyles.Standard.HeaderIsOn, True)

            # Delete the header
            self.ui_test.execute_dialog_through_command(
                    ".uno:InsertPageHeader?PageStyle:string=Default%20Style&On:bool=false")

            xDialog = self.xUITest.getTopFocusWindow()  #question dialog
            xOption = xDialog.getChild("yes")
            xOption.executeAction("CLICK", tuple())

            self.assertEqual(document.StyleFamilies.PageStyles.Standard.HeaderIsOn, False)

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

    def test_insert_remove_footer(self):
        xEdit = self.load_file()
        if xEdit:
            document = self.ui_test.get_component()

            #Insert Default footer if it doesn't exists
            if not document.StyleFamilies.PageStyles.Standard.FooterIsOn:
                self.xUITest.executeCommand(
                        ".uno:InsertPageFooter?PageStyle:string=Default%20Style&On:bool=true")

            self.assertEqual(document.StyleFamilies.PageStyles.Standard.FooterIsOn, True)

            # Delete the header
            self.ui_test.execute_dialog_through_command(
                    ".uno:InsertPageFooter?PageStyle:string=Default%20Style&On:bool=false")

            xDialog = self.xUITest.getTopFocusWindow()  #question dialog
            xOption = xDialog.getChild("yes")
            xOption.executeAction("CLICK", tuple())

            self.assertEqual(document.StyleFamilies.PageStyles.Standard.FooterIsOn, False)

        self.ui_test.close_doc()

    def test_traverse_all_pages(self):
        xEdit = self.load_file()
        if xEdit:
            document = self.ui_test.get_component()
            pageCount = document.CurrentController.PageCount

            for i in range(pageCount):
                xEdit.executeAction("TYPE", mkPropertyValues({"KEYCODE":"PAGEDOWN"}))

            for i in range(pageCount):
                xEdit.executeAction("TYPE", mkPropertyValues({"KEYCODE":"PAGEUP"}))

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

        self.ui_test.close_doc()

    def test_default_bullet_list_and_undo(self):
        xEdit = self.load_file()
        if xEdit:
            self.xUITest.executeCommand(".uno:SelectAll")
            self.xUITest.executeCommand(".uno:DefaultBullet")
            self.xUITest.executeCommand(".uno:Undo")

        self.ui_test.close_doc()

    def test_change_alignment_and_undo(self):
        xEdit = self.load_file()
        if xEdit:
            self.xUITest.executeCommand(".uno:SelectAll")
            self.xUITest.executeCommand(".uno:CommonAlignLeft")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:CommonAlignHorizontalCenter")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:CommonAlignRight")
            self.xUITest.executeCommand(".uno:Undo")
            self.xUITest.executeCommand(".uno:CommonAlignJustified")
            self.xUITest.executeCommand(".uno:Undo")

        self.ui_test.close_doc()

# vim: set shiftwidth=4 softtabstop=4 expandtab:
