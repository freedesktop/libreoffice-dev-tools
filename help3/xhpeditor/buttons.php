<div class="navbar">
    <div class="dropdown">
    <button class="dropbtn">File</button>
    <div class="dropdown-content">
    <input type="file" id="file-input" accept=".xhp" value="Open"/>
    <a href="#" onclick="download(editor.getValue(),getFileNameFromXML(),'text/xml')">Save</a>
    </div>
  </div>
    <div class="dropdown">
    <button class="dropbtn">Edit</button>
    <div class="dropdown-content">
    <a href="#" onclick="editor.undo()">Undo</a>
    <a href="#" onclick="editor.redo()">Redo</a>
    </div>
  </div>
    <div class="dropdown">
    <button class="dropbtn">Document</button>
    <div class="dropdown-content">
    <a href="#" onclick="startNewXHPDoc()">Start new XHP document</a>
    <a href="#" onclick="docHeading()">DocHeading</a>
    <a href="#" onclick="snippet7()">&lt;ahelp&gt;</a>
    </div>
  </div>
    <div class="dropdown">
    <button class="dropbtn">Bookmarks</button>
    <div class="dropdown-content">
    <a href="#" onclick="bookmarkValue()">bmk-value</a>
    <a href="#" onclick="bookmarkBranch()">bmk-hid</a>
    <a href="#" onclick="bookmarkIndex()">bmk-index</a>
    <a href="#" onclick="bookmarkNoWidget()">bmk-nowidget</a>
    </div>
  </div>
    <div class="dropdown">
    <button class="dropbtn">Sections</button>
    <div class="dropdown-content">
    <a href="#" onclick="section_div()">Section</a>
    <a href="#" onclick="related_topics()">Related Topics</a>
    <a href="#" onclick="howtoget()">How to get</a>
    <a href="#" onclick="bascode_div()">bascode div</a>
    <a href="#" onclick="pycode_div()">pycode div</a>
    </div>
  </div>
  <div class="dropdown">
    <button class="dropbtn">Tables</button>
    <div class="dropdown-content">
    <a href="#" onclick="table2R3C()">Table Full</a>
    <a href="#" onclick="tableRow()">Table Row</a>
    <a href="#" onclick="tableCell()">Table Cell</a>
    <a href="#" onclick="iconTable()">Icon Table</a>
    </div>
  </div>
  <div class="dropdown">
    <button class="dropbtn">Paragraph</button>
    <div class="dropdown-content">
    <a href="#" onclick="paragraph('paragraph')">&lt;paragraph&gt;</a>
    <a href="#" onclick="note()">&lt;note&gt;</a>
    <a href="#" onclick="warning()">&lt;warning&gt;</a>
    <a href="#" onclick="tip()">&lt;tip&gt;</a>
    <a href="#" onclick="bascode_par()">bascode-par</a>
    <a href="#" onclick="pycode_par()">pycode-par</a>
    <a href="#" onclick="image_par()">image-par</a>
    </div>
  </div>
  <div class="dropdown">
    <button class="dropbtn">Characters</button>
    <div class="dropdown-content">
    <a href="#" onclick="emph()">&lt;emph&gt;</a>
    <a href="#" onclick="c_menuitem()">&lt;menuitem&gt;</a>
    <a href="#" onclick="_input()">&lt;input&gt;</a>
    <a href="#" onclick="_literal()">&lt;literal&gt;</a>
    <a href="#" onclick="_keystroke()">&lt;keycode&gt;</a>
    <a href="#" onclick="_widget()">&lt;widget&gt;</a>
    </div>
  </div>
  <div class="dropdown">
    <button class="dropbtn">Headings</button>
    <div class="dropdown-content">
    <a href="#" onclick="heading('1')">&lt;H1&gt;</a>
    <a href="#" onclick="heading('2')">&lt;H2&gt;</a>
    <a href="#" onclick="heading('3')">&lt;H3&gt;</a>
    <a href="#" onclick="heading('4')">&lt;H4&gt;</a>
    </div>
  </div>
  <div class="dropdown">
    <button class="dropbtn">Switches</button>
    <div class="dropdown-content">
        <a href="#" onclick="switchXHP('appl')">Switch appl</a>
        <a href="#" onclick="switchXHP('sys')">Switch sys</a>
        <a href="#" onclick="switchInline('appl')">Switchinline appl</a>
        <a href="#" onclick="switchInline('sys')">Switchinline sys</a>
        <a href="#" onclick="MenuPrefMAC()">Menu MAC</a>
        <a href="#" onclick="KeyMAC()">Key MAC</a>
    </div>
  </div>
  <div class="dropdown">
    <button class="dropbtn">Lists</button>
    <div class="dropdown-content">
      <a href="#" onclick="tList('unordered')">&lt;ul&gt;</a>
      <a href="#" onclick="tList('ordered')">&lt;ol&gt;</a>
      <a href="#" onclick="listItem()">&lt;listitem&gt;</a>
    </div>
  </div>
  <div class="dropdown">
    <button class="dropbtn">Links</button>
    <div class="dropdown-content">
      <a href="#" onclick="tVariable()">&lt;variable&gt;</a>
      <a href="#" onclick="tEmbed()">&lt;embed&gt;</a>
      <a href="#" onclick="tEmbedvar()">&lt;embedvar&gt;</a>
      <a href="#" onclick="tLink()">&lt;link&gt;</a>
    </div>
  </div>
  <div class="dropdown">
    <button class="dropbtn">Tools</button>
    <div class="dropdown-content">
        <input type="submit" form="CMtextarea" name="render_page" value="Render page"/>
        <input type="submit" form="CMtextarea" name="get_patch" value="Generate patch"/>
        <input type="submit" form="CMtextarea" name="check_xhp" value="Check XHP"/>
        <input type="submit" form="CMtextarea" name="open_master" value="Open Master"/>
    </div>
  </div>
  <div class="dropdown">
    <button class="dropbtn">Help</button>
    <div class="dropdown-content">
        <a href="https://wiki.documentfoundation.org/Documentation/Understanding,_Authoring_and_Editing_Openoffice.org_Help/3" target="_blank">XHP Reference</a>
        <a href="doc/manual.html#commands" target="_blank">Editor shortcuts</a>
        <a href="#" target="_blank">Editor</a>
    </div>
  </div>
</div>
