/*
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 */

var helpcontent2 = "/hc2/";
var productname = "LibreOffice";
var productversion = "6.3";
var root = helpcontent2 + "source/";
var language = "en-US";
var local = "no";
var xhttp;

function loadDoc(filename, isXML)
{
    if (window.ActiveXObject)
    {
        xhttp = new ActiveXObject("Msxml2.XMLHTTP");
    }
    else
    {
        xhttp = new XMLHttpRequest();
    }

//     xhttp.onreadystatechange = function() {
//         if (this.readyState == 4 && this.status == 200) {
//             // Typical action to be performed when the document is ready:
//         }
//     };

    xhttp.open("GET", filename, false);
    try {xhttp.responseType = "msxml-document"} catch(err) {} // Helping IE11
//     if isXML=true return XML otherwise return a text string
    xhttp.send(null);
    return (isXML) ? xhttp.responseXML : xhttp.responseText;
}

function displayResult()
{
    // Clean current renderedpage <div> contents
    document.getElementById("renderedpage").innerHTML = null;
    // trigger update on textarea contents, after editing anything
    editor.changeGeneration();
    // create a DOM parser for textarea contents
    var oParser = new DOMParser();
    // Parse XML contents
    var xml = oParser.parseFromString( editor.doc.getValue(), "application/xml");
    // Load XSLT
    var xsl = loadDoc("/ed/ed_transform.xsl", true);
    // Process transformation & display in 'renderedpage'
    // code for IE
    if (window.ActiveXObject || xhttp.responseType == "msxml-document")
    {
        ex = xml.transformNode(xsl);
        document.getElementById("renderedpage").innerHTML = ex;
    }
    // code for Chrome, Firefox, Opera, etc.
    else if (document.implementation && document.implementation.createDocument)
    {
        var xsltProcessor = new XSLTProcessor();
        xsltProcessor.importStylesheet(xsl);
        xsltProcessor.setParameter("", "root", root)
        xsltProcessor.setParameter("", "local", local)
        xsltProcessor.setParameter("", "language", language)
        xsltProcessor.setParameter("", "productname", productname)
        xsltProcessor.setParameter("", "productversion", productversion)
//         document.getElementById("renderedpage").innerHTML('<link  type="text/css" href="/ed/hc2/help3xsl/default.css" rel="Stylesheet" />"');
        var resultDocument = xsltProcessor.transformToFragment(xml, document);

        document.getElementById("renderedpage").appendChild(resultDocument.getElementById("DisplayArea"));
    }
}
function loadText(filename){
    var text = loadDoc(helpcontent2 + filename,false);
    editor.doc.setValue(text);
}
function saveFile(){
    var data = new FormData();
    data.append("data" , editor.doc.getValue());
    var xhr = (window.XMLHttpRequest) ? new XMLHttpRequest() : new activeXObject("Microsoft.XMLHTTP");
    xhr.open( 'post', '/ed/savexhp.php', true );
    xhr.send(data);
}
