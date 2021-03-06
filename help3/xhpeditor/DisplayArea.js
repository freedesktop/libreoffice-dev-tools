/*
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 *
 */

// scripts for rendered DisplayArea

// Used to set system in case, caseinline=sys
function setSystemSpan(system) {
    hideSystemSpan();
    var spans = document.querySelectorAll("[class^=switch]");//this selector can be bounded to DisplayArea div
    for (z = 0; z < spans.length; z++) {
        var id = spans[z].getAttribute("id");
        if (id === null) {
            continue;
        }
        else if (id.startsWith("swlnsys")) {
            var y = spans[z].getElementsByTagName("SPAN");
            var n = y.length;
            var foundSystem = false;
            // unhide selectively
            for (i = 0; i < n; i++) {
                if (y[i].getAttribute("id") === null){
                    continue;
                }
                else if( y[i].getAttribute("id").startsWith(system)){
                    y[i].removeAttribute("hidden");
                    foundSystem=true;
                }
            }
            for (i = 0; i < n; i++) {
                if (y[i].getAttribute("id") === null){
                    continue;
                }
                else if( y[i].getAttribute("id").startsWith("default")){
                    if(!foundSystem){
                        y[i].removeAttribute("hidden");
                    }
                }
            }
        }
    }
}
function hideSystemSpan(){
    var spans = document.querySelectorAll("[class^=switch]");//this selector can be bounded to DisplayArea div
    for (z = 0; z < spans.length; z++) {
        var id = spans[z].getAttribute("id");
        if (id === null) {
            continue;
        }else if(id.startsWith("swlnsys")) {
            var y = spans[z].getElementsByTagName("SPAN");
            var n = y.length;
            for (i = 0; i < n; i++) {
                if (y[i].getAttribute("id") === null){
                    continue;
                }
                else if( y[i].getAttribute("id").startsWith("MAC")){y[i].setAttribute("hidden","true");}
                else if( y[i].getAttribute("id").startsWith("WIN")){y[i].setAttribute("hidden","true");}
                else if( y[i].getAttribute("id").startsWith("UNIX")){y[i].setAttribute("hidden","true");}
                else if( y[i].getAttribute("id").startsWith("default")){y[i].setAttribute("hidden","true");}
            }
        }
    }
}
// Used to set application in case, caseinline=appl
function setApplSpan(appl) {
    hideApplSpan();
    var spans = document.querySelectorAll("[class^=switch]");//this selector can be bounded to DisplayArea div
    for (z = 0; z < spans.length; z++) {
        var id = spans[z].getAttribute("id");
        if (id === null) {
            continue;
        }
        else if (id.startsWith("swlnappl")) {
            var y = spans[z].getElementsByTagName("SPAN");
            var n = y.length;
            var foundSystem = false;
            // unhide selectively
            for (i = 0; i < n; i++) {
                if (y[i].getAttribute("id") === null){
                    continue;
                }
                else if( y[i].getAttribute("id").startsWith(appl)){
                    y[i].removeAttribute("hidden");
                    foundSystem=true;
                }
            }
            for (i = 0; i < n; i++) {
                if (y[i].getAttribute("id") === null){
                    continue;
                }
                else if( y[i].getAttribute("id").startsWith("default")){
                    if(!foundSystem){
                        y[i].removeAttribute("hidden");
                    }
                }
            }
        }
    }
}
function hideApplSpan(){
    var spans = document.querySelectorAll("[class^=switch]"); //this selector can be bounded to DisplayArea div
    for (z = 0; z < spans.length; z++) {
        var id = spans[z].getAttribute("id");
        if (id === null) {
            continue;
        }else if(id.startsWith("swlnappl")) {
            var y = spans[z].getElementsByTagName("SPAN");
            var n = y.length;
            for (i = 0; i < n; i++) {
                if (y[i].getAttribute("id") === null){
                    continue;
                }
                else if( y[i].getAttribute("id").startsWith("WRITER")){y[i].setAttribute("hidden","true");}
                else if( y[i].getAttribute("id").startsWith("CALC")){y[i].setAttribute("hidden","true");}
                else if( y[i].getAttribute("id").startsWith("IMPRESS")){y[i].setAttribute("hidden","true");}
                else if( y[i].getAttribute("id").startsWith("DRAW")){y[i].setAttribute("hidden","true");}
                else if( y[i].getAttribute("id").startsWith("BASE")){y[i].setAttribute("hidden","true");}
                else if( y[i].getAttribute("id").startsWith("MATH")){y[i].setAttribute("hidden","true");}
                else if( y[i].getAttribute("id").startsWith("default")){y[i].setAttribute("hidden","true");}
            }
        }
    }
}
