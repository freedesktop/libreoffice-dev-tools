# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This shell script creates a LibreOffice.flatpak bundle from a given git
# branch/tag.
#
# It expects two command line arguments, an absolute pathname for a directory
# where the script does all its work (which must not yet exist), followed by the
# requested git branch/tag (i.e., the --branch argument to "git clone").
#
# The script expects an installation of flatpak (nee xdg-app). and availability
# of the org.gnome.Platform 3.20 runtime (and SDK) from
# <http://sdk.gnome.org/repo/>.  To obtain the latter, do something like:
#
#  $ xdg-app --user remote-add gnome-sdk http://sdk.gnome.org/repo/
#  $ xdg-app --user install gnome-sdk org.gnome.Platform 3.20
#  $ xdg-app --user install gnome-sdk org.gnome.Sdk 3.20
#
# TODO:
#
# * Fix the --repo-url=http://libreoffice.org/TODO URL in the build-bundle
# step.
#
# * GPG signing.
#
# * Explicitly specify the --arch to build?
#
# * The script still calls the old "xdg-app" tool throughout.  All these calls
# shall be rewritten to "flatpak" in environments that use the new name.


set -e

my_dir="${1?}"
my_branch="${2?}"

mkdir "${my_dir?}"


# 1  Install Perl:Archive-Zip not available in org.gnome.Sdk:

wget http://search.cpan.org/CPAN/authors/id/P/PH/PHRED/Archive-Zip-1.56.tar.gz \
 -O "${my_dir?}"/Archive-Zip-1.56.tar.gz
mkdir "${my_dir?}"/perl
(cd "${my_dir?}"/perl && tar xf "${my_dir?}"/Archive-Zip-1.56.tar.gz)


# 2  Clone the LibreOffice git repo:

git clone --branch "${my_branch?}" --recursive \
 git://gerrit.libreoffice.org/core "${my_dir?}"/lo


# 3  Fetch external dependencies of LibreOffice:

mkdir "${my_dir?}"/fetch
(cd "${my_dir?}"/fetch \
 && "${my_dir?}"/lo/autogen.sh --prefix="${my_dir?}"/inst \
  --with-distro=LibreOfficeFlatpak --with-external-tar="${my_dir?}"/tar \
 && make fetch)


# 4  Build LibreOffice:

xdg-app build-init "${my_dir?}"/app org.libreoffice.LibreOffice org.gnome.Sdk \
 org.gnome.Platform 3.20
mkdir "${my_dir?}"/build
xdg-app build --build-dir="${my_dir?}"/build \
 --env=PERLLIB="${my_dir?}"/perl/Archive-Zip-1.56/lib "${my_dir?}"/app bash -c \
 '"${1?}"/lo/autogen.sh --prefix="${1?}"/inst --with-distro=LibreOfficeFlatpak \
  --with-external-tar="${1?}"/tar && make && make distro-pack-install' \
 bash "${my_dir?}"


# 5  Assemble the app files and metadata:

cp -r "${my_dir?}"/inst/lib/libreoffice "${my_dir?}"/app/files/
mkdir "${my_dir?}"/app/files/share
mkdir "${my_dir?}"/app/files/share/applications
## libreoffice-*.desktop -> org.libreoffice.LibreOffice-*.desktop:
for i in "${my_dir?}"/inst/share/applications/libreoffice-*.desktop; do
 sed -e 's,^Exec=libreoffice,Exec=/app/libreoffice/program/soffice,' \
  -e 's/^Icon=libreoffice-/Icon=org.libreoffice.LibreOffice-/' "$i" \
  > "${my_dir?}"/app/files/share/applications/org.libreoffice.LibreOffice-"${i##*/libreoffice-}"
done
mkdir "${my_dir?}"/app/files/share/icons
## icons/hicolor/*/apps/libreoffice-* ->
## icons/hicolor/*/apps/org.libreoffice.LibreOffice-*:
for i in "${my_dir?}"/inst/share/icons/hicolor/*/apps/libreoffice-*; do
 mkdir -p \
  "$(dirname "${my_dir?}"/app/files/share/icons/hicolor/"${i#"${my_dir?}"/inst/share/icons/hicolor/}")"
 cp -a "$i" \
  "$(dirname "${my_dir?}"/app/files/share/icons/hicolor/"${i#"${my_dir?}"/inst/share/icons/hicolor/}")"/org.libreoffice.LibreOffice-"${i##*/apps/libreoffice-}"
done
## see git://anongit.freedesktop.org/xdg-app/xdg-app
## app/flatpak-builtins-build-finish.c for further places where build-finish
## would look for data:
## cp ... "${my_dir?}"/app/files/share/dbus-1/services/
## cp ... "${my_dir?}"/app/files/share/gnome-shell/search-providers/
##
## see git://anongit.freedesktop.org/xdg-app/xdg-app builder/builder-manifest.c
## for the appstream-compose command line:
mkdir "${my_dir?}"/app/files/share/appdata
for i in "${my_dir?}"/inst/share/appdata/libreoffice-*.appdata.xml; do
 sed -e 's/<id>libreoffice-/<id>org.libreoffice.LibreOffice-/' "$i" \
  > "${my_dir?}"/app/files/share/appdata/org.libreoffice.LibreOffice-"${i##*/libreoffice-}"
done
xdg-app build --nofilesystem=host "${my_dir?}"/app appstream-compose \
 --prefix=/app --origin=flatpak --basename=org.libreoffice.LibreOffice \
 org.libreoffice.LibreOffice-{base,calc,draw,impress,writer}


# 6  Generate bundle:

xdg-app build-finish --command=/app/libreoffice/program/soffice \
 --share=network --share=ipc --socket=x11 --socket=wayland --socket=pulseaudio \
 --socket=system-bus --socket=session-bus --filesystem=host \
 --env=LIBO_FLATPAK=1 "${my_dir?}"/app
xdg-app build-export "${my_dir?}"/repo "${my_dir?}"/app
xdg-app build-bundle --repo-url=http://libreoffice.org/TODO "${my_dir?}"/repo \
 "${my_dir?}"/LibreOffice.flatpak org.libreoffice.LibreOffice
