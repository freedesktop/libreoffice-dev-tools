/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/*
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */


// Here we define the schema for XHP, for the auto-completion

var xhptags = {
    "!top": ["helpdocument"],
    helpdocument: {
        children: ["meta", "body"],
        attrs: {version: ["1.0"]},
    },
    meta: {
        children: ["topic", "history"],
        attrs: {localise: ["false"]},
    },
    topic: {
        children: ["title", "bookmark", "filename"],
        attrs: {id: null, indexer: ["exclude", "include"]}
    },
    history: {
        children: ["created", "lastedited"]
    },
    created: {
        attrs: {date: null}
    },
    lastedited: {
        attrs: {date: null}
    },
    body: {
        attrs: {name: null, localize: ["false"]},
        children: ["section", "paragraph", "table", "comment", "bookmark", "switch", "embed", "list", "sort"]
    },
    section: {
        attrs: {id: null, localise: ["false"]},
        children: ["section", "paragraph", "table", "list", "comment", "embed", "switch", "sort"]
    },
    paragraph: {
        attrs: {'xml-lang': null, role: null, level: null, id: null, l10n: null, oldref: null, localize: ["false"]},
        children: ["image", "embedvar", "br", "emph", "help-id-missing", "item", "link", "switchinline", "variable", "ahelp", "object", "bookmark"]
    },
    image: {
        attrs: {src: null, width: null, height: null, id: null, localize: null},
        children: ["caption", "alt"]
    },
    caption: {
        attrs: {id: null, localize: ["false"]},
        children: ["embedvar", "br", "emph", "item", "link", "switchinline", "variable"]
    },
    alt: {
        attrs: {'xml-lang': null, id: null, localize: ["false"]},
    },
    embedvar: {
        attrs: {href: null, markup: ["keep", "ignore"]},
    },
    br: {
        attrs: {'xml-lang': null, id: null, localize: ["false"]},
        children: ["embedvar", "br", "emph", "item", "link", "switchinline", "variable"]
    },
    emph: {
        children: ["item", "comment", "help-id-missing"]
    },
    item: {
        attrs: {type: null},
    },
    link: {
        attrs: {href: null, name: null, type: null},
        children: ["emph", "item", "variable", "embedvar", "switchinline"]
    },
    switchinline: {
        attrs: {select: null},
        children: ["caseinline", "defaultinline"]
    },
    variable: {
        attrs: {id: null, visibility: ["hidden", "visible"]},
        children: ["ahelp", "embedvar", "br", "emph", "item", "link", "variable", "image", "object", "switchinline"]
    },
    ahelp: {
        attrs: {hid: null, visibility: ["hidden", "visible"]},
        children: ["comment", "embedvar", "br", "emph", "item", "link", "variable"]
    },
    object: {
        attrs: {type: null, id: null, data: null, width: null, height: null},
    },
    bookmark: {
        attrs: {branch: null, 'xml-lang': null, localize: ["false"]},
        children: ["bookmark-value"]
    },
    'bookmark-value': {
        children: ["embedvar"]
    },
    table: {
        attrs: {name: null, width: null, height: null, unit: ["px", "pt"], class: null, id: null, localize: ["false"]},
        children: ["caption", "tablerow"]
    },
    tablerow: {
        attrs: {height: null, unit: ["px", "pt", "cm", "in"], class: null, localize: ["false"]},
        children: ["tablecell"]
    },
    tablecell: {
        attrs: {colspan: null, rowspan: null, width: null, unit: ["px", "pt", "cm", "in", "pct"], class: null, localize: ["false"]},
    },
    list: {
        attrs: {type: ["ordered", "unordered"], startwith: null, format: ["1", "i", "I", "a"], bullet: ["disc", "circle", "square"], localize: ["false"], sorted: ["asc", "desc"]},
        children: ["listitem", "comment"]
    },
    listitem: {
        attrs: {format: ["1", "i", "I", "a"], bullet: ["disc", "circle"], localize: ["false"], class: null},
        children: ["comment", "section", "paragraph", "table", "switch", "embed", "bookmark"]
    },
    sort: {
        attrs: {order: ["asc", "desc"]},
        children: ["section"]
    },
    embed: {
        attrs: {href: null, role: null, level: null},
    },
    switch: {
        attrs: {select: ["sys"], localize: ["false"]},
        children: ["case", "comment", "default"]
    },
    case: {
        attrs: {select: null},
        children: ["paragraph", "table", "comment", "bookmark", "embed", "list", "switch", "section"]
    },
    default: {
        children: ["paragraph", "table", "comment", "bookmark", "embed", "list", "section"]
    },
    title: {
        attrs: {'xml-lang': null, id: null, localize: ["false"]},
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

/* vim:set shiftwidth=4 softtabstop=4 expandtab cinoptions=b1,g0,N-s cinkeys+=0=break: */
