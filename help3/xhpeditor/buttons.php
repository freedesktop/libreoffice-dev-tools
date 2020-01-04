<?php
echo '<div class="snip_heading">
        <div class="snip_div">Open:</div><input type="file" id="file-input" accept=".xhp"/>
        <div class="snip_div">Save:</div><button onclick="download(editor.getValue(),getFileNameFromXML(),\'text/xml\')" class="snip_buttons">Save local file</button>
    </div>
    <div class="snip_heading"><div class="snip_div">Edit:</div>
        <button onclick="editor.undo()">Undo</button>
        <button onclick="editor.redo()">Redo</button>
    </div>
    <div class="snip_heading"><div class="snip_div">Document:</div>
        <button onclick="startNewXHPDoc()" class="snip_buttons">Start new XHP document</button>
        <button onclick="docHeading()" class="snip_buttons">DocHeading</button>
        <button onclick="snippet7()" class="snip_buttons">ahelp</button>
    </div>
    <div class="snip_heading"><div class="snip_div">Bookmarks: </div>
        <button onclick="bookmarkValue()" class="snip_buttons">bk-value</button>
        <button onclick="bookmarkBranch()" class="snip_buttons">bk-hid</button>
        <button onclick="bookmarkIndex()" class="snip_buttons">bk-index</button>
        <button onclick="bookmarkNoWidget()" class="snip_buttons">bk-nowidget</button>
    </div>
    <div class="snip_heading"><div class="snip_div">Sections: </div>
        <button onclick="section_div()" class="snip_buttons">Section</button>
        <button onclick="related_topics()" class="snip_buttons">Related Topics</button>
        <button onclick="howtoget()" class="snip_buttons">How to get</button>
        <button onclick="bascode_div()" class="snip_buttons">bascode div</button>
        <button onclick="pycode_div()" class="snip_buttons">pycode div</button>
    </div>
    <div class="snip_heading"><div class="snip_div">Tables:</div>
        <button onclick="table2R3C()" class="snip_buttons">Table Full</button>
        <button onclick="tableRow()" class="snip_buttons">Table Row</button>
        <button onclick="tableCell()" class="snip_buttons">Table Cell</button>
        <button onclick="iconTable()" class="snip_buttons">Icon Table</button>
    </div>
    <div class="snip_heading"><div class="snip_div">Paragraph:</div>
        <button onclick="paragraph(\'paragraph\')" class="snip_buttons">paragraph</button>
        <button onclick="note()" class="snip_buttons">note</button>
        <button onclick="warning()" class="snip_buttons">warning</button>
        <button onclick="tip()" class="snip_buttons">tip</button>
        <button onclick="bascode_par()" class="snip_buttons">bascode-par</button>
        <button onclick="pycode_par()" class="snip_buttons">pycode-par</button>
        <button onclick="image_par()" class="snip_buttons">image-par</button>
    </div>
    <div class="snip_heading"><div class="snip_div">Characters:</div>
        <button onclick="emph()" class="snip_buttons">emph</button>
        <button onclick="c_menuitem()" class="snip_buttons">menuitem</button>
        <button onclick="_input()" class="snip_buttons">input</button>
        <button onclick="_literal()" class="snip_buttons">literal</button>
        <button onclick="_keystroke()" class="snip_buttons">keystroke</button>
        <button onclick="_widget()" class="snip_buttons">widget</button>
    </div>
    <div class="snip_heading"><div class="snip_div">Headings:</div>
        <button onclick="heading(\'1\')" class="snip_buttons">H1</button>
        <button onclick="heading(\'2\')" class="snip_buttons">H2</button>
        <button onclick="heading(\'3\')" class="snip_buttons">H3</button>
        <button onclick="heading(\'4\')" class="snip_buttons">H4</button>
    </div>
    <div class="snip_heading"><div class="snip_div">Switches:</div>
        <button onclick="switchXHP(\'appl\')" class="snip_buttons">Switch appl</button>
        <button onclick="switchXHP(\'sys\')" class="snip_buttons">Switch sys</button>
        <button onclick="switchInline(\'appl\')" class="snip_buttons">Switchinline appl</button>
        <button onclick="switchInline(\'sys\')" class="snip_buttons">Switchinline sys</button>
        <button onclick="MenuPrefMAC()" class="snip_buttons">Menu MAC</button>
        <button onclick="KeyMAC()" class="snip_buttons">Key MAC</button>
    </div>
    <div class="snip_heading"><div class="snip_div">Lists:</div>
        <button onclick="tList(\'unordered\')" class="snip_buttons">UL</button>
        <button onclick="tList(\'ordered\')" class="snip_buttons">OL</button>
        <button onclick="listItem()" class="snip_buttons">List Item</button>
    </div>
    <div class="snip_heading"><div class="snip_div">Links:</div>
        <button onclick="tVariable()" class="snip_buttons">Variable</button>
        <button onclick="tEmbed()" class="snip_buttons">Embed</button>
        <button onclick="tEmbedvar()" class="snip_buttons">Embedvar</button>
        <button onclick="tLink()" class="snip_buttons">Link</button>
    </div>'
?>
