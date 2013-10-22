#! /usr/bin/env make
# -*- Mode: makefile-gmake; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*-
#
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
# [ Copyright (C) 2011 Bjoern Michaelsen (initial developer) ]
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
#

include bibisect.cfg

BINREPO:=$(WORKDIR)/binrepo
BUILDDIR:=$(WORKDIR)/build
ARTIFACTDIR:=$(WORKDIR)/artifact
ORDERMODE?=master
SHELL:=/bin/bash

ifeq ($(ORDERMODE),master)
SOURCETYPE:=hash
endif
ifeq ($(ORDERMODE),tags)
SOURCETYPE:=tag
endif

.DEFAULT_GOAL=all
.PHONY: all clean
all:
		@echo "finished: binary repository is in $(BINREPO)"

clean:
		rm -rf $(BINREPO) $(BUILDDIR) $(ARTIFACTDIR) $(WORKDIR)/milestone $(WORKDIR)/buildorder $(WORKDIR)/init


define commit_artifacts
cd $(BINREPO) && git checkout -f $(1) && \
cd $(ARTIFACTDIR) && \
git --git-dir=$(BINREPO)/.git --work-tree=$(ARTIFACTDIR) add -A && \
git --git-dir=$(BINREPO)/.git --work-tree=$(ARTIFACTDIR) commit -F $(ARTIFACTDIR)/commitmsg && \
git --git-dir=$(BINREPO)/.git tag source-$(SOURCETYPE)-$(2) && \
echo "$(2) $(3)" > $@;
endef


$(WORKDIR)/milestone/%:
		rm -rf $(BUILDDIR)
		rm -rf $(ARTIFACTDIR)
		git clone -n $(SOURCEREPO) $(BUILDDIR)
		mkdir -p $(ARTIFACTDIR)
		cd $(BUILDDIR) && git checkout $*
		$(BUILDSCRIPT) $(BUILDDIR) $(ARTIFACTDIR); if test $$? -eq 0; \
		then \
				$(call commit_artifacts,master,$*,success) \
		else \
				$(call commit_artifacts,failures,$*,failed) \
		fi

ifneq ($(MAKECMDGOALS),clean)
include $(WORKDIR)/buildorder
endif


ifeq ($(ORDERMODE),master)
$(WORKDIR)/buildorder: $(WORKDIR)/init
		git --git-dir=$(SOURCEREPO) rev-list --reverse $(FROM)..$(TO) | \
			awk \
				'BEGIN { last="$@" } \
				NR % $(INTERVAL) == 1 { current="$(WORKDIR)/milestone/" $$0; printf "%s: %s\n", current, last; last = current} \
				END { printf "$(TO): %s\nall: $(TO)", last }' > $@

endif

ifeq ($(ORDERMODE),tags)
$(WORKDIR)/buildorder: $(WORKDIR)/init
	git --git-dir=$(SOURCEREPO) tag|grep ^libreoffice|sed -e 's/\./-/g'|paste - <(git --git-dir=$(SOURCEREPO) tag|grep ^libreoffice)|sort|cut -f2| \
		awk \
			'BEGIN { last="$@" } \
			{ current="$(WORKDIR)/milestone/" $$0; printf "%s: %s\n", current, last; last = current} \
			END { printf "$(TO): %s\nall: $(TO)", last }' > $@

endif

$(WORKDIR)/init:
		mkdir -p $(WORKDIR)/milestone
		mkdir -p $(BUILDDIR)
		mkdir -p $(ARTIFACTDIR)
		git init $(BINREPO)
		git --git-dir=$(BINREPO)/.git commit --allow-empty -m 'root'
		git --git-dir=$(BINREPO)/.git branch failures
		touch $@

# vim:set shiftwidth=4 softtabstop=4 noexpandtab:
