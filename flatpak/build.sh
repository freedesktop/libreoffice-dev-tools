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
# org.gnome.Platform 3.20 runtime (and SDK) from <http://sdk.gnome.org/repo/>.
# To obtain the latter, do something like:
#
#  $ flatpak remote-add --user gnome-sdk http://sdk.gnome.org/repo/
#  $ flatpak install --user gnome-sdk org.gnome.Platform 3.20
#  $ flatpak install --user gnome-sdk org.gnome.Sdk 3.20
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


# 1  Install Perl:Archive-Zip not available in org.gnome.Sdk:

if [ ! -e "${my_dir?}"/perl ]; then
 wget \
  http://search.cpan.org/CPAN/authors/id/P/PH/PHRED/Archive-Zip-1.56.tar.gz \
  -O "${my_dir?}"/Archive-Zip-1.56.tar.gz
 mkdir "${my_dir?}"/perl
 (cd "${my_dir?}"/perl && tar xf "${my_dir?}"/Archive-Zip-1.56.tar.gz)
fi


# 2  Clone the LibreOffice git repo:

if [ -e "${my_dir?}"/lo ]; then
 git -C "${my_dir?}"/lo fetch --tags
 git -C "${my_dir?}"/lo submodule foreach git fetch --tags
 git -C "${my_dir?}"/lo checkout "${my_gitbranch?}"
else
 git clone --branch "${my_gitbranch?}" --recursive \
  git://gerrit.libreoffice.org/core "${my_dir?}"/lo
fi


# 3  Fetch external dependencies of LibreOffice:

rm -fr "${my_dir?}"/fetch
mkdir "${my_dir?}"/fetch
(cd "${my_dir?}"/fetch \
 && "${my_dir?}"/lo/autogen.sh --prefix="${my_dir?}"/inst \
  --with-distro=LibreOfficeFlatpak --with-external-tar="${my_dir?}"/tar \
 && make fetch)


# 4  Build LibreOffice:

rm -fr "${my_dir?}"/app "${my_dir?}"/build "${my_dir?}"/inst
flatpak build-init "${my_dir?}"/app org.libreoffice.LibreOffice org.gnome.Sdk \
 org.gnome.Platform 3.20
mkdir "${my_dir?}"/build
flatpak build --build-dir="${my_dir?}"/build \
 --env=PERLLIB="${my_dir?}"/perl/Archive-Zip-1.56/lib "${my_dir?}"/app bash -c \
 '"${1?}"/lo/autogen.sh --prefix="${1?}"/inst --with-distro=LibreOfficeFlatpak \
  --with-external-tar="${1?}"/tar && make && make distro-pack-install' \
 bash "${my_dir?}"


# 5  Assemble the app files and metadata:

cp -r "${my_dir?}"/inst/lib/libreoffice "${my_dir?}"/app/files/
mkdir "${my_dir?}"/app/files/bin
## Per "man gdbus" and <https://developer.gnome.org/glib/stable/
## gvariant-text.html#gvariant-text-strings> (cf.
## <https://bugzilla.gnome.org/show_bug.cgi?id=768555#c1>, comment 1 to "'man
## gdbus': unclear what 'serialized GVariant' means for args to 'gdbus call'"),
## the argument to the below xdg-open must be UTF-8 encoded, must not have "..."
## or '...' as its outermost characters (as those should be interpreted by gdbus
## as---unnecessary---quoting), and must not contain backslashes (as those would
## need to be quoted as "\\"); for the first requirement, LO's
## ShellExec::execute (shell/source/unix/exec/shellexec.cxx) encodes the
## argument with osl_getThreadTextEncoding(), which these days hopefully is
## always UTF-8 on Linux (and, hoping that the argument is a valid URI, it
## should not contain any non-ASCII characters); for the latter two
## requirements, hope that the argument is a valid absolute URI, and so should
## not contain any double quotes or backslashes, nor should it contain single
## quotes as its first and last character (where the first character needs to be
## part of the URI scheme):
cat <<\EOF > "${my_dir?}"/app/files/bin/xdg-open
gdbus call --session --dest org.freedesktop.portal.Desktop \
 --object-path /org/freedesktop/portal/desktop \
 --method org.freedesktop.portal.OpenURI.OpenURI -- '' "$1" {}
EOF
chmod +x "${my_dir?}"/app/files/bin/xdg-open
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
## see <https://github.com/flatpak/flatpak/blob/master/app/
## flatpak-builtins-build-finish.c> for further places where build-finish would
## look for data:
## cp ... "${my_dir?}"/app/files/share/dbus-1/services/
## cp ... "${my_dir?}"/app/files/share/gnome-shell/search-providers/
##
## see
## <https://github.com/flatpak/flatpak/blob/master/builder/builder-manifest.c>
## for the appstream-compose command line:
mkdir "${my_dir?}"/app/files/share/appdata
for i in "${my_dir?}"/inst/share/appdata/libreoffice-*.appdata.xml; do
 sed -e 's/<id>libreoffice-/<id>org.libreoffice.LibreOffice-/' "$i" \
  > "${my_dir?}"/app/files/share/appdata/org.libreoffice.LibreOffice-"${i##*/libreoffice-}"
done
flatpak build --nofilesystem=host "${my_dir?}"/app appstream-compose \
 --prefix=/app --origin=flatpak --basename=org.libreoffice.LibreOffice \
 org.libreoffice.LibreOffice-{base,calc,draw,impress,writer}


# 6  Generate bundle

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
 --gpg-keys="${my_dir?}"/key "${my_dir?}"/repository \
 "${my_dir?}"/LibreOffice.flatpak org.libreoffice.LibreOffice \
 "${my_flatpakbranch?}"
