#!/bin/bash

cd ~/bin/irker
export PYTHONPATH=irc-8.0.1
if test -z "`ps ax | grep irkerd | grep -v grep`"; then
	./irkerd &>irkerd.log &
fi
