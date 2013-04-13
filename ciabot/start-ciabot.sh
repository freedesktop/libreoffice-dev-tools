#! /bin/bash

cd ~/libreoffice

test -n "`ps ax | grep run-libreoffice-ciabot.pl | grep -v grep`" || screen -d -m run-libreoffice-ciabot.pl
