# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# This shell script creates a LibreOffice.flatpak bundle from a given
# flatpak-builder manifest.json.
#
# It expects five command line arguments, in the following order:
# * An absolute pathname for a directory where the script does all its work.
# * The absolute pathname of the manifest.json file.
# * The flatpak branch name (which must match the "branch" value in the
#   manifest.json file).
# * The absolute pathname of the GPG home directory (i.e., the --homedir=
#   argument to gpg)
# * The GPG key ID for signing.
#
# The script expects an installation of flatpak and availability of the
# org.gnome.Platform 3.24 runtime (and SDK) from <http://sdk.gnome.org/repo/>
# (or whatever is specified in the manifest.json file).  To obtain the latter,
# do something like:
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
my_manifest="${2?}"
my_flatpakbranch="${3?}"
my_gpghomedir="${4?}"
my_gpgkeyid="${5?}"

mkdir -p "${my_dir?}"

flatpak-builder --repo="${my_dir?}"/repository \
 --gpg-homedir="${my_gpghomedir?}" --gpg-sign="${my_gpgkeyid?}" --force-clean \
 "${my_dir?}"/app "${my_manifest?}"

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
