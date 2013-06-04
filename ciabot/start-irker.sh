#!/bin/bash

cd ~/bin/irker
export PYTHONPATH=irc-8.3
if test -z "`ps ax | grep irkerd | grep -v grep`"; then
	./irkerd -n loirkerbot &>irkerd.log &
fi
