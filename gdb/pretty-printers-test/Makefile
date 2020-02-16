# -*- Mode: makefile-gmake; tab-width: 4; indent-tabs-mode: t -*-
# Version: MPL 1.1 / GPLv3+ / LGPLv3+
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License or as specified alternatively below. You may obtain a copy of
# the License at https://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# Major Contributor(s):
# Copyright (C) 2012 Red Hat, Inc., David Tardon <dtardon@redhat.com>
#  (initial developer)
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

# This makefile sets up everything necessary to hook into the "main" gbuild
# system. That means that we are using the "main" workdir/outdir, but I
# hope that is not a big problem, becase all the produced executables
# have pretty distinctive names. Also, it can only be invoked manually,
# so noone can claim he did not know what was going on .-)

# Use: make topdir=wherever-your-main-source-dir-is
# default value is ../../..

THISDIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

ifeq ($(topdir),)
topdir := ../../..
endif

# We cannot use solenv/gbuild/partial_build.mk , because we need to
# register executables _before_ the module is read

gb_PARTIALBUILD := T

ifeq ($(SOLARENV),)
include $(topdir)/config_host.mk
endif

SRCDIR_RELATIVE := $(if $(patsubst $(SRCDIR)%,%,$(THISDIR),$(THISDIR)),$(patsubst $(SRCDIR)%,%,$(THISDIR)),$(error currently this only works if this dir is a subdir of $(SRCDIR)))

include $(topdir)/solenv/gbuild/gbuild.mk

$(eval $(call gb_Helper_add_repositories,$(THISDIR)))

$(eval $(call gb_Helper_collect_knownlibs))

$(eval $(call gb_Module_make_global_targets,Module_gdb.mk))

# vim:set shiftwidth=4 tabstop=4 noexpandtab:
