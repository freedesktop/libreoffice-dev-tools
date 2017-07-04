# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This shell script creates a LibreOffice.flatpak bundle from a given git
# branch/tag.
#
# It expects five command line arguments, in the following order:
# * An absolute pathname for a directory where the script does all its work.
# * The requested git branch/tag (i.e., the --branch argument to "git clone").
# * The flatpak branch name.
# * The absolute pathname of the GPG home directory (i.e., the --homedir=
#   argument to gpg)
# * The GPG key ID for signing.
#
# The script expects an installation of flatpak and availability of the
# org.gnome.Platform 3.24 runtime (and SDK) from <http://sdk.gnome.org/repo/>.
# To obtain the latter, do something like:
#
#  $ flatpak remote-add --user --from gnome-sdk \
#     https://sdk.gnome.org/gnome.flatpakrepo
#  $ flatpak install --user gnome-sdk org.gnome.Platform 3.24
#  $ flatpak install --user gnome-sdk org.gnome.Sdk 3.24
#  ...
#  $ flatpak update --user
#
# TODO:
#
# * Explicitly specify the --arch to build?


set -e

my_dir="${1?}"
my_gitbranch="${2?}"
my_flatpakbranch="${3?}"
my_gpghomedir="${4?}"
my_gpgkeyid="${5?}"

mkdir -p "${my_dir?}"


# 1  Clone the LibreOffice git repo:

if [ -e "${my_dir?}"/lo ]; then
 git -C "${my_dir?}"/lo fetch --tags
 git -C "${my_dir?}"/lo submodule foreach git fetch --tags
 git -C "${my_dir?}"/lo checkout "${my_gitbranch?}"
else
 git clone --branch "${my_gitbranch?}" --recursive \
  git://gerrit.libreoffice.org/core "${my_dir?}"/lo
fi


# 2  Build LibreOffice:

rm -fr "${my_dir?}"/app "${my_dir?}"/build "${my_dir?}"/inst
flatpak build-init "${my_dir?}"/app org.libreoffice.LibreOffice org.gnome.Sdk \
 org.gnome.Platform 3.24
mkdir "${my_dir?}"/build
flatpak build --build-dir="${my_dir?}"/build --share=network "${my_dir?}"/app \
 bash -c \
 '"${1?}"/lo/autogen.sh --prefix="${1?}"/inst --with-distro=LibreOfficeFlatpak \
  && make && make distro-pack-install-strip \
  && make cmd cmd='\''$(SRCDIR)/solenv/bin/assemble-flatpak.sh'\' \
 bash "${my_dir?}"


# 3  Assemble the app files and metadata:

## see
## <https://github.com/flatpak/flatpak/blob/master/builder/builder-manifest.c>
## for the appstream-compose command line:
flatpak build --nofilesystem=host "${my_dir?}"/app appstream-compose \
 --prefix=/app --origin=flatpak --basename=org.libreoffice.LibreOffice \
 org.libreoffice.LibreOffice


# 4  Generate repository, .flatpak bundle, and .flatpakref file

flatpak build-finish --command=/app/libreoffice/program/soffice \
 --share=network --share=ipc --socket=x11 --socket=wayland --socket=pulseaudio \
 --socket=system-bus --socket=session-bus --filesystem=host \
 --env=LIBO_FLATPAK=1 "${my_dir?}"/app
flatpak build-export --gpg-homedir="${my_gpghomedir?}" \
 --gpg-sign="${my_gpgkeyid?}" "${my_dir?}"/repository "${my_dir?}"/app \
 "${my_flatpakbranch?}"
## --prune-depth=1 leaves the one most recent older revision available; that
## keeps the repo from growing without bounds, but for one allows users to roll
## back at least one rev (if there's decent support for that; there's currently
## "flatpak update --commit="), and for another makes --generate-static-deltas
## provide fast deltas at least from that prev rev (in addition to fast deltas
## "from nothing"):
flatpak build-update-repo --title='The Document Foundation LibreOffice' \
 --generate-static-deltas --prune --prune-depth=1 \
 --gpg-homedir="${my_gpghomedir?}" --gpg-sign="${my_gpgkeyid?}" \
 "${my_dir?}"/repository
tar --create --file "${my_dir?}"/repository.tgz --gzip \
 --directory="${my_dir?}" repository
rm -f "${my_dir?}"/key
gpg2 --homedir="${my_gpghomedir?}" --output="${my_dir?}"/key --export \
 "${my_gpgkeyid?}"
flatpak build-bundle \
 --repo-url=http://download.documentfoundation.org/libreoffice/flatpak/repository \
 --runtime-repo=https://sdk.gnome.org/gnome.flatpakrepo \
 --gpg-keys="${my_dir?}"/key "${my_dir?}"/repository \
 "${my_dir?}"/LibreOffice.flatpak org.libreoffice.LibreOffice \
 "${my_flatpakbranch?}"
rm -f "${my_dir?}"/LibreOffice.flatpakref
printf \
 '[Flatpak Ref]\nTitle=The Document Foundation LibreOffice\nName=org.libreoffice.LibreOffice\nBranch=%s\nUrl=http://download.documentfoundation.org/libreoffice/flatpak/repository\nIsRuntime=False\nGPGKey=%s\nRuntimeRepo=https://sdk.gnome.org/gnome.flatpakrepo\n' \
 "${my_flatpakbranch?}" "$(base64 --wrap=0 < "${my_dir?}"/key)" \
 > "${my_dir?}"/LibreOffice.flatpakref
