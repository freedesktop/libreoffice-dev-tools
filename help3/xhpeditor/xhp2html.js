/*
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 */

/* change these parameters to fit your installation */


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
    xhttp.open("GET", filename, false);
    try {xhttp.responseType = "msxml-document"} catch(err) {} // Helping IE11
//     if isXML=true return XML otherwise return a text string
    xhttp.send(null);
    var response =  (isXML) ? xhttp.responseXML : xhttp.responseText;
    return response;
}

function loadText(filename){
    var text = loadDoc(filename,false);
    editor.doc.setValue(text);
}

function readSingleFile(e) {
  var file = e.target.files[0];

  if (!file) {
    return;
  }
  var reader = new FileReader();
  reader.onload = function(e) {
    var contents = e.target.result;
    editor.doc.setValue(contents);
  };
  reader.readAsText(file);
}

document.getElementById('file-input').addEventListener('change', readSingleFile, false);

