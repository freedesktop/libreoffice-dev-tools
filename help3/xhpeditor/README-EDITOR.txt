This file explains how to install the XHP online editor and give some hints

Summary
-------
a) Unzip (or clone) the editor in a webserver path
b) clone the Help repository in your user area
c) clone the LibreOffice repository 
   - alternatively, copy the icon-theme/ folder 
d) set the configuration in config.php
e) open index.php in the webserver

To clone the editor
-------------------
git clone https://git.libreoffice.org/dev-tools dev-tools

The editor is in folder

dev-tools/help3/xhpeditor/

To clone the HelpContents2 submodule
-------------------------------------
git clone https://git.libreoffice.org/help helpcontent2

all help files are in helpcontent2/ folder

Other services
--------------
A) A working  apache or nginx webserver at http://localhost
b) PHP support for apache/nginx, include support for XSLT and dependencies

Setup
-----

*) change to the editor folder

cd <location>/dev-tools/help3/xhpeditor

*) Set a symbolic link to the core repo

ln -s <location>/core core

This will make a symbolic link between core -> <location>/core
Note: the core/ link is needed to get the colibre_svg/ icon theme

*) set a symbolic link of the DTD

ls -s helpcontent2/helpers/xmlhelp.dtd .

*) Web server

As root/admin execute a symbolic link, assuming /var/www/html is your webroot
cd /var/www/html
ln -s <location>/dev-tools/help3/xhpeditor .

this will create a symbolic link /var/www/html/xhpeditor -> <location>/dev-tools/help3/xhpeditor

Running the editor
------------------
Point the browser to

http://localhost/xhpeditor/index.php

Open XHP file
-------------
Click Open to pick a local Help file. You should have cloned the helpcontent2/ repo

Save XHP file
------------
Click Save to save the local file. Note that you must navigate to the right folder because
the suggested file name does not have the full path.

Check XHP
--------
Click to check the xml with respect to its DTD. Used to verify XHP consistency. DTD viloations are
reported in the rendering area.

Render the edited XHP
---------------------
click on 'Render file' to see the XHP page rendered on the right pane.

NOTE: 
- Links are killed to prevent navigating to invalid pages. The link color is kept blue.
- Embeds are surrounded with a light grey box and have their link in magenta
- Images and icons are preceded by their URL in magenta
- Select the 'System' and 'Module' radio buttons  to exercise the <switch*> tags



