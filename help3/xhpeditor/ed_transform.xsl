<?xml version="1.0" encoding="UTF-8"?>
<!--
 * This file is part of the LibreOffice project.
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 *
 * This file incorporates work covered by the following license notice:
 *
 *   Licensed to the Apache Software Foundation (ASF) under one or more
 *   contributor license agreements. See the NOTICE file distributed
 *   with this work for additional information regarding copyright
 *   ownership. The ASF licenses this file to you under the Apache
 *   License, Version 2.0 (the "License"); you may not use this file
 *   except in compliance with the License. You may obtain a copy of
 *   the License at https://www.apache.org/licenses/LICENSE-2.0 .
-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:output indent="yes" method="html" doctype-system= "about:legacy-compat"/>

<xsl:include href="links.txt.xsl"/>
<!--
############################
# Variables and Parameters #
############################
//-->

<xsl:param name="root"/>
<xsl:param name="Language"/>
<xsl:param name="productname"/>
<xsl:param name="productversion"/>
<xsl:param name="iconpath"/>

<xsl:param name="System" select="'WIN'"/>
<xsl:param name="imgtheme" select="'colibre_svg'"/>
<xsl:param name="Id" />

<!-- General Usage -->
<xsl:variable name="am" select="'&amp;'"/>
<xsl:variable name="sl" select="'/'"/>
<xsl:variable name="qt" select="'&quot;'"/>

<!-- For calculating pixel sizes -->
<xsl:variable name="dpi" select="'96'"/>
<xsl:variable name="dpcm" select="'38'"/>
<xsl:variable name="dpmm" select="'3.8'"/>

<!-- Product brand variables used in the help files -->
<xsl:variable name="brand1" select="'$[officename]'"/>
<xsl:variable name="brand2" select="'$[officeversion]'"/>
<xsl:variable name="brand3" select="'%PRODUCTNAME'"/>
<xsl:variable name="brand4" select="'%PRODUCTVERSION'"/>

<!-- Installation -->
<xsl:variable name="target" select="''"/>
<xsl:variable name="source" select="$root"/>

<!-- meta data variables from the help file -->
<xsl:variable name="filename" select="/helpdocument/meta/topic/filename"/>
<xsl:variable name="title" select="/helpdocument/meta/topic/title"/>

<!-- the other parameters given by the help caller -->

<xsl:variable name="pversion">
	<xsl:value-of select="translate($productversion,' ','')"/>
</xsl:variable>
<!-- this is were the images are -->

<xsl:variable name="lang" select="$Language"/>
<xsl:variable name="urlpre" select="$root"/>


<!-- generic Icon alt text -->
<xsl:variable name="alttext" select="concat($root,'text/shared/00/icon_alt.xhp')"/>

  <!-- parts of help and image urls -->

<xsl:variable name="img_url_prefix" select="concat($iconpath,'/')"/>

<xsl:variable name="urlpost" select="concat('?Language=',$lang,$am,'System=',$System,$am,'UseDB=no')"/>

<xsl:variable name="linkprefix" select="concat($target,$lang,'/')"/>

<!--<xsl:variable name="linkpostfix" select="$urlpost"/>-->
<xsl:variable name="linkpostfix" select="''"/>

<!-- images for notes, tips and warnings -->
<xsl:variable name="note_img" select="concat($iconpath,'/help/note.svg')"/>
<xsl:variable name="tip_img" select="concat($iconpath,'/help/tip.svg')"/>
<xsl:variable name="warning_img" select="concat($iconpath,'/help/warning.svg')"/>

<!-- Strings for the help UI page -->
<xsl:variable name="tmp_href_ui"><xsl:value-of select="concat($urlpre,'text/shared/help/browserhelp.xhp')"/></xsl:variable>
<xsl:variable name="tmp_doc_ui" select="document($tmp_href_ui)"/>
<xsl:variable name ="ui_copyclip"><xsl:apply-templates select="$tmp_doc_ui//variable[@id='copyclip']"/></xsl:variable>
<!--
#############
# Templates #
#############
//-->

<!-- Create the document skeleton -->
<xsl:template match="/">
    <div id="DisplayArea" itemprop="articleBody">
        <xsl:apply-templates select="/helpdocument/body"/>
        <footer>
            <div id="DEBUG" class="debug">
                <h3 class="bug">Help content debug info:</h3>
                <p>This page is: <a href="https://opengrok.libreoffice.org/xref/help/source{$filename}" target="_blank"><xsl:value-of select="$filename"/></a></p>
                <p>Title is: <xsl:value-of select="$title"/></p>
                <p id="bm_module"></p>
                <p id="bm_system"></p>
                <p id="bm_HID"></p>
            </div>
        </footer>
    </div>
</xsl:template>

<!-- AHELP -->
<xsl:template match="ahelp">
	<xsl:if test="not(@visibility='hidden')"><span class="avis"><xsl:apply-templates /></span></xsl:if>
</xsl:template>

<!-- ALT -->
<xsl:template match="alt"/>

<!-- BOOKMARK -->
<xsl:template match="bookmark">
	<a name="{@id}"></a>
	<xsl:choose>
		<xsl:when test="starts-with(@branch,'hid')" />
		<xsl:otherwise><xsl:apply-templates /></xsl:otherwise>
	</xsl:choose>
</xsl:template>
<xsl:template match="bookmark" mode="embedded" />

<!-- BOOKMARK_VALUE -->
<xsl:template match="bookmark_value">
    <xsl:element name="meta">
        <xsl:attribute name="itemprop">keywords</xsl:attribute>
        <xsl:attribute name="content"><xsl:value-of select="translate(.,';',',')"/></xsl:attribute>
    </xsl:element>
</xsl:template>

<!-- BR -->
<xsl:template match="br"><br /></xsl:template>

<!-- CAPTION -->
<xsl:template match="caption" />

<!-- CASE -->
<xsl:template match="case"><xsl:call-template name="insertcase" /></xsl:template>
<xsl:template match="case" mode="embedded">
        <xsl:call-template name="insertcase">
            <xsl:with-param name="embedded" select="'yes'"/>
        </xsl:call-template>
</xsl:template>

<!-- CASEINLINE -->
<xsl:template match="caseinline"><xsl:call-template name="insertcase" /></xsl:template>
<xsl:template match="caseinline" mode="embedded">
	<xsl:call-template name="insertcase">
		<xsl:with-param name="embedded" select="'yes'"/>
	</xsl:call-template>
</xsl:template>

<!-- COMMENT -->
<xsl:template match="comment" />
<xsl:template match="comment" mode="embedded"/>

<!-- CREATED -->
<xsl:template match="created" />

<!-- DEFAULT -->
<xsl:template match="default"><xsl:call-template name="insertdefault" /></xsl:template>
<xsl:template match="default" mode="embedded">
	<xsl:call-template name="insertdefault">
		<xsl:with-param name="embedded" select="'yes'"/>
	</xsl:call-template>
</xsl:template>

<!-- DEFAULTINLINE -->
<xsl:template match="defaultinline"><xsl:call-template name="insertdefault" /></xsl:template>
<xsl:template match="defaultinline" mode="embedded">
	<xsl:call-template name="insertdefault">
		<xsl:with-param name="embedded" select="'yes'"/>
	</xsl:call-template>
</xsl:template>

<!-- EMBED -->
<xsl:template match="embed"><xsl:call-template name="resolveembed"/></xsl:template>
<xsl:template match="embed" mode="embedded"><xsl:call-template name="resolveembed"/></xsl:template>

<!-- EMBEDVAR -->
<xsl:template match="embedvar"><xsl:call-template name="resolveembedvar"/></xsl:template>
<xsl:template match="embedvar" mode="embedded"><xsl:call-template name="resolveembedvar"/></xsl:template>

<!-- EMPH -->
<xsl:template match="emph">
	<span class="emph"><xsl:apply-templates /></span>
</xsl:template>
<xsl:template match="emph" mode="embedded">
	<span class="emph"><xsl:apply-templates /></span>
</xsl:template>

<!-- SUB -->
<xsl:template match="sub">
	<sub><xsl:apply-templates /></sub>
</xsl:template>
<xsl:template match="sub" mode="embedded">
	<sub><xsl:apply-templates /></sub>
</xsl:template>

<!-- SUP -->
<xsl:template match="sup">
	<sup><xsl:apply-templates /></sup>
</xsl:template>
<xsl:template match="sup" mode="embedded">
	<sup><xsl:apply-templates /></sup>
</xsl:template>

<!-- FILENAME -->
<xsl:template match="filename"/>

<!-- HISTORY -->
<xsl:template match="history" />

<!-- IMAGE -->
<xsl:template match="image"><xsl:call-template name="insertimage"/></xsl:template>
<xsl:template match="image" mode="embedded"><xsl:call-template name="insertimage"/></xsl:template>

<!-- ITEM -->
<xsl:template match="item">
    <span class="{@type}">
<!-- Insert tooltip only to input classes and only if the content is longer than 3 characters -->
        <xsl:if test="@type='input' and string-length(.)>3">
            <xsl:attribute name="data-tooltip">
                <xsl:value-of select="$ui_copyclip"/>
            </xsl:attribute>
        </xsl:if>
        <xsl:apply-templates />
    </span>
</xsl:template>
<xsl:template match="item" mode="embedded">
    <span class="{@type}">
        <xsl:if test="@type='input' and string-length(.)>3">
            <xsl:attribute name="data-tooltip">
                <xsl:value-of select="$ui_copyclip"/>
            </xsl:attribute>
        </xsl:if>
        <xsl:apply-templates />
    </span>
</xsl:template>

<!-- LINK -->
<xsl:template match="link">
    <xsl:choose> <!-- don't insert the heading link to itself -->
        <xsl:when test="(concat('/',@href) = /helpdocument/meta/topic/filename) or (@href = /helpdocument/meta/topic/filename)">
            <xsl:apply-templates />
        </xsl:when>
        <xsl:when test="contains(child::embedvar/@href,'/00/00000004.xhp#wie')"> <!-- special treatment of howtoget links -->
            <xsl:call-template name="insert_howtoget">
                <xsl:with-param name="linkhref" select="@href"/>
            </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
            <xsl:call-template name="createlink" />
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>
<xsl:template match="link" mode="embedded">
	<xsl:call-template name="createlink"/>
</xsl:template>

<!-- LIST -->
<xsl:template match="list">
    <xsl:choose>
        <xsl:when test="@type='ordered'">
            <ol>
                <xsl:if test="@startwith">
                    <xsl:attribute name="start"><xsl:value-of select="@startwith"/></xsl:attribute>
                </xsl:if>
                <xsl:apply-templates />
            </ol>
        </xsl:when>
        <xsl:otherwise>
            <ul><xsl:apply-templates /></ul>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template match="list" mode="embedded">
    <xsl:choose>
        <xsl:when test="@type='ordered'">
            <ol>
                <xsl:if test="@startwith">
                    <xsl:attribute name="start"><xsl:value-of select="@startwith"/></xsl:attribute>
                </xsl:if>
                <xsl:apply-templates mode="embedded"/>
            </ol>
        </xsl:when>
        <xsl:otherwise>
            <ul><xsl:apply-templates mode="embedded"/></ul>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- LISTITEM -->
<xsl:template match="listitem">
    <li><xsl:apply-templates /></li>
</xsl:template>

<xsl:template match="listitem" mode="embedded">
    <li><xsl:apply-templates mode="embedded"/></li>
</xsl:template>

<!-- META, SEE HEADER -->
<xsl:template match="meta" />

<!-- OBJECT -->
<xsl:template match="object">
	    <xsl:call-template name="insertobject"/>
</xsl:template>
<xsl:template match="object" mode="embedded">
	    <xsl:call-template name="insertobject"/>
</xsl:template>

<!-- PARAGRAPH -->
<xsl:template match="paragraph">
    <xsl:choose>

        <xsl:when test="@role='heading'">
            <xsl:call-template name="insertheading">
                <xsl:with-param name="level" select="@level"/>
            </xsl:call-template>
        </xsl:when>

        <xsl:when test="@role='note' or @role='tip' or @role='warning'">
            <xsl:call-template name="insertnote">
                <xsl:with-param name="type" select="@role" />
            </xsl:call-template>
        </xsl:when>

        <xsl:when test="contains(descendant::embedvar/@href,'/00/00000004.xhp#wie')"> <!-- special treatment of howtoget links -->
            <xsl:apply-templates />
        </xsl:when>

        <xsl:when test="@role='bascode' or @role='pycode'">
            <xsl:value-of select="." />
        </xsl:when>

        <xsl:when test="@role='smathcode'">
            <p id="{@id}" class="smathcode"><span class="input" data-tooltip="{$ui_copyclip}"><xsl:apply-templates /></span></p>
        </xsl:when>

        <xsl:when test="@role='logocode'">
            <xsl:call-template name="insertlogocode" />
        </xsl:when>

        <xsl:otherwise>
            <xsl:call-template name="insertpara" />
        </xsl:otherwise>

    </xsl:choose>
</xsl:template>

<xsl:template match="paragraph" mode="embedded">
    <xsl:choose>
        <xsl:when test="@role='heading'">	<!-- increase the level of headings that are embedded -->
            <xsl:variable name="newlevel">
                <xsl:choose>
                    <xsl:when test="@level='1'"><xsl:value-of select="'2'"/></xsl:when>
                    <xsl:otherwise><xsl:value-of select="@level"/></xsl:otherwise>
                </xsl:choose>
            </xsl:variable>

            <xsl:call-template name="insertheading">
                <xsl:with-param name="level" select="$newlevel"/>
                <xsl:with-param name="embedded" select="'yes'"/>
            </xsl:call-template>
        </xsl:when>

        <xsl:when test="@role='note' or @role='tip' or @role='warning'">
            <xsl:call-template name="insertnote">
                <xsl:with-param name="type" select="@role" />
            </xsl:call-template>
        </xsl:when>

        <xsl:when test="contains(descendant::embedvar/@href,'/00/00000004.xhp#wie')"> <!-- special treatment of howtoget links -->
            <xsl:apply-templates />
        </xsl:when>

        <xsl:when test="@role='bascode' or @role='pycode'">
            <xsl:value-of select="." />
        </xsl:when>

        <xsl:when test="@role='smathcode'">
            <p id="{@id}" class="smathcode"><span class="input" data-tooltip="{$ui_copyclip}"><xsl:apply-templates /></span></p>
        </xsl:when>

        <xsl:otherwise>
            <xsl:call-template name="insertpara" />
        </xsl:otherwise>

    </xsl:choose>
</xsl:template>

<!-- SECTION -->
<xsl:template match="section">
    <a name="{@id}"></a>
    <xsl:choose>
        <xsl:when test="@id='relatedtopics'">
            <div class="relatedtopics">
                <!--<xsl:variable name="href"><xsl:value-of select="concat($urlpre,'text/shared/00/00000004.xhp',$urlpost)"/></xsl:variable>-->
                <xsl:variable name="href"><xsl:value-of select="concat($urlpre,'text/shared/00/00000004.xhp')"/></xsl:variable>
                <xsl:variable name="anchor"><xsl:value-of select="'related'"/></xsl:variable>
                <xsl:variable name="doc" select="document($href)"/>
                <p class="related" itemprop="mentions">
                    <xsl:apply-templates select="$doc//variable[@id=$anchor]"/>
                </p>
                <div class="relatedbody" itemprop="mentions">
                    <xsl:apply-templates />
                </div>
            </div>
        </xsl:when>
        <xsl:when test="@id='howtoget'">
            <xsl:call-template name="insert_howtoget" />
        </xsl:when>
        <xsl:otherwise>
            <xsl:apply-templates/>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- SECTION -->
<xsl:template match="section" mode="embedded">
    <a name="{@id}"></a>
    <xsl:apply-templates mode="embedded"/>
</xsl:template>

<!-- SORT -->
<xsl:template match="sort" >
    <xsl:variable name="order1">
        <xsl:choose>
            <xsl:when test="string-length(@order) = 0"><xsl:value-of  select="'ascending'"/></xsl:when>
            <xsl:otherwise><xsl:value-of select="concat(@order,'ending')"/></xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:apply-templates><xsl:sort order="{$order1}" select="descendant::paragraph"/></xsl:apply-templates>
</xsl:template>
<xsl:template match="sort" mode="embedded">
    <xsl:variable name="order1">
        <xsl:choose>
            <xsl:when test="string-length(@order) = 0"><xsl:value-of  select="'ascending'"/></xsl:when>
            <xsl:otherwise><xsl:value-of select="concat(@order,'ending')"/></xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:apply-templates><xsl:sort order="{$order1}" select="descendant::paragraph"/></xsl:apply-templates>
</xsl:template>

<!-- SWITCH -->
<xsl:template match="switch">
    <xsl:choose>
        <xsl:when test ="@select = 'sys'">
            <xsl:variable name="idsw" select="concat('swlnsys',generate-id())"/>
            <span id="{$idsw}" class="switch">
                <xsl:apply-templates />
            </span>
        </xsl:when>
        <xsl:when test ="@select = 'appl'">
            <xsl:variable name="idsw" select="concat('swlnappl',generate-id())"/>
            <span id="{$idsw}" class="switch">
                <xsl:apply-templates />
            </span>
        </xsl:when>
        <xsl:otherwise>
            <p class="debug">Unsupported switch condition.</p>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>
<xsl:template match="switch" mode="embedded">
    <xsl:choose>
        <xsl:when test ="@select = 'sys'">
            <xsl:variable name="idsw" select="concat('swlnsys',generate-id())"/>
            <span id="{$idsw}" class="switch">
                <xsl:apply-templates mode="embedded"/>
            </span>
        </xsl:when>
        <xsl:when test ="@select = 'appl'">
            <xsl:variable name="idsw" select="concat('swlnappl',generate-id())"/>
            <span id="{$idsw}" class="switch">
                <xsl:apply-templates mode="embedded"/>
            </span>
        </xsl:when>
        <xsl:otherwise>
            <p class="debug">Unsupported switch condition.</p>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- SWITCHINLINE -->
<xsl:template match="switchinline">
    <xsl:choose>
        <xsl:when test ="@select = 'sys'">
            <xsl:variable name="idsw" select="concat('swlnsys',generate-id())"/>
            <span id="{$idsw}" class="switchinline">
                <xsl:apply-templates />
            </span>
        </xsl:when>
        <xsl:when test ="@select = 'appl'">
            <xsl:variable name="idsw" select="concat('swlnappl',generate-id())"/>
            <span id="{$idsw}" class="switchinline">
                <xsl:apply-templates />
            </span>
        </xsl:when>
        <xsl:otherwise>
            <p class="debug">Unsupported switch condition.</p>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>
<xsl:template match="switchinline" mode="embedded">
    <xsl:choose>
        <xsl:when test ="@select = 'sys'">
            <xsl:variable name="idsw" select="concat('swlnsys',generate-id())"/>
            <span id="{$idsw}" class="switchinline">
                <xsl:apply-templates mode="embedded"/>
            </span>
        </xsl:when>
        <xsl:when test ="@select = 'appl'">
            <xsl:variable name="idsw" select="concat('swlnappl',generate-id())"/>
            <span id="{$idsw}" class="switchinline">
                <xsl:apply-templates mode="embedded"/>
            </span>
        </xsl:when>
        <xsl:otherwise>
            <p class="debug">Unsupported switch condition.</p>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- TABLE -->
<xsl:template match="table"><xsl:call-template name="inserttable"/></xsl:template>
<xsl:template match="table" mode="embedded"><xsl:call-template name="inserttable"/></xsl:template>

<!-- TABLECELL -->
<xsl:template match="tablecell">
    <xsl:choose>
        <xsl:when test="paragraph[@role='tablehead']">
            <td rowspan="{@rowspan}" colspan="{@colspan}" class='tableheadcell'><xsl:apply-templates /></td>
        </xsl:when>
        <xsl:otherwise>
            <td rowspan="{@rowspan}" colspan="{@colspan}"><xsl:apply-templates /></td>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>
<xsl:template match="tablecell" mode="onecell"><xsl:apply-templates/></xsl:template>
<xsl:template match="tablecell" mode="icontable"><div class="iconcell"><xsl:apply-templates/></div></xsl:template>
<xsl:template match="tablecell" mode="embedded">
    <xsl:choose>
        <xsl:when test="paragraph[@role='tablehead']">
            <td rowspan="{@rowspan}" colspan="{@colspan}" class='tableheadcell'><xsl:apply-templates mode="embedded"/></td>
        </xsl:when>
        <xsl:otherwise>
            <td rowspan="{@rowspan}" colspan="{@colspan}"><xsl:apply-templates mode="embedded"/></td>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- TABLEROW -->
<xsl:template match="tablerow"><tr><xsl:apply-templates /></tr></xsl:template>
<xsl:template match="tablerow" mode="onecell"><xsl:apply-templates mode="onecell"/></xsl:template>
<xsl:template match="tablerow" mode="icontable"><div class="icontable"><xsl:apply-templates mode="icontable"/></div></xsl:template>
<xsl:template match="tablerow" mode="embedded"><tr><xsl:apply-templates mode="embedded"/></tr></xsl:template>

<!-- TITLE -->
<xsl:template match="title"/>

<!-- TOPIC -->
<xsl:template match="topic"/>

<!-- VARIABLE -->
<xsl:template match="variable"><a name="{@id}"></a><xsl:apply-templates /></xsl:template>
<xsl:template match="variable" mode="embedded"><a name="{@id}"></a><xsl:apply-templates mode="embedded"/></xsl:template>

<xsl:template match="text()">
    <xsl:call-template name="brand">
        <xsl:with-param name="string"><xsl:value-of select="."/></xsl:with-param>
    </xsl:call-template>
</xsl:template>

<xsl:template match="text()" mode="embedded">
    <xsl:call-template name="brand">
        <xsl:with-param name="string"><xsl:value-of select="."/></xsl:with-param>
    </xsl:call-template>
</xsl:template>

<!-- XHP extensions (2018) -->
<!-- H1-H6 -->
<xsl:template match="h1 | h2 | h3 | h4 | h5 | h6">
    <xsl:element name="{local-name()}">
        <xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute><xsl:apply-templates />
    </xsl:element>
</xsl:template>
<xsl:template match="h1 | h2 | h3 | h4 | h5 | h6" mode="embedded">
    <xsl:element name="{concat('h',substring-after(local-name(),'h') + 1)}">
        <xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute><xsl:apply-templates mode="embedded"/>
    </xsl:element>
</xsl:template>

<!-- INPUT -->
<xsl:template match="input">
    <span class="input" data-tooltip="{$ui_copyclip}"><xsl:apply-templates /></span>
</xsl:template>
<xsl:template match="input" mode="embedded">
    <span class="input" data-tooltip="{$ui_copyclip}"><xsl:apply-templates mode="embedded"/></span>
</xsl:template>

<!--MENUITEM, KEYCODE, LITERAL, WIDGET-->
<xsl:template match="menuitem | keycode | literal | widget">
    <span class="{local-name()}"><xsl:apply-templates /></span>
</xsl:template>
<xsl:template match="menuitem | input | keycode | literal" mode="embedded">
    <span class="{local-name()}"><xsl:apply-templates mode="embedded"/></span>
</xsl:template>

<!--NOTE TIP AND WARNING-->
<xsl:template match="tip | note | warning">
    <xsl:variable name="imgsrc">
        <xsl:choose>
            <xsl:when test="local-name()='note'"><xsl:value-of select="$note_img"/></xsl:when>
            <xsl:when test="local-name()='tip'"><xsl:value-of select="$tip_img"/></xsl:when>
            <xsl:when test="local-name()='warning'"><xsl:value-of select="$warning_img"/></xsl:when>
        </xsl:choose>
    </xsl:variable>
    <div class="{local-name()}">
        <div class="noteicon"><img src="{$imgsrc}" alt="{local-name()}" title="{local-name()}"/></div>
        <div class="notetext"><p id="{@id}"><xsl:apply-templates /></p></div>
    </div>
    <br/>
</xsl:template>
<xsl:template match="tip | note | warning" mode="embedded">
    <xsl:variable name="imgsrc">
        <xsl:choose>
            <xsl:when test="local-name()='note'"><xsl:value-of select="$note_img"/></xsl:when>
            <xsl:when test="local-name()='tip'"><xsl:value-of select="$tip_img"/></xsl:when>
            <xsl:when test="local-name()='warning'"><xsl:value-of select="$warning_img"/></xsl:when>
        </xsl:choose>
    </xsl:variable>
    <div class="{local-name()}">
        <div class="noteicon"><img src="{$imgsrc}" alt="{local-name()}" title="{local-name()}"/></div>
        <div class="notetext"><p id="{@id}"><xsl:apply-templates mode="embedded"/></p></div>
    </div>
    <br/>
</xsl:template>

<!-- In case of missing help files -->
<xsl:template match="help-id-missing"><xsl:value-of select="$Id"/></xsl:template>

<!--
###################
# NAMED TEMPLATES #
###################
//-->

<!-- Branding -->
<xsl:template name="brand" >
    <xsl:param name="string"/>

    <xsl:choose>

        <xsl:when test="contains($string,$brand1)">
            <xsl:variable name="newstr">
                <xsl:value-of select="substring-before($string,$brand1)"/>
                <xsl:value-of select="$productname"/>
                <xsl:value-of select="substring-after($string,$brand1)"/>
            </xsl:variable>
            <xsl:call-template name="brand">
                <xsl:with-param name="string" select="$newstr"/>
            </xsl:call-template>
        </xsl:when>

        <xsl:when test="contains($string,$brand2)">
            <xsl:variable name="newstr">
                <xsl:value-of select="substring-before($string,$brand2)"/>
                <xsl:value-of select="$pversion"/>
                <xsl:value-of select="substring-after($string,$brand2)"/>
            </xsl:variable>
            <xsl:call-template name="brand">
                <xsl:with-param name="string" select="$newstr"/>
            </xsl:call-template>
        </xsl:when>

        <xsl:when test="contains($string,$brand3)">
            <xsl:variable name="newstr">
                <xsl:value-of select="substring-before($string,$brand3)"/>
                <xsl:value-of select="$productname"/>
                <xsl:value-of select="substring-after($string,$brand3)"/>
            </xsl:variable>
            <xsl:call-template name="brand">
                <xsl:with-param name="string" select="$newstr"/>
            </xsl:call-template>
        </xsl:when>

        <xsl:when test="contains($string,$brand4)">
            <xsl:variable name="newstr">
                <xsl:value-of select="substring-before($string,$brand4)"/>
                <xsl:value-of select="$pversion"/>
                <xsl:value-of select="substring-after($string,$brand4)"/>
            </xsl:variable>
            <xsl:call-template name="brand">
                <xsl:with-param name="string" select="$newstr"/>
            </xsl:call-template>
        </xsl:when>

        <xsl:otherwise>
            <xsl:value-of select="$string"/>
        </xsl:otherwise>
    </xsl:choose>

</xsl:template>

<!-- Insert Paragraph -->
<xsl:template name="insertpara">
    <xsl:variable name="role">
        <xsl:choose>
            <xsl:when test="ancestor::table">
                <xsl:value-of select="concat(@role,'intable')"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="@role"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <p id="{@id}" class="{$role}"><xsl:apply-templates /></p>
</xsl:template>

<xsl:template match="bascode">
    <div class="bascode" itemscope="true" itemtype="http://schema.org/SoftwareSourceCode" itemprop="codeSampleType" content="snippet"><pre><code class="language-visual-basic line-numbers"><xsl:apply-templates /></code></pre></div>
</xsl:template>
<xsl:template match="bascode" mode="embedded">
    <div class="bascode" itemscope="true" itemtype="http://schema.org/SoftwareSourceCode" itemprop="codeSampleType" content="snippet"><pre><code class="language-visual-basic line-numbers"><xsl:apply-templates mode="embedded" /></code></pre></div>
</xsl:template>

<xsl:template match="pycode">
    <div class="pycode" itemscope="true" itemtype="http://schema.org/SoftwareSourceCode" itemprop="codeSampleType" content="snippet"><pre><code class="language-python line-numbers"><xsl:apply-templates /></code></pre></div>
</xsl:template>
<xsl:template match="pycode" mode="embedded">
    <div class="pycode" itemscope="true" itemtype="http://schema.org/SoftwareSourceCode" itemprop="codeSampleType" content="snippet"><pre><code class="language-python line-numbers"><xsl:apply-templates mode="embedded" /></code></pre></div>
</xsl:template>

<!-- Insert Logo code snippet  -->
<xsl:template name="insertlogocode">
    <pre><xsl:apply-templates /></pre>
</xsl:template>

<!-- Insert "How to get Link" -->
<xsl:template name="insert_howtoget">
    <xsl:param name="linkhref" />
    <xsl:variable name="archive" select="'shared'"/>
    <xsl:variable name="tmp_href"><xsl:value-of select="concat($urlpre,'text/shared/00/00000004.xhp')"/></xsl:variable>
    <xsl:variable name="tmp_doc" select="document($tmp_href)"/>
    <div class="howtoget">
        <div>
            <p class="howtogetheader"><xsl:apply-templates select="$tmp_doc//variable[@id='wie']"/></p>
        </div>
        <div class="howtogetbody">
            <xsl:choose>
                <xsl:when test="$linkhref = ''"> <!-- new style -->
                    <xsl:apply-templates/>
                </xsl:when>
                <xsl:otherwise> <!-- old style -->
                    <xsl:variable name="href"><xsl:value-of select="concat($urlpre,substring-before($linkhref,'#'))"/></xsl:variable>
                    <xsl:variable name="anc"><xsl:value-of select="substring-after($linkhref,'#')"/></xsl:variable>
                    <xsl:variable name="docum" select="document($href)"/>
                    <xsl:call-template name="insertembed">
                        <xsl:with-param name="doc" select="$docum" />
                        <xsl:with-param name="anchor" select="$anc" />
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
        </div>
    </div>
    <br/>
</xsl:template>

<!-- Create a link -->
<!-- Modified for editor -->
<xsl:template name="createlink">
     <span style="color: blue;" data-tooltip="{@href}"><xsl:apply-templates /></span>
</xsl:template>

<!-- Insert Note, Warning, or Tip -->
<xsl:template name="insertnote">
    <xsl:param name="type" /> <!-- note, tip, or warning -->
    <xsl:variable name="imgsrc">
        <xsl:choose>
            <xsl:when test="$type='note'"><xsl:value-of select="$note_img"/></xsl:when>
            <xsl:when test="$type='tip'"><xsl:value-of select="$tip_img"/></xsl:when>
            <xsl:when test="$type='warning'"><xsl:value-of select="$warning_img"/></xsl:when>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="alt">
        <xsl:variable name="href"><xsl:value-of select="$alttext"/></xsl:variable>
        <xsl:variable name="anchor"><xsl:value-of select="concat('alt_',$type)"/></xsl:variable>
        <xsl:variable name="doc" select="document($href)"/>
        <xsl:apply-templates select="$doc//variable[@id=$anchor]" mode="embedded"/>
    </xsl:variable>
    <div class="{$type}">
        <div class="noteicon"><img src="{$imgsrc}" alt="{$alt}" title="{$alt}"/></div>
        <div class="notetext"><p><xsl:apply-templates /></p></div>
    </div>
    <br/>
</xsl:template>

<!-- Insert a heading -->
<xsl:template name="insertheading">
        <xsl:param name="level" />
        <xsl:param name="embedded" />
        <xsl:element name="{concat('h',$level)}">
                <xsl:if test="$level = '1' or $level='2'">
                        <xsl:attribute name="itemprop"><xsl:text>articleSection</xsl:text></xsl:attribute>
                </xsl:if>
                <xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute>
                <xsl:choose>
                    <xsl:when test="$embedded = 'yes'">
                        <xsl:apply-templates mode="embedded"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:apply-templates />
                    </xsl:otherwise>
                </xsl:choose>
        </xsl:element>
</xsl:template>

<!-- Evaluate a case or caseinline switch -->
<xsl:template name="insertcase">
    <xsl:param name="embedded" />
    <xsl:variable name="auxID" select="concat(@select,generate-id())"/>
    <xsl:choose>
        <xsl:when test="$embedded = 'yes'">
            <span hidden="true" id="{$auxID}"><xsl:apply-templates mode="embedded"/></span>
        </xsl:when>
        <xsl:otherwise>
            <span hidden="true" id="{$auxID}"><xsl:apply-templates/></span>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- Evaluate a default or defaultinline switch -->
<xsl:template name="insertdefault">
    <xsl:param name="embedded" />
    <xsl:choose>
        <xsl:when test="parent::switch[@select='sys'] or parent::switchinline[@select='sys']">
            <xsl:variable name="auxID" select="concat('default',generate-id())"/>
            <xsl:choose>
                <xsl:when test="$embedded = 'yes'">
                    <span hidden="true" id="{$auxID}"><xsl:apply-templates mode="embedded"/></span>
                </xsl:when>
                <xsl:otherwise>
                    <span hidden="true" id="{$auxID}"><xsl:apply-templates /></span>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:when>
        <xsl:when test="parent::switch[@select='appl'] or parent::switchinline[@select='appl']">
            <xsl:variable name="auxID" select="concat('default',generate-id())"/>
            <xsl:choose>
                <xsl:when test="$embedded = 'yes'">
                    <span hidden="true" id="{$auxID}"><xsl:apply-templates mode="embedded"/></span>
                </xsl:when>
                <xsl:otherwise>
                    <span hidden="true" id="{$auxID}"><xsl:apply-templates /></span>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:when>
        <xsl:when test="parent::switch[@select='distrib'] or parent::switchinline[@select='distrib']"><!--TODO: fix this distrib case if relevant-->
            <xsl:if test="not(../child::case[@select=$distrib]) and not(../child::caseinline[@select=$distrib])">
                <xsl:choose>
                    <xsl:when test="$embedded = 'yes'">
                        <span hidden="true" itemprop="distrib" value="DEFDIST"><xsl:apply-templates mode="embedded"/></span>
                    </xsl:when>
                    <xsl:otherwise>
                        <span hidden="true" itemprop="distrib" value="DEFDIST"><xsl:apply-templates /></span>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:if>
        </xsl:when>
    </xsl:choose>
</xsl:template>

<!-- evaluate embeds -->
<xsl:template name="insertembed">
    <xsl:param name="doc" />
    <xsl:param name="anchor" />
    <!-- different embed targets (also falsely used embed instead embedvar) -->
    <xsl:choose>
        <xsl:when test="$doc//section[@id=$anchor]"> <!-- first test for a section of that name -->
            <xsl:apply-templates select="$doc//section[@id=$anchor]" mode="embedded"/>
        </xsl:when>
        <xsl:when test="$doc//paragraph[@id=$anchor]"> <!-- then test for a para of that name -->
            <p class="embedded">
                <xsl:apply-templates select="$doc//paragraph[@id=$anchor]" mode="embedded"/>
            </p>
        </xsl:when>
        <xsl:when test="$doc//variable[@id=$anchor]"> <!-- then test for a variable of that name -->
            <p class="embedded">
                <xsl:apply-templates select="$doc//variable[@id=$anchor]" mode="embedded"/>
            </p>
        </xsl:when>
        <xsl:otherwise> <!-- then give up -->
            <p class="bug">D'oh! You found a bug (<xsl:value-of select="@href"/> not found).</p>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- Insert an image -->
<xsl:template name="insertimage">
    <xsl:variable name="src2">
        <xsl:choose>
            <xsl:when test="starts-with(@src,'media/screenshots/')">
                <xsl:choose>
                    <xsl:when test="not(@localize=false) and not($lang='en-US')">
                        <xsl:variable name="tmp0" select="substring-before(@src, '/ui/')"/>
                        <xsl:variable name="tmp1" select="substring-after(@src, '/ui/')"/>
                        <xsl:variable name="tmp2" select="substring-before($tmp1,'/')"/>
                        <xsl:variable name="tmp3" select="substring-after($tmp1,'/')"/>
                        <xsl:value-of select="concat($source,'/',$tmp0,'/ui/', $tmp2, '/',$lang,'/',$tmp3)"/>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="concat($source,'source/',@src)"/>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <!-- generic media file -->
            <xsl:when test="starts-with(@src,'media/')">
                <xsl:value-of select="concat($source,'/',@src)"/>
            </xsl:when>
            <!-- handle icons -->
            <xsl:when test="not(starts-with(@src,'media/'))">
                <xsl:variable name="linklist">
                    <xsl:call-template name="linktxt"><xsl:with-param name="src1" select="@src"/></xsl:call-template>
                </xsl:variable>
                <xsl:variable name="aux00">
                    <xsl:choose>
                        <xsl:when test="substring($linklist,string-length($linklist) - 3, 4)='.png'">
                            <xsl:value-of select="concat(substring-before($linklist,'.png'),'.svg')"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="$linklist"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:value-of select="concat($img_url_prefix,$aux00)"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="concat($target,@src)"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="imagestyle">
        <xsl:choose>
            <xsl:when test="starts-with(@src,'media/screenshots/')">
                <xsl:value-of select="'screenshot'"/>
            </xsl:when>
            <xsl:when test="starts-with(@src,'media/')">
                <xsl:value-of select="'genericimage'"/>
            </xsl:when>
            <xsl:when test="not(starts-with(@src,'media/'))">
                <xsl:value-of select="'iconimage'"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="'genericimage'"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="alt"><xsl:value-of select="./alt"/></xsl:variable>
    <xsl:variable name="width">
        <xsl:if test="string-length(@width)!=0">
            <xsl:call-template name="convert2px"><xsl:with-param name="value" select="@width"/></xsl:call-template>
        </xsl:if>
    </xsl:variable>
    <xsl:variable name="height">
        <xsl:if test="string-length(@height)!=0">
            <xsl:call-template name="convert2px"><xsl:with-param name="value" select="@height"/></xsl:call-template>
        </xsl:if>
    </xsl:variable>
    <p class="debugembed">Image href: <xsl:value-of select="$src2"/></p>
    <img src="{$src2}" class="{$imagestyle}" alt="{$alt}" title="{$alt}" style="{concat('width:',$width,';height:',$height)}"/>
</xsl:template>

<!-- Insert an object -->
<xsl:template name="insertobject">
    <xsl:variable name="tmp_href"><xsl:value-of select="concat($urlpre,'text/shared/00/00000004.xhp')"/></xsl:variable>
    <xsl:variable name="tmp_doc" select="document($tmp_href)"/>
    <xsl:variable name="data">
        <xsl:value-of select="concat($img_url_prefix,@data)"/>
    </xsl:variable>
    <xsl:variable name="type"><xsl:value-of select="@type"/></xsl:variable>
    <xsl:variable name="width">
        <xsl:call-template name="convert2px"><xsl:with-param name="value" select="@width"/></xsl:call-template>
    </xsl:variable>
    <xsl:variable name="height">
        <xsl:call-template name="convert2px"><xsl:with-param name="value" select="@height"/></xsl:call-template>
    </xsl:variable>
    <xsl:variable name="auxID" select="concat('obj',generate-id())"/>
    <xsl:choose>
        <xsl:when test="starts-with(@type,'video/youtube')">
                <div id="mediadiv">
                    <iframe id="{@id}" src="{@data}" width="{$width}" height="{$height}" frameborder="0" allowfullscreen="true"></iframe>
                </div>
        </xsl:when>
        <xsl:when test="not(starts-with(@type,'video/youtube')) and starts-with(@type,'video')">
            <div id="mediadiv">
                <video src="{$data}" type="{@type}" width="{$width}" height="{$height}" controls="'1'"></video>
            </div>
        </xsl:when>
        <xsl:when test="starts-with(@type,'audio')">
            <div id="mediadiv">
                <audio src="{$data}" type="{@type}" controls="'1'"></audio>
            </div>
        </xsl:when>
        <xsl:when test="@type='application/vnd.oasis.opendocument.spreadsheet'">
            <xsl:variable name="src">
                <xsl:call-template name="addlang2path">
                    <xsl:with-param name="string" select="@data"/>
                </xsl:call-template>
            </xsl:variable>
            <div class="samplefilesection" id="{$auxID}">
            <h3><xsl:apply-templates select="$tmp_doc//variable[@id='samplefile']"/></h3>
            <a class="objectfiles" href="{concat($target,$src)}"><img src="{concat($target,'media/navigation/libo-calc.svg')}" width="25px" height="30px"></img></a>
            </div>
        </xsl:when>
        <xsl:when test="@type='application/vnd.oasis.opendocument.text'">
            <xsl:variable name="src">
                <xsl:call-template name="addlang2path">
                    <xsl:with-param name="string" select="@data"/>
                </xsl:call-template>
            </xsl:variable>
            <div class="samplefilesection" id="{$auxID}">
            <h3><xsl:apply-templates select="$tmp_doc//variable[@id='samplefile']"/></h3>
            <a class="objectfiles" href="{concat($target,$src)}"><img src="{concat($target,'media/navigation/libo-writer.svg')}" width="25px" height="30px"></img></a>
            </div>
        </xsl:when>
        <xsl:when test="@type='application/vnd.oasis.opendocument.presentation'">
            <xsl:variable name="src">
                <xsl:call-template name="addlang2path">
                    <xsl:with-param name="string" select="@data"/>
                </xsl:call-template>
            </xsl:variable>
            <div class="samplefilesection" id="{$auxID}">
            <h3><xsl:apply-templates select="$tmp_doc//variable[@id='samplefile']"/></h3>
            <a class="objectfiles" href="{concat($target,$src)}"><img src="{concat($target,'media/navigation/libo-impress.svg')}" width="25px" height="30px"></img></a>
            </div>
            </xsl:when>
        <xsl:when test="@type='application/vnd.oasis.opendocument.drawing'">
            <xsl:variable name="src">
                <xsl:call-template name="addlang2path">
                    <xsl:with-param name="string" select="@data"/>
                </xsl:call-template>
            </xsl:variable>
            <div class="samplefilesection" id="{$auxID}">
            <h3><xsl:apply-templates select="$tmp_doc//variable[@id='samplefile']"/></h3>
            <a class="objectfiles" href="{concat($target,$src)}"><img src="{concat($target,'media/navigation/libo-draw.svg')}" width="25px" height="30px"></img></a>
            </div>
        </xsl:when>
        <xsl:when test="@type='application/vnd.oasis.opendocument.formula'">
            <xsl:variable name="src">
                <xsl:call-template name="addlang2path">
                    <xsl:with-param name="string" select="@data"/>
                </xsl:call-template>
            </xsl:variable>
            <div class="samplefilesection" id="{$auxID}">
            <h3><xsl:apply-templates select="$tmp_doc//variable[@id='samplefile']"/></h3>
            <a class="objectfiles" href="{concat($target,$src)}"><img src="{concat($target,'media/navigation/libo-math.svg')}" width="25px" height="30px"></img></a>
            </div>
        </xsl:when>
        <xsl:when test="@type='application/vnd.oasis.opendocument.database'">
            <xsl:variable name="src">
                <xsl:call-template name="addlang2path">
                    <xsl:with-param name="string" select="@data"/>
                </xsl:call-template>
            </xsl:variable>
            <div class="samplefilesection" id="{$auxID}">
            <h3><xsl:apply-templates select="$tmp_doc//variable[@id='samplefile']"/></h3>
            <a class="objectfiles" href="{concat($target,$src)}"><img src="{concat($target,'media/navigation/libo-base.svg')}" width="25px" height="30px"></img></a>
            </div>
        </xsl:when>
        <xsl:otherwise>
            <object width="{$width}" height="{$height}" data="{$data}" type="{@type}"></object>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- changing measure to pixel -->
<xsl:template name="convert2px">
    <xsl:param name="value"/>
    <xsl:choose>
        <xsl:when test="contains($value, 'cm')">
            <xsl:value-of select="concat(round(number(substring-before($value, 'cm')) * $dpcm),'px')"/>
        </xsl:when>
        <xsl:when test="contains($value, 'mm')">
            <xsl:value-of select="concat(round(number(substring-before($value, 'mm')) * $dpmm),'px')"/>
        </xsl:when>
        <xsl:when test="contains($value, 'in')">
            <xsl:value-of select="concat(round(number(substring-before($value, 'in')) * $dpi),'px')"/>
        </xsl:when>
        <xsl:when test="contains($value, 'px')">
            <xsl:value-of select="$value"/>
        </xsl:when>
        <xsl:otherwise>
<!--                      <xsl:message>measure_conversion.xsl: Find no conversion for <xsl:value-of select="$value"/> to 'px'!</xsl:message> -->
            <xsl:value-of select="concat($value, 'px;')"/>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- Insert a Table -->
<xsl:template name="inserttable">
    <xsl:variable name="imgsrc">	<!-- see if we are in an image table -->
        <xsl:value-of select="tablerow/tablecell[1]/paragraph[1]/image/@src"/>
    </xsl:variable>

    <xsl:choose>
        <xsl:when test="count(descendant::tablecell)=1">
            <div class="onecell"><xsl:apply-templates mode="onecell"/></div>
        </xsl:when>

        <xsl:when test="descendant::tablecell[1]/descendant::image">
            <xsl:apply-templates mode="icontable"/>
        </xsl:when>

        <xsl:when test="@class='wide'">
            <table border="1" class="{@class}" cellpadding="0" cellspacing="0" width="100%" >
                <xsl:apply-templates />
            </table>
            <br/>
        </xsl:when>

        <xsl:when test="not(@class='')">
            <table border="1" class="{@class}" cellpadding="0" cellspacing="0" >
                <xsl:apply-templates />
            </table>
            <br/>
        </xsl:when>

        <xsl:otherwise>
            <table border="1" class="border" cellpadding="0" cellspacing="0" >
                <xsl:apply-templates />
            </table>
            <br/>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template name="resolveembed">
    <div class="embedded">
        <xsl:variable name="href"><xsl:value-of select="concat($urlpre,substring-before(@href,'#'))"/></xsl:variable>
        <xsl:variable name="anc"><xsl:value-of select="substring-after(@href,'#')"/></xsl:variable>
        <xsl:variable name="docum" select="document($href)"/>
        <p class="debugembed">Embed href: <xsl:value-of select="@href"/></p>
        <xsl:call-template name="insertembed">
            <xsl:with-param name="doc" select="$docum" />
            <xsl:with-param name="anchor" select="$anc" />
        </xsl:call-template>
    </div>
</xsl:template>

<xsl:template name="resolveembedvar">
    <xsl:if test="not(@href='text/shared/00/00000004.xhp#wie')"> <!-- special treatment if howtoget links -->
        <xsl:variable name="archive"><xsl:value-of select="concat(substring-before(substring-after(@href,'text/'),'/'),'/')"/></xsl:variable>
        <xsl:variable name="href"><xsl:value-of select="concat($urlpre,substring-before(@href,'#'))"/></xsl:variable>
        <xsl:variable name="anchor"><xsl:value-of select="substring-after(@href,'#')"/></xsl:variable>
        <xsl:variable name="doc" select="document($href)"/>
        <xsl:choose>
            <xsl:when test="$doc//variable[@id=$anchor]"> <!-- test for a variable of that name -->
                <xsl:apply-templates select="$doc//variable[@id=$anchor]" mode="embedded"/>
            </xsl:when>
            <xsl:otherwise> <!-- or give up -->
                <span class="bug">[<xsl:value-of select="@href"/> not found].</span>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:if>
</xsl:template>

<!-- Apply -->
<xsl:template name="apply">
    <xsl:param name="embedded" />
    <xsl:choose>
        <xsl:when test="$embedded = 'yes'">
            <xsl:apply-templates mode="embedded"/>
        </xsl:when>
        <xsl:otherwise>
            <xsl:apply-templates />
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template name="filehtml">
   <xsl:param name="file"/>
   <xsl:value-of select="concat(substring-before($file,'.xhp'),'.html')"/>
</xsl:template>

<!-- recursive named template -->
<xsl:template name="tokenize">
    <xsl:param name="str" />
    <xsl:param name="result" select="''" />
    <xsl:choose>
        <xsl:when test="substring-after($str,'/')">
            <xsl:call-template name="tokenize">
                <xsl:with-param name="str" select="substring-after($str,'/')" />
                <xsl:with-param name="result" select="concat($result,'../')" />
            </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
                <xsl:value-of select="$result" />
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>
<!--Add language to path for file -->
<xsl:template name="addlang2path">
    <xsl:param name="string"/>
    <xsl:choose>
        <xsl:when test="not($lang='en-US')">
            <xsl:variable name="tmpfn">
                <xsl:call-template name="substring-after-last">
                    <xsl:with-param name="string" select="$string"/>
                    <xsl:with-param name="char" select="'/'"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:value-of select="concat(substring-before($string, $tmpfn),$lang,'/',$tmpfn)"/>
        </xsl:when>
        <xsl:otherwise>
            <xsl:value-of select="$string"/>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template name="substring-after-last">
    <xsl:param name="string"/>
    <xsl:param name="char"/>
    <xsl:choose>
        <xsl:when test="contains($string, $char)">
            <xsl:call-template name="substring-after-last">
                <xsl:with-param name="string" select="substring-after($string, $char)"/>
                <xsl:with-param name="char" select="$char"/>
            </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
            <xsl:value-of select="$string"/>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>
</xsl:stylesheet>
