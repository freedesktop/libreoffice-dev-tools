<!DOCTYPE html>
<!--
* This file is part of the LibreOffice project.
*
* This Source Code Form is subject to the terms of the Mozilla Public
* License, v. 2.0. If a copy of the MPL was not distributed with this
* file, You can obtain one at http://mozilla.org/MPL/2.0/.
-->
<?php
require_once './config.php';
require_once './snippets.php';
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
    <script type="text/javascript" src="helpcontent2/help3xsl/prism.js"></script>
    <script type="text/javascript" src="autocomplete.js" defer=""></script>
    <script type="text/javascript" src="snippets.js" defer=""></script>
    <script type="text/javascript" src="DisplayArea.js"></script>
</head>

<body style="font-family:sans-serif;">
<div class="leftside">
    <h2>LibreOffice Documentation XHP Editor</h2>
    
    <form id="CMtextarea" class="form_area" method="post" action="index.php">
        <input type="submit" name="render_page" value="Render page"/>
        <input type="submit" name="get_patch" value="Generate patch"/>
        <input type="submit" name="check_xhp" value="Check XHP"/>
        <input type="submit" name="open_master" value="Open Master"/>
        <textarea id="xhpeditor" name="xhpdoc" form="CMtextarea"><?php echo $xhp;?></textarea></br>
    </form>
    <div class="buttonsdiv">
    <?php include './buttons.php';?>
    </div>
</div>
<div class="rightside">
    <?php
        $xhp = $_POST["xhpdoc"];
        if (isset($_POST["render_page"])) {
            echo '<h2>Rendered page</h2><div class="buttonrow"><div class="systembuttons"><p>System: ';
            $opSys = array("MAC", "WIN", "UNIX");
            foreach ($opSys as $value) {
               echo '<input type="radio" name="sys" onclick="setSystemSpan(\''.$value.'\')" class="snip_buttons">'.$value.'&nbsp;';
               }
            echo '</p></div><div class="applbuttons"><p> Module: ';
            $appModule = array("WRITER", "CALC", "IMPRESS", "DRAW", "BASE", "MATH");
            foreach ($appModule as $value){
                echo '<input type="radio" name="app" onclick="setApplSpan(\''.$value.'\')" class="snip_buttons">'.$value.'&nbsp;';
            }
            echo '</p></div></div><div id="renderedpage">';
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
            echo '</div>';
        }elseif (isset($_POST["check_xhp"])) {
            libxml_use_internal_errors(true);
            libxml_clear_errors();
            $root = 'helpdocument';
            $old = new DOMDocument;
            
            echo '<h2>XHP Verification</h2>';
            if ( !$old->loadXML($xhp) ) {
                $errors = libxml_get_errors();
                echo '<p class="bug">The XML is malformed!</p>';
                foreach ($errors as $error) {
                    echo display_xml_error($error, explode("\n", $old->saveXML()));
                }
                libxml_clear_errors();
            }else{
                echo "<p>No XML errors found</p>";
                $creator = new DOMImplementation;
                $doctype = $creator->createDocumentType($root, null, 'xmlhelp.dtd');
                $new = $creator->createDocument(null, null, $doctype);
                $new->encoding = "utf-8";

                $oldNode = $old->getElementsByTagName($root)->item(0);
                $newNode = $new->importNode($oldNode, true);
                $new->appendChild($newNode);

                echo '<h2>Check XHP:</h2>';
                if (!$new->validate()) {
                    echo '<p class="bug">This document does not verify the DTD and is NOT VALID!</p>';
                    $errors = libxml_get_errors();
                    foreach ($errors as $error) {
                        echo display_xml_error($error, explode("\n", $new->saveXML()));
                    }
                    libxml_clear_errors();
                }else{
                    echo '<p>This document verifies the DTD!</p>';
                };
                echo "<h2>Check duplicated Id's:</h2>";
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
                    echo '<p class="bug">Found duplicated ids:</p>';
                    foreach($dupped_array as $dup) {
                        echo "<p>$dup</p>";
                    }
                }else{
                    echo "<p>No duplicates ids found.</p>";
                }
            }
        }elseif (isset($_POST["get_patch"])) {
        echo '<h2>Get Patch:</h2>';
        } else {
        echo '<h2>Viewing Area</h2>';
        }
    ?>
</div>
</body>
</html>
