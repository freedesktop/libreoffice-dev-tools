# Version: MPL 1.1 / GPLv3+ / LGPLv3+
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License or as specified alternatively below. You may obtain a copy of
# the License at http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# Major Contributor(s):
# Copyright (C) 2011 David Tardon, Red Hat Inc. <dtardon@redhat.com> (initial developer)
#
# All Rights Reserved.
#
# For minor contributions see the git repository.
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 3 or later (the "GPLv3+"), or
# the GNU Lesser General Public License Version 3 or later (the "LGPLv3+"),
# in which case the provisions of the GPLv3+ or the LGPLv3+ are applicable
# instead of those above.

# Okay, so this is a bit of a hack, but it works here :)

# This must be run in build env. (i.e., with Env.Host.sh sourced).

DEFS := -DGCC -DLINUX -DUNX -DGLIBC=2 -DCPPU_ENV=gcc3 -DC341 -DX86
INCLUDES := $(SOLARINC) -I$(SOLARVER)/$(INPATH)/inc/offapi -I$(SOLARVER)/$(INPATH)/inc/udkapi
LIBS := -luno_sal
LIBDIR := $(SOLARVER)/$(INPATH)/lib

cppu: LIBS += -luno_cppu

svl: LIBS += -lsvllo

sw: INCLUDES += -I$(SRC_ROOT)/sw/inc
sw: LIBS += -lswlo

tl : LIBS += -ltllo

BINS = $(patsubst %.cxx,%,$(wildcard *.cxx))

.PHONY: all clean check

all : $(BINS)

% : %.cxx
	$(CXX) -o $@ $< -O0 -ggdb3 $(DEFS) $(INCLUDES) $(LIBS) -L$(LIBDIR) -Wl,-rpath=$(LIBDIR) -Wl,-rpath-link=$(LIBDIR)

check : all $(patsubst %,check-%,$(BINS))

.PHONY : check-%
check-% : %
	export PYTHONPATH=$(SOLARENV)/gdb && \
	gdb -n -x $<.gdb $<

clean :
	rm -f $(BINS)

# vim: set ts=4 sw=4 noet:
