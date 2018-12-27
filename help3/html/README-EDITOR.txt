This file explains how to install the XHP online editor and give some hints

To clone the editor
-------------------
git clone https://gerrit.libreoffice.org/dev-tools dev-tools

The editor is in folder

dev-tools/help3/html/

To clone the HelpContents2 submodule
-------------------------------------
git clone https://gerrit.libreoffice.org/help helpcontent2

all help files are in helpcontent2/ folder

Other services
--------------
A) A working  apache or nginx webserver at http://localhost
b) PHP support for apache

Setup
-----

1) change to the editor folder

cd <location>/dev-tools/help3/html

2) Set a symbolic link to helpcontent2

ln -s <location>/helcontent2 hc2

this will make a symbolic link between hc2 -> <location>/helpcontent2

3) Set a symbolic link to the core repo

ln -s <location>/core core

This will make a symbolic link between core -> <location>/core
Note: the core/ link is needed to get the colibre_svg/ icon theme

4) Web server

As root/admin execute a symbolic link

cd /var/www/html
ln -s <location>/dev-tools/help3/html ed

this will create a symbolic link /var/www/html/ed -> <location>/dev-tools/help3/html

Running the editor
------------------

point the browser to

http://localhost/ed/index.php

Open XHP file
-------------

type 'source/text/shared/main0108.xhp' and click Open file to load the file in the editor

Render the edited XHP
--------------------

click on 'Render file' to see the XHP page rendered on the right pane.
