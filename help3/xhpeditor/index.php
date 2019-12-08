<!DOCTYPE html>
<!--
* This file is part of the LibreOffice project.
*
* This Source Code Form is subject to the terms of the Mozilla Public
* License, v. 2.0. If a copy of the MPL was not distributed with this
* file, You can obtain one at http://mozilla.org/MPL/2.0/.
-->
<?php 
require_once './class.Diff.php';
require_once './config.php';
$xhp = $_POST["xhpdoc"];
?>
<html>
<head>
<meta charset="utf-8"/>
    <title>LibreOffice Documentation XHP Editor</title>
    <link type="text/css" rel="stylesheet" href="xhpeditor.css">
    <link type="text/css" rel="stylesheet" href="lib/codemirror.css">
    <link type="text/css" rel="stylesheet" href="addon/hint/show-hint.css">
    <link type="text/css" rel="stylesheet" href="helpcontent2/help3xsl/normalize.css">
    <link type="text/css" rel="stylesheet" href="helpcontent2/help3xsl/prism.css">

    <script type="text/javascript" src="lib/codemirror.js"></script>
    <script type="text/javascript" src="addon/hint/show-hint.js"></script>
    <script type="text/javascript" src="addon/hint/xml-hint.js"></script>
    <script type="text/javascript" src="mode/xml/xml.js"></script>
    <script type="text/javascript" src="xhp2html.js" defer=""></script>
    <script type="text/javascript" src="helpcontent2/help3xsl/help2.js"></script>
    <script type="text/javascript" src="helpcontent2/help3xsl/prism.js"></script>
    <script type="text/javascript" src="helpcontent2/help3xsl/help.js" defer=""></script>
    <script type="text/javascript" src="autocomplete.js" defer=""></script>
    <script type="text/javascript" src="snippets.js" defer=""></script>
</head>

<body style="font-family:sans-serif;">
<div class="leftside">
    <h2>LibreOffice Documentation XHP Editor</h2>
    <form id="CMtextarea" class="form_area" action="index.php" method="post">
        <input type="submit" name="render_page" value="Render page"/>
        <input type="submit" name="get_patch" value="Generate patch"/>
        <input type="submit" name="check_xhp" value="Check XHP"/>
        <input type="submit" name="open_master" value="Open Master"/>
        <textarea id="xhpeditor" name="xhpdoc" form="CMtextarea">
<?php
if (isset($_POST["render_page"])) {
echo $xhp;
}elseif (isset($_POST["get_patch"])) {
echo "get patch";
}elseif (isset($_POST["check_xhp"])) {
echo "check xhp";
}elseif (isset($_POST["open_master"])) {
echo "Open in master repository";
}else{
echo $xhp;
} 
?>
        </textarea></br>
    </form>
    <div class="snip_heading">
        <div class="snip_div">Open:</div><input type="file" id="file-input" accept=".xhp"/>
        <div class="snip_div">Save:</div><button onclick="download(editor.getValue(),getFileNameFromXML(),'text/xml')" class="snip_buttons">Save local file</button>
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
    </div>
    <div class="snip_heading"><div class="snip_div">Tables:</div>
        <button onclick="table2R3C()" class="snip_buttons">Table Full</button>
        <button onclick="tableRow()" class="snip_buttons">TableRow</button>
        <button onclick="tableCell()" class="snip_buttons">Table Cell</button>
        <button onclick="iconTable()" class="snip_buttons">Icon Table</button>
    </div>
    <div class="snip_heading"><div class="snip_div">Paragraph:</div>
        <button onclick="paragraph('paragraph')" class="snip_buttons">paragraph</button>
        <button onclick="note()" class="snip_buttons">note</button>
        <button onclick="warning()" class="snip_buttons">warning</button>
        <button onclick="tip()" class="snip_buttons">tip</button>
        <button onclick="bascode_par()" class="snip_buttons">bascode-par</button>
        <button onclick="pycode_par()" class="snip_buttons">pycode-par</button>
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
        <button onclick="heading('1')" class="snip_buttons">H1</button>
        <button onclick="heading('2')" class="snip_buttons">H2</button>
        <button onclick="heading('3')" class="snip_buttons">H3</button>
        <button onclick="heading('4')" class="snip_buttons">H4</button>
    </div>
    <div class="snip_heading"><div class="snip_div">Switches:</div>
        <button onclick="switchXHP('appl')" class="snip_buttons">Switch appl</button>
        <button onclick="switchXHP('sys')" class="snip_buttons">Switch sys</button>
        <button onclick="switchInline('appl')" class="snip_buttons">Switchinline appl</button>
        <button onclick="switchInline('sys')" class="snip_buttons">Switchinline sys</button>
        <button onclick="MenuPrefMAC()" class="snip_buttons">Menu MAC</button>
        <button onclick="KeyMAC()" class="snip_buttons">Key MAC</button>
    </div>
    <div class="snip_heading"><div class="snip_div">Lists:</div>
        <button onclick="tList('unordered')" class="snip_buttons">UL</button>
        <button onclick="tList('ordered')" class="snip_buttons">OL</button>
        <button onclick="listItem()" class="snip_buttons">List Item</button>
    </div>
    <div class="snip_heading"><div class="snip_div">Links:</div>
        <button onclick="tVariable()" class="snip_buttons">Variable</button>
        <button onclick="tEmbed()" class="snip_buttons">Embed</button>
        <button onclick="tEmbedvar()" class="snip_buttons">Embedvar</button>
        <button onclick="tLink()" class="snip_buttons">Link</button>
    </div>
</div>
<div class="rightside">
    <?php 
        $xhp = $_POST["xhpdoc"];
        if (isset($_POST["render_page"])) {
            echo '<h2>Rendered page</h2><div id="renderedpage">';
            $xml = new DOMDocument();
            $xml->loadXML($xhp);
            $xsl = new DOMDocument;
            $xsl->load('ed_transform.xsl');
            $proc = new XSLTProcessor();
            $proc->setParameter("","root",$CONFIG["help_path"]);
            $proc->setParameter("","productname",$CONFIG["productname"]);
            $proc->setParameter("","iconpath",$CONFIG["icon_path"]);
            $proc->importStyleSheet($xsl);
            echo $proc->transformToXml($xml);
            echo'</div>';
        }
    ?>
</div>
</body>
</html>
