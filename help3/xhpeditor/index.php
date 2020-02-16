<!DOCTYPE html>
<!--
* This file is part of the LibreOffice project.
*
* This Source Code Form is subject to the terms of the Mozilla Public
* License, v. 2.0. If a copy of the MPL was not distributed with this
* file, You can obtain one at https://mozilla.org/MPL/2.0/.
-->
<?php
require_once './config.php';
require_once './snippets.php';
$xhp = $_POST["xhpdoc"];
?>
<html>
<head>
<meta charset="utf-8"/>
    <title>LibreOffice XHP Editor</title>
    <link rel="shortcut icon" href="favicon.ico"/>
    <link type="text/css" rel="stylesheet" href="cm/lib/codemirror.css">
    <link type="text/css" rel="stylesheet" href="cm/addon/hint/show-hint.css">
    <link type="text/css" rel="stylesheet" href="cm/addon/dialog/dialog.css">
    <link type="text/css" rel="stylesheet" href="cm/addon/display/fullscreen.css">
    <link type="text/css" rel="stylesheet" href="xhpeditor.css">
    <link type="text/css" rel="stylesheet" href="helpcontent2/help3xsl/normalize.css">
    <link type="text/css" rel="stylesheet" href="helpcontent2/help3xsl/prism.css">
    <link type="text/css" rel="stylesheet" href="DisplayArea.css">
    <link type="text/css" rel="stylesheet" href="cm/addon/search/matchesonscrollbar.css">

    <script type="application/javascript" src="cm/lib/codemirror.js"></script>
    <script type="application/javascript" src="cm/mode/xml/xml.js"></script>
    <script type="application/javascript" src="cm/addon/dialog/dialog.js"></script> 
    <script type="application/javascript" src="cm/addon/hint/show-hint.js"></script>
    <script type="application/javascript" src="cm/addon/hint/xml-hint.js"></script>
    <script type="application/javascript" src="cm/addon/edit/matchtags.js"></script>
    <script type="application/javascript" src="cm/addon/edit/closetag.js"></script>
    <script type="application/javascript" src="cm/addon/fold/xml-fold.js"></script>
    <script type="application/javascript" src="cm/addon/fold/foldcode.js"></script>
    <script type="application/javascript" src="cm/addon/search/search.js"></script>
    <script type="application/javascript" src="cm/addon/search/searchcursor.js"></script>
    <script type="application/javascript" src="cm/addon/search/jump-to-line.js"></script>
    <script type="application/javascript" src="cm/addon/search/matchesonscrollbar.js"></script>
    <script type="application/javascript" src="cm/addon/display/fullscreen.js"></script>
    <script type="application/javascript" src="cm/addon/scroll/annotatescrollbar.js"></script>
    
    <script type="application/javascript" src="helpcontent2/help3xsl/prism.js"></script>
    <script type="application/javascript" src="autocomplete.js"></script>
    <script type="application/javascript" src="snippets.js"></script>
    <script type="application/javascript" src="DisplayArea.js"></script>
    <script type="application/javascript" src="xhp2html.js" defer></script>
</head>

<body style="font-family:sans-serif;">
    <div id="editorpageheader">
        <h2>LibreOffice Documentation XHP Editor</h2>
        <?php include './menu.php';?>
    </div>
    <div id="editortextarea">
        <form id="CMtextarea" method="post" action="index.php">
            <textarea id="xhpeditor" name="xhpdoc" form="CMtextarea"><?php echo htmlspecialchars($xhp,ENT_NOQUOTES);?></textarea>
        </form>
    </div>
    <?php
        $xhp = $_POST["xhpdoc"];
        $xhp_filename = simplexml_load_string($xhp)->xpath("//filename");
        if (isset($_POST["render_page"])) {
            echo '<div id="renderedpageheader"><h2>Rendered page: '.$xhp_filename[0];
            echo '</h2><div class="buttonrow"><div class="systembuttons"><p>System: ';
            $opSys = array("MAC", "WIN", "UNIX");
            foreach ($opSys as $value) {
               echo '<input type="radio" name="sys" onclick="setSystemSpan(\''.$value.'\')">'.$value.'&nbsp;';
               }
            echo '</p></div><div class="applbuttons"><p> Module: ';
            $appModule = array("WRITER", "CALC", "IMPRESS", "DRAW", "BASE", "MATH");
            foreach ($appModule as $value){
                echo '<input type="radio" name="app" onclick="setApplSpan(\''.$value.'\')">'.$value.'&nbsp;';
            }
            echo '</p></div></div></div><div id="renderedpage">';
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
            echo "</div>";
        }elseif (isset($_POST["check_xhp"])) {
            libxml_use_internal_errors(true);
            libxml_clear_errors();
            $root = 'helpdocument';
            $old = new DOMDocument;
            
            echo '<div id="renderedpageheader"><h2>Help File Verification: '.$xhp_filename[0];
            echo '</h2></div>';
            echo '<div id="renderedpage"><h3>Check XML Formation</h3>';
            if ( !$old->loadXML($xhp) ) {
                $errors = libxml_get_errors();
                echo '<p class="bug">The XML is malformed!</p>';
                foreach ($errors as $error) {
                    echo display_xml_error($error, explode("\n", $old->saveXML()));
                }
                libxml_clear_errors();
            }else{
                echo "<p>No XML errors found!</p>";
                $creator = new DOMImplementation;
                $doctype = $creator->createDocumentType($root, null, 'xmlhelp.dtd');
                $new = $creator->createDocument(null, null, $doctype);
                $new->encoding = "utf-8";

                $oldNode = $old->getElementsByTagName($root)->item(0);
                $newNode = $new->importNode($oldNode, true);
                $new->appendChild($newNode);
                libxml_clear_errors();
                echo '<h3>Check XML Document Type Definition:</h3>';
                if (!$new->validate()) {
                    echo '<p class="bug">This document does not verify the DTD and is <b>NOT VALID!</b></p>';
                    $errors = libxml_get_errors();
                    foreach ($errors as $error) {
                        echo display_xml_error($error, explode("\n", $new->saveXML()));
                    }
                    libxml_clear_errors();
                }else{
                    echo '<p>No DTD errors found!</p>';
                };
                echo "<h3>Check duplicated id= :</h3>";
                $tags_id_uniq = array('paragraph','note','warning','tip','h1','h2','h3','h4','h5','h6');
                $xmlarray = simplexml_load_string($xhp);
                $i=0;
                foreach($tags_id_uniq as $tag_uniq) {
                    foreach ($xmlarray->xpath("//$tag_uniq") as $tag){
                        $idarray[$i] = $tag['id'];
                        ++$i;
                    }
                }
                $dupped_array =  array_values(array_unique(array_diff_key($idarray, array_unique($idarray))));
                if (count($dupped_array) > 0){
                    echo '<p class="bug">Found duplicated id= attributes:</p>';
                    foreach($dupped_array as $dup) {
                        echo "<p>$dup</p>";
                    }
                }else{
                    echo "<p>No duplicate id= found.</p></div>";
                }
            }
        }elseif (isset($_POST["get_patch"])) {
        echo '<div id="renderedpageheader">';
        echo '<h2>Get Patch:</h2>';
        echo "</div>";
        } else {
        echo '<div id="renderedpageheader">';
        echo '<h2>Viewing Area</h2>';
        echo "</div>";
        };
    ?>
</body>
</html>
