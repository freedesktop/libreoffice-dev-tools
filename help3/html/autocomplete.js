/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/*
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */


// Here we define the schema for XHP, for the auto-completion

var tags = {
    "!top": ["helpdocument"],
    helpdocument: {
        children: ["meta", "body"],
        attrs: {version: ["1.0"]},
    },
    meta: {
        attrs: {localise: ["false"]},
        children: ["topic", "history"]
    },
    body: {
        attrs: {name: null},
        children: ["section", "paragraph", "table", "comment", "bookmark", "switch", "embed", "list", "sort"]
    },
    section: {
        attrs: {id: null, localise: ["false"]},
        children: ["section", "paragraph", "table", "list", "comment", "embed", "switch", "sort"]
    },
};

// And here's the code that provides the auto-completion in the editor

function completeAfter(cm, pred) {
    var cur = cm.getCursor();
    if (!pred || pred()) setTimeout(function() {
        if (!cm.state.completionActive)
            cm.showHint({completeSingle: false});
    }, 100);
    return CodeMirror.Pass;
}

function completeIfAfterLt(cm) {
    return completeAfter(cm, function() {
        var cur = cm.getCursor();
        return cm.getRange(CodeMirror.Pos(cur.line, cur.ch - 1), cur) == "<";
    });
}

function completeIfInTag(cm) {
    return completeAfter(cm, function() {
        var tok = cm.getTokenAt(cm.getCursor());
        if (tok.type == "string" && (!/['"]/.test(tok.string.charAt(tok.string.length - 1)) || tok.string.length == 1)) return false;
                         var inner = CodeMirror.innerMode(cm.getMode(), tok.state).state;
        return inner.tagName;
    });
}

var editor = CodeMirror.fromTextArea(document.getElementById("xhpeditor"), {
    lineNumbers: true,
    mode: "text/html",
    matchBrackets: true,
    theme: "default",
    extraKeys: {
        "'<'": completeAfter,
        "'/'": completeIfAfterLt,
        "' '": completeIfInTag,
        "'='": completeIfInTag,
        "Ctrl-Space": "autocomplete"
    },
    hintOptions: {schemaInfo: tags}
});
/* vim:set shiftwidth=4 softtabstop=4 expandtab cinoptions=b1,g0,N-s cinkeys+=0=break: */
