/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/*
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */


// Code for buttons underneath the editor

// Global document snippets

function startNewXHPDoc() {
    if (confirm('Lose all changes and start fresh?')) {
        var a1 =
        editor.doc.setValue('<?xml version="1.0" encoding="UTF-8"?>\n<helpdocument version="1.0">\n<!--\n * This file is part of the LibreOffice project.\n *\n * This Source Code Form is subject to the terms of the Mozilla Public\n * License, v. 2.0. If a copy of the MPL was not distributed with this\n * file, You can obtain one at http://mozilla.org/MPL/2.0/.\n *\n-->\n\n<meta>\n  <topic id="CHANGE ME" indexer="include" status="PUBLISH">\n    <title id="tit" xml-lang="en-US">TITLE ME</title>\n    <filename>FILE NAME ME</filename>\n  </topic>\n</meta>\n<body>\n\n</body>\n</helpdocument>');
    }
}
function docHeading() {
    var a1 = '<section id="CHANGE ME">\n    <bookmark id="' + random('bm') + '" xml-lang="en-US" branch="hid/CHANGE ME" localize="false"/>\n';
    var a2 = '    <h1 id="' + random('hd') + '"><link href="HELP FILE URL" name="CHANGE ME">CHANGE ME</link></h1>\n';
    var a3 = '    <paragraph id="' + random('par') + '" role="paragraph"><variable id="CHANGE ME"><ahelp hid="CHANGE ME">CHANGE ME</ahelp></variable></paragraph>\n\n</section>\n';
    editor.replaceRange(a1 + a2 + a3 , editor.doc.getCursor());
}

// Paragraph
function paragraph(role) {
    var a0 = '<paragraph role="'+ role + '" id="' + random("par") + '">'
    var a1 = '</paragraph>';
    editor.replaceSelection(a0 + editor.doc.getSelection() + a1,'');
}

function note() {
    var a0 = '<note id="' + random('par') + '">'
    var a1 = '</note>';
    editor.replaceSelection(a0 + editor.doc.getSelection() + a1,'');
}

function tip() {
    var a0 = '<tip id="' + random('par') + '">'
    var a1 = '</tip>';
    editor.replaceSelection(a0 + editor.doc.getSelection() + a1,'');
}

function warning() {
    var a0 = '<warning id="' + random('par') + '">'
    var a1 = '</warning>';
    editor.replaceSelection(a0 + editor.doc.getSelection() + a1,'');
}

function heading(level) {
    var a0 = '<h'+ level +' id="' + random('hd') + '">'
    var a1 = '</h' + level+'>';
    editor.replaceSelection(a0 + editor.doc.getSelection() + a1,'');
}

function bascode_par() {
    var a1 = '<paragraph role="bascode" id="' + random('bas') + '">';
    var a2 = '</paragraph>';
    editor.replaceSelection(a1 + editor.doc.getSelection() + a2,'');
}
function pycode_par() {
    var a1 = '<paragraph role="pycode" id="' + random('pyc') + '">';
    var a2 = '</paragraph>';
    editor.replaceSelection(a1 + editor.doc.getSelection() + a2,'');
}

function image_par() {
    var a1 = '<paragraph role="image" id="' + random('par') + '"><image src="media/CHANGE-ME" id="' + random('img') + '" width="" height=""><alt id="' + random('alt') +'">';
    var a2 = '</alt></image></paragraph>';
    editor.replaceSelection(a1 + editor.doc.getSelection() + a2,'');
}
// Tables
// simple table cell
function tCell (role){
    return '       <tablecell>\n           <paragraph id="' + random('par') + '" role="' + role + '"></paragraph>\n       </tablecell>\n';
}

function iconTable() {
    var a1 = '<table id="' + random('tab') + '">\n    <tablerow>\n        <tablecell>\n            ';
    var a2 = '<paragraph role="image" id="' + random('par') + '">\n<image src="media/CHANGE-ME" id="' + random('img') + '" width="" height=""><alt id="' + random('alt') +'">Icon</alt></image>\n            </paragraph>';
    var a3 = '\n       </tablecell>\n' + tCell("paragraph") + '    </tablerow>\n</table>\n';
    editor.replaceRange(a1 + a2 + a3, editor.doc.getCursor());
}

function tableCell() {
    editor.replaceRange(tCell('tablecontent'), editor.doc.getCursor());
}

function table2R3C() {
    var a1 = '<table id="' + random('tab') + '">\n';
    var a2 = '   <tablerow>\n';
    var a4 = '   </tablerow>\n';
    var a5 = a4 + '\n</table>\n';
    editor.replaceRange(a1 + a2 + tCell('tablehead') + tCell('tablehead') + tCell('tablehead') + a4 + a2 + tCell('tablecontent') + tCell('tablecontent') + tCell('tablecontent') + a5, editor.doc.getCursor());
}

function tableRow() {
    editor.replaceRange('    <tablerow>\n' + tCell('tablecontent') + '\n    </tablerow>\n', editor.doc.getCursor());
}

// Sections
function related_topics() {
    editor.replaceRange('<section id="relatedtopics">\n   \n</section>\n', editor.doc.getCursor());
}

function howtoget() {
    editor.replaceRange('<section id="howtoget">\n   \n</section>\n', editor.doc.getCursor());
}

function bascode_div() {
    editor.replaceRange('<bascode>\n   \n</bascode>\n', editor.doc.getCursor());
}

function pycode_div() {
    editor.replaceRange('<pycode>\n   \n</pycode>\n', editor.doc.getCursor());
}

function section_div() {
    editor.replaceRange('<section id="CHANGE ME">\n   \n</section>\n', editor.doc.getCursor());
}
// Bookmarks
function aHelp() {
    editor.replaceRange('<ahelp hid="HID PATH ME" visibility="hidden">'+ editor.doc.getSelection() +'</ahelp>', editor.doc.getCursor());
}

function bookmarkValue() {
    var a1 = '<bookmark_value>CHANGE ME;CHANGE ME TOO</bookmark_value>\n';
    editor.replaceRange(a1, editor.doc.getCursor());
}

function bookmarkBranch() {
    var a1 = '<bookmark xml-lang="en-US" branch="hid/CHANGE ME(path/to/dialog/widget)" id="' + random('bm') + '" localize="false"/>\n';
    editor.replaceRange(a1, editor.doc.getCursor());
}

function bookmarkNoWidget() {
    var a1 = '<bookmark xml-lang="en-US" branch="hid/CHANGE ME(/path/to/dialog)/@@nowidget@@" id="' + random('bm') + '" localize="false"/>\n';
    editor.replaceRange(a1, editor.doc.getCursor());
}

function bookmarkIndex() {
    var a1 = '<bookmark xml-lang="en-US" branch="index" id="' + random('bm') + '">\n<bookmark_value>CHANGE ME;CHANGE ME TOO</bookmark_value>\n\n</bookmark>\n';
    editor.replaceRange(a1, editor.doc.getCursor());
}

//characters snippets

function emph() {
    editor.replaceSelection('<emph>'+ editor.doc.getSelection() +'</emph>','');
}

function item(type) {
    editor.replaceSelection('<item type="'+ type + '">'+ editor.doc.getSelection() +'</item>','');
}

function c_menuitem() {
    editor.replaceSelection('<menuitem>'+ editor.doc.getSelection() +'</menuitem> ','');
}
function _literal() {
    editor.replaceSelection('<literal>'+ editor.doc.getSelection() +'</literal>','');
}
function _keystroke() {
    editor.replaceSelection('<keycode>'+ editor.doc.getSelection() +'</keycode>','');
}
function _input() {
    editor.replaceSelection('<input>'+ editor.doc.getSelection() +'</input>','');
}
function _widget() {
    editor.replaceSelection('<widget>'+ editor.doc.getSelection() +'</widget>','');
}
// switches

function switchXHP(type) {
    var type_string = (type=='sys') ? "MAC | UNIX | WIN" : "WRITER | CALC | IMPRESS | DRAW | BASE | MATH";
    var a1 = '<switch select="' + type + '">\n';
    var a2 = '<case select="' + type_string +'">\nCHANGE ME\n</case>\n';
    var a3 = '<default>\nDEFAULT STUFF\n</default>\n</switch>\n';
    editor.replaceRange(a1 + a2 + a3, editor.doc.getCursor());
}

function switchInline(type) {
    var type_string = (type=='sys') ? "MAC | UNIX | WIN" : "WRITER | CALC | IMPRESS | DRAW | BASE | MATH";
    var a1 = '<switchinline select="' + type + '">';
    var a2 = '<caseinline  select="' + type_string +'">CHANGE ME</caseinline>';
    var a3 = '<defaultinline>DEFAULT STUFF</defaultinline></switchinline>';
    editor.replaceRange(a1 + a2 + a3, editor.doc.getCursor());
}
function MenuPrefMAC(){
    editor.replaceRange('<switchinline select="sys"><caseinline select="MAC"><menuitem>%PRODUCTNAME - Preferences</menuitem></caseinline><defaultinline><menuitem>Tools - Options</menuitem></defaultinline></switchinline><menuitem> - </menuitem> ', editor.doc.getCursor());
}
function KeyMAC(){
    editor.replaceRange('<switchinline select="sys"><caseinline select="MAC"><keycode>command</keycode></caseinline><defaultinline><keycode>Ctrl</keycode></defaultinline></switchinline><keycode>+</keycode>', editor.doc.getCursor());
}
// lists
function tList(mode){
    var a1 = '<list type="' + mode + '">\n\n</list>\n';
    editor.replaceRange(a1, editor.doc.getCursor());
}

function listItem(){
    var a1 = '    <listitem>\n        <paragraph id="' + random('par') + '" role="listitem">';
    var a2 = '</paragraph>\n    </listitem>\n';
    editor.replaceSelection(a1+ editor.doc.getSelection() + a2,'');
}

// Variables, embeds, link

function tVariable() {
    var a1 = '<variable id="CHANGE ME">';
    var a2 = '</variable>';
    editor.replaceSelection(a1 + editor.doc.getSelection() + a2,'');
}
function tEmbed(){
    var a1 = '<embed href="text/CHANGE ME(path/to/xhp/file#select id)"/>\n';
    editor.replaceRange(a1, editor.doc.getCursor());
}
function tEmbedvar(){
    var a1 = '<embedvar href="text/CHANGE ME(path/to/xhp/file#select id)" markup="ignore/keep"/>';
    editor.replaceRange(a1, editor.doc.getCursor());
}
 function tLink(){
     var a1 ='<link href="text/CHANGE ME(path/to/xhp/file#select id)" name="CHANGE ME">';
     var a2 = '</link>';
     editor.replaceSelection(a1 + editor.doc.getSelection() + a2,'');
}

/* javascript code for snippets (originally for KDE kate)*/
function fileName() { return document.fileName(); }
function fileUrl() { return document.url(); }
function encoding() { return document.encoding(); }
function selection() { return view.selectedText(); }
function year() { return new Date().getFullYear(); }
function upper(x) { return x.toUpperCase(); }
function lower(x) { return x.toLowerCase(); }
function random(x) {var d = new Date(); return x +'_id'+(Math.floor(Math.random() * 100) + 1) + d.getTime(); }
function helpFile() {var d = document.url(); var t = d.search("text/"); return d.substr(t); }

/* vim:set shiftwidth=4 softtabstop=4 expandtab cinoptions=b1,g0,N-s cinkeys+=0=break: */
