<div class="buttonrow">
    <div class="snip_heading">File:</div>
    <div class="snip_buttons">Open: <input type="file" id="file-input" accept=".xhp"/></div>
    <button onclick="download(editor.getValue(),getFileNameFromXML(),'text/xml')" class="snip_buttons">Save local file</button>
</div>
<div class="buttonrow">
    <div class="snip_heading">Edit: </div>
    <button class="snip_buttons" onclick="editor.undo()">Undo</button>
    <button class="snip_buttons" onclick="editor.redo()">Redo</button>
</div>
<div class="buttonrow">
    <div class="snip_heading">Document: </div>
    <button onclick="startNewXHPDoc()" class="snip_buttons">Start new XHP document</button>
    <button onclick="docHeading()" class="snip_buttons">DocHeading</button>
    <button onclick="snippet7()" class="snip_buttons">&lt;ahelp&gt;</button>
</div>
<div class="buttonrow">
    <div class="snip_heading">Bookmarks: </div>
    <button onclick="bookmarkValue()" class="snip_buttons">bmk-value</button>
    <button onclick="bookmarkBranch()" class="snip_buttons">bmk-hid</button>
    <button onclick="bookmarkIndex()" class="snip_buttons">bmk-index</button>
    <button onclick="bookmarkNoWidget()" class="snip_buttons">bmk-nowidget</button>
</div>
<div class="buttonrow">
    <div class="snip_heading">Sections: </div>
    <button onclick="section_div()" class="snip_buttons">Section</button>
    <button onclick="related_topics()" class="snip_buttons">Related Topics</button>
    <button onclick="howtoget()" class="snip_buttons">How to get</button>
    <button onclick="bascode_div()" class="snip_buttons">bascode div</button>
    <button onclick="pycode_div()" class="snip_buttons">pycode div</button>
</div>
<div class="buttonrow">
    <div class="snip_heading">Tables: </div>
    <button onclick="table2R3C()" class="snip_buttons">Table Full</button>
    <button onclick="tableRow()" class="snip_buttons">Table Row</button>
    <button onclick="tableCell()" class="snip_buttons">Table Cell</button>
    <button onclick="iconTable()" class="snip_buttons">Icon Table</button>
</div>
<div class="buttonrow">
    <div class="snip_heading">Paragraph: </div>
    <button onclick="paragraph('paragraph')" class="snip_buttons">&lt;paragraph&gt;</button>
    <button onclick="note()" class="snip_buttons">&lt;note&gt;</button>
    <button onclick="warning()" class="snip_buttons">&lt;warning&gt;</button>
    <button onclick="tip()" class="snip_buttons">&lt;tip&gt;</button>
    <button onclick="bascode_par()" class="snip_buttons">bascode-par</button>
    <button onclick="pycode_par()" class="snip_buttons">pycode-par</button>
    <button onclick="image_par()" class="snip_buttons">image-par</button>
</div>
<div class="buttonrow">
    <div class="snip_heading">Characters: </div>
    <button onclick="emph()" class="snip_buttons">&lt;emph&gt;</button>
    <button onclick="c_menuitem()" class="snip_buttons">&lt;menuitem&gt;</button>
    <button onclick="_input()" class="snip_buttons">&lt;input&gt;</button>
    <button onclick="_literal()" class="snip_buttons">&lt;literal&gt;</button>
    <button onclick="_keystroke()" class="snip_buttons">&lt;keycode&gt;</button>
    <button onclick="_widget()" class="snip_buttons">&lt;widget&gt;</button>
</div>
<div class="buttonrow">
    <div class="snip_heading">Headings:</div>
    <button onclick="heading('1')" class="snip_buttons">&lt;H1&gt;</button>
    <button onclick="heading('2')" class="snip_buttons">&lt;H2&gt;</button>
    <button onclick="heading('3')" class="snip_buttons">&lt;H3&gt;</button>
    <button onclick="heading('4')" class="snip_buttons">&lt;H4&gt;</button>
</div>
<div class="buttonrow">
    <div class="snip_heading">Switches: </div>
    <button onclick="switchXHP('appl')" class="snip_buttons">Switch appl</button>
    <button onclick="switchXHP('sys')" class="snip_buttons">Switch sys</button>
    <button onclick="switchInline('appl')" class="snip_buttons">Switchinline appl</button>
    <button onclick="switchInline('sys')" class="snip_buttons">Switchinline sys</button>
    <button onclick="MenuPrefMAC()" class="snip_buttons">Menu MAC</button>
    <button onclick="KeyMAC()" class="snip_buttons">Key MAC</button>
</div>
<div class="buttonrow">
    <div class="snip_heading">Lists: </div>
    <button onclick="tList('unordered')" class="snip_buttons">&lt;ul&gt;</button>
    <button onclick="tList('ordered')" class="snip_buttons">&lt;ol&gt;</button>
    <button onclick="listItem()" class="snip_buttons">&lt;listitem&gt;</button>
</div>
<div class="buttonrow">
    <div class="snip_heading">Links:</div>
    <button onclick="tVariable()" class="snip_buttons">&lt;variable&gt;</button>
    <button onclick="tEmbed()" class="snip_buttons">&lt;embed&gt;</button>
    <button onclick="tEmbedvar()" class="snip_buttons">&lt;embedvar&gt;</button>
    <button onclick="tLink()" class="snip_buttons">&lt;link&gt;</button>
</div>
