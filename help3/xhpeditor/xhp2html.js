/*
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 */

/* change these parameters to fit your installation */

// Codemirror configuration 

var editor = CodeMirror.fromTextArea(document.getElementById("xhpeditor"), {
    lineNumbers: true,
    theme: "default",
    mode: "xml",
    lineWrapping: true,
    autoCloseTags: true,
    extraKeys: {
        "F11": function(cm) {
          cm.setOption("fullScreen", !cm.getOption("fullScreen"));
          document.getElementById("editorpageheader").style.display=(cm.getOption("fullScreen")) ? "none" : "block";
        },
        "Esc": function(cm) {
          if (cm.getOption("fullScreen")) {
              cm.setOption("fullScreen", false);
              document.getElementById("editorpageheader").style.display="block";
          }
        },
        "'<'": completeAfter,
        "'/'": completeIfAfterLt,
        "' '": completeIfInTag,
        "'='": completeIfInTag,
        "Ctrl-Space": "autocomplete"
    },
    hintOptions: {schemaInfo: this.xhptags}
});

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

// XML parser of the poor...
function getFileNameFromXML(){
    var textXML = editor.doc.getValue();
    var p1=textXML.lastIndexOf('<filename>');
    var p2=textXML.lastIndexOf('</filename>');
    return textXML.substring(p1+10,p2).split('/').pop();
}


// Function to download data to a file
// source: https://stackoverflow.com/questions/13405129/javascript-create-and-save-file
function downloadFile(data, filename, type) {
    var file = new Blob([data], {type: type});
    if (window.navigator.msSaveOrOpenBlob) // IE10+
        window.navigator.msSaveOrOpenBlob(file, filename);
    else { // Others
        var a = document.createElement("a"),
                url = URL.createObjectURL(file);
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        setTimeout(function() {
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);  
        }, 0); 
    }
}
