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
# Setting disable-fsckobjects is needed to avoid "error: object
# 8dbc86aa82fb73668816f228779b2094de546aa0: missingSpaceBeforeEmail: invalid
# author/committer line - missing space before email", which has "Author: Andre
# Fischer <andre.f.fischer <Andre Fischer<andre.f.fischer@oracle.com>".
#
# TODO:
#
# * Explicitly specify the --arch to build?
# * Properly encode my_{flatpak,git}branch in manifest.json

set -e

my_dir="${1?}"
my_gitbranch="${2?}"
my_flatpakbranch="${3?}"
my_gpghomedir="${4?}"
my_gpgkeyid="${5?}"

mkdir -p "${my_dir?}"

rm -f "${my_dir?}"/manifest.json
cat > "${my_dir?}"/manifest.json <<EOF
{
    "id": "org.libreoffice.LibreOffice",
    "runtime": "org.gnome.Platform",
    "runtime-version": "3.24",
    "sdk": "org.gnome.Sdk",
    "command": "/app/libreoffice/program/soffice",
    "separate-locales": false,
    "modules": [
        {
            "name": "libreoffice",
            "sources": [
                {
                    "type": "git",
                    "url": "git://gerrit.libreoffice.org/core",
                    "branch": "${my_gitbranch?}",
                    "disable-fsckobjects": true
                },
                {
                    "commands": [
                        "mkdir external/tarballs"
                    ],
                    "type": "shell"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/4b87018f7fff1d054939d19920b751a0-collada2gltf-master-cb1d97788a.tar.bz2",
                    "sha256": "b0adb8e71aef80751b999c9c055e419a625c4a05184e407aef2aee28752ad8cb",
                    "type": "file",
                    "dest-filename": "external/tarballs/4b87018f7fff1d054939d19920b751a0-collada2gltf-master-cb1d97788a.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/pdfium-3151.tar.bz2",
                    "sha256": "d24f41b65a797e545eeafc37106a85001437664267361a7576572b967d31ed6a",
                    "type": "file",
                    "dest-filename": "external/tarballs/pdfium-3151.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/OpenCOLLADA-master-6509aa13af.tar.bz2",
                    "sha256": "8f25d429237cde289a448c82a0a830791354ccce5ee40d77535642e46367d6c4",
                    "type": "file",
                    "dest-filename": "external/tarballs/OpenCOLLADA-master-6509aa13af.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/0168229624cfac409e766913506961a8-ucpp-1.3.2.tar.gz",
                    "sha256": "983941d31ee8d366085cadf28db75eb1f5cb03ba1e5853b98f12f7f51c63b776",
                    "type": "file",
                    "dest-filename": "external/tarballs/0168229624cfac409e766913506961a8-ucpp-1.3.2.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/xmlsec1-1.2.24.tar.gz",
                    "sha256": "99a8643f118bb1261a72162f83e2deba0f4f690893b4b90e1be4f708e8d481cc",
                    "type": "file",
                    "dest-filename": "external/tarballs/xmlsec1-1.2.24.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/368f114c078f94214a308a74c7e991bc-crosextrafonts-20130214.tar.gz",
                    "sha256": "c48d1c2fd613c9c06c959c34da7b8388059e2408d2bb19845dc3ed35f76e4d09",
                    "type": "file",
                    "dest-filename": "external/tarballs/368f114c078f94214a308a74c7e991bc-crosextrafonts-20130214.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/c74b7223abe75949b4af367942d96c7a-crosextrafonts-carlito-20130920.tar.gz",
                    "sha256": "4bd12b6cbc321c1cf16da76e2c585c925ce956a08067ae6f6c64eff6ccfdaf5a",
                    "type": "file",
                    "dest-filename": "external/tarballs/c74b7223abe75949b4af367942d96c7a-crosextrafonts-carlito-20130920.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/33e1e61fab06a547851ed308b4ffef42-dejavu-fonts-ttf-2.37.zip",
                    "sha256": "7576310b219e04159d35ff61dd4a4ec4cdba4f35c00e002a136f00e96a908b0a",
                    "type": "file",
                    "dest-filename": "external/tarballs/33e1e61fab06a547851ed308b4ffef42-dejavu-fonts-ttf-2.37.zip"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/1725634df4bb3dcb1b2c91a6175f8789-GentiumBasic_1102.zip",
                    "sha256": "2f1a2c5491d7305dffd3520c6375d2f3e14931ee35c6d8ae1e8f098bf1a7b3cc",
                    "type": "file",
                    "dest-filename": "external/tarballs/1725634df4bb3dcb1b2c91a6175f8789-GentiumBasic_1102.zip"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/134d8262145fc793c6af494dcace3e71-liberation-fonts-ttf-1.07.4.tar.gz",
                    "sha256": "61a7e2b6742a43c73e8762cdfeaf6dfcf9abdd2cfa0b099a9854d69bc4cfee5c",
                    "type": "file",
                    "dest-filename": "external/tarballs/134d8262145fc793c6af494dcace3e71-liberation-fonts-ttf-1.07.4.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/5c781723a0d9ed6188960defba8e91cf-liberation-fonts-ttf-2.00.1.tar.gz",
                    "sha256": "7890278a6cd17873c57d9cd785c2d230d9abdea837e96516019c5885dd271504",
                    "type": "file",
                    "dest-filename": "external/tarballs/5c781723a0d9ed6188960defba8e91cf-liberation-fonts-ttf-2.00.1.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/e7a384790b13c29113e22e596ade9687-LinLibertineG-20120116.zip",
                    "sha256": "54adcb2bc8cac0927a647fbd9362f45eff48130ce6e2379dc3867643019e08c5",
                    "type": "file",
                    "dest-filename": "external/tarballs/e7a384790b13c29113e22e596ade9687-LinLibertineG-20120116.zip"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/7a15edea7d415ac5150ea403e27401fd-open-sans-font-ttf-1.10.tar.gz",
                    "sha256": "cc80fd415e57ecec067339beadd0eef9eaa45e65d3c51a922ba5f9172779bfb8",
                    "type": "file",
                    "dest-filename": "external/tarballs/7a15edea7d415ac5150ea403e27401fd-open-sans-font-ttf-1.10.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/c3c1a8ba7452950636e871d25020ce0d-pt-serif-font-1.0000W.tar.gz",
                    "sha256": "6757feb23f889a82df59679d02b8ee1f907df0a0ac1c49cdb48ed737b60e5dfa",
                    "type": "file",
                    "dest-filename": "external/tarballs/c3c1a8ba7452950636e871d25020ce0d-pt-serif-font-1.0000W.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/907d6e99f241876695c19ff3db0b8923-source-code-pro-2.030R-ro-1.050R-it.tar.gz",
                    "sha256": "09466dce87653333f189acd8358c60c6736dcd95f042dee0b644bdcf65b6ae2f",
                    "type": "file",
                    "dest-filename": "external/tarballs/907d6e99f241876695c19ff3db0b8923-source-code-pro-2.030R-ro-1.050R-it.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/edc4d741888bc0d38e32dbaa17149596-source-sans-pro-2.010R-ro-1.065R-it.tar.gz",
                    "sha256": "e7bc9a1fec787a529e49f5a26b93dcdcf41506449dfc70f92cdef6d17eb6fb61",
                    "type": "file",
                    "dest-filename": "external/tarballs/edc4d741888bc0d38e32dbaa17149596-source-sans-pro-2.010R-ro-1.065R-it.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/EmojiOneColor-SVGinOT-1.3.tar.gz",
                    "sha256": "d1a08f7c10589f22740231017694af0a7a270760c8dec33d8d1c038e2be0a0c7",
                    "type": "file",
                    "dest-filename": "external/tarballs/EmojiOneColor-SVGinOT-1.3.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/boost_1_63_0.tar.bz2",
                    "sha256": "beae2529f759f6b3bf3f4969a19c2e9d6f0c503edcb2de4a61d1428519fcb3b0",
                    "type": "file",
                    "dest-filename": "external/tarballs/boost_1_63_0.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/48d647fbd8ef8889e5a7f422c1bfda94-clucene-core-2.3.3.4.tar.gz",
                    "sha256": "ddfdc433dd8ad31b5c5819cc4404a8d2127472a3b720d3e744e8c51d79732eab",
                    "type": "file",
                    "dest-filename": "external/tarballs/48d647fbd8ef8889e5a7f422c1bfda94-clucene-core-2.3.3.4.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/CoinMP-1.7.6.tgz",
                    "sha256": "86c798780b9e1f5921fe4efe651a93cb420623b45aa1fdff57af8c37f116113f",
                    "type": "file",
                    "dest-filename": "external/tarballs/CoinMP-1.7.6.tgz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/cppunit-1.14.0.tar.gz",
                    "sha256": "3d569869d27b48860210c758c4f313082103a5e58219a7669b52bfd29d674780",
                    "type": "file",
                    "dest-filename": "external/tarballs/cppunit-1.14.0.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/Firebird-3.0.0.32483-0.tar.bz2",
                    "sha256": "6994be3555e23226630c587444be19d309b25b0fcf1f87df3b4e3f88943e5860",
                    "type": "file",
                    "dest-filename": "external/tarballs/Firebird-3.0.0.32483-0.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/bae83fa5dc7f081768daace6e199adc3-glm-0.9.4.6-libreoffice.zip",
                    "sha256": "d0312c360efe04dd048b3311fe375ff36f1993b4c2e3cb58c81062990532904a",
                    "type": "file",
                    "dest-filename": "external/tarballs/bae83fa5dc7f081768daace6e199adc3-glm-0.9.4.6-libreoffice.zip"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/gpgme-1.9.0.tar.bz2",
                    "sha256": "1b29fedb8bfad775e70eafac5b0590621683b2d9869db994568e6401f4034ceb",
                    "type": "file",
                    "dest-filename": "external/tarballs/gpgme-1.9.0.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/libassuan-2.4.3.tar.bz2",
                    "sha256": "22843a3bdb256f59be49842abf24da76700354293a066d82ade8134bb5aa2b71",
                    "type": "file",
                    "dest-filename": "external/tarballs/libassuan-2.4.3.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/libgpg-error-1.27.tar.bz2",
                    "sha256": "4f93aac6fecb7da2b92871bb9ee33032be6a87b174f54abf8ddf0911a22d29d2",
                    "type": "file",
                    "dest-filename": "external/tarballs/libgpg-error-1.27.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/libabw-0.1.1.tar.bz2",
                    "sha256": "7a3d3415cf82ab9894f601d1b3057c4615060304d5279efdec6275e01b96a199",
                    "type": "file",
                    "dest-filename": "external/tarballs/libabw-0.1.1.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/libcdr-0.1.3.tar.bz2",
                    "sha256": "5160bbbfefe52bd4880840fad2b07a512813e37bfaf8ccac062fca238f230f4d",
                    "type": "file",
                    "dest-filename": "external/tarballs/libcdr-0.1.3.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/libcmis-0.5.1.tar.gz",
                    "sha256": "6acbdf22ecdbaba37728729b75bfc085ee5a4b49a6024757cfb86ccd3da27b0e",
                    "type": "file",
                    "dest-filename": "external/tarballs/libcmis-0.5.1.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/libe-book-0.1.2.tar.bz2",
                    "sha256": "b710a57c633205b933015474d0ac0862253d1c52114d535dd09b20939a0d1850",
                    "type": "file",
                    "dest-filename": "external/tarballs/libe-book-0.1.2.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/libetonyek-0.1.6.tar.bz2",
                    "sha256": "032f53e8d7691e48a73ddbe74fa84c906ff6ff32a33e6ee2a935b6fdb6aecb78",
                    "type": "file",
                    "dest-filename": "external/tarballs/libetonyek-0.1.6.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/10d61fbaa6a06348823651b1bd7940fe-libexttextcat-3.4.4.tar.bz2",
                    "sha256": "9595601c41051356d03d0a7d5dcad334fe1b420d221f6885d143c14bb8d62163",
                    "type": "file",
                    "dest-filename": "external/tarballs/10d61fbaa6a06348823651b1bd7940fe-libexttextcat-3.4.4.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/libfreehand-0.1.1.tar.bz2",
                    "sha256": "45dab0e5d632eb51eeb00847972ca03835d6791149e9e714f093a9df2b445877",
                    "type": "file",
                    "dest-filename": "external/tarballs/libfreehand-0.1.1.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/libgltf/libgltf-0.1.0.tar.gz",
                    "sha256": "119e730fbf002dd0eaafa4930167267d7d910aa17f29979ca9ca8b66625fd2da",
                    "type": "file",
                    "dest-filename": "external/tarballs/libgltf-0.1.0.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/language-subtag-registry-2017-04-19.tar.bz2",
                    "sha256": "8333809eec6fce852a1d6de68859962106e13a84705417efb03452164da3ee7a",
                    "type": "file",
                    "dest-filename": "external/tarballs/language-subtag-registry-2017-04-19.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/liblangtag-0.6.2.tar.bz2",
                    "sha256": "d6242790324f1432fb0a6fae71b6851f520b2c5a87675497cf8ea14c2924d52e",
                    "type": "file",
                    "dest-filename": "external/tarballs/liblangtag-0.6.2.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/libmspub-0.1.2.tar.bz2",
                    "sha256": "26d488527ffbb0b41686d4bab756e3e6aaeb99f88adeb169d0c16d2cde96859a",
                    "type": "file",
                    "dest-filename": "external/tarballs/libmspub-0.1.2.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/libmwaw-0.3.12.tar.xz",
                    "sha256": "7691a6e6e7221d61c40e3f630a8907e3e516b99a587e47d09ec53f8ac60ed1e7",
                    "type": "file",
                    "dest-filename": "external/tarballs/libmwaw-0.3.12.tar.xz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/libodfgen-0.1.6.tar.bz2",
                    "sha256": "2c7b21892f84a4c67546f84611eccdad6259875c971e98ddb027da66ea0ac9c2",
                    "type": "file",
                    "dest-filename": "external/tarballs/libodfgen-0.1.6.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/libpagemaker-0.0.3.tar.bz2",
                    "sha256": "3b5de037692f8e156777a75e162f6b110fa24c01749e4a66d7eb83f364e52a33",
                    "type": "file",
                    "dest-filename": "external/tarballs/libpagemaker-0.0.3.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/librevenge-0.0.4.tar.bz2",
                    "sha256": "c51601cd08320b75702812c64aae0653409164da7825fd0f451ac2c5dbe77cbf",
                    "type": "file",
                    "dest-filename": "external/tarballs/librevenge-0.0.4.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/libstaroffice-0.0.4.tar.xz",
                    "sha256": "6e728784d002144716b10fe122973b3e4edda9004538386b0b58bb303404903a",
                    "type": "file",
                    "dest-filename": "external/tarballs/libstaroffice-0.0.4.tar.xz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/ltm-1.0.zip",
                    "sha256": "083daa92d8ee6f4af96a6143b12d7fc8fe1a547e14f862304f7281f8f7347483",
                    "type": "file",
                    "dest-filename": "external/tarballs/ltm-1.0.zip"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/libvisio-0.1.5.tar.bz2",
                    "sha256": "b83b7991a40b4e7f07d0cac7bb46ddfac84dece705fd18e21bfd119a09be458e",
                    "type": "file",
                    "dest-filename": "external/tarballs/libvisio-0.1.5.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/libwpd-0.10.1.tar.bz2",
                    "sha256": "efc20361d6e43f9ff74de5f4d86c2ce9c677693f5da08b0a88d603b7475a508d",
                    "type": "file",
                    "dest-filename": "external/tarballs/libwpd-0.10.1.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/libwpg-0.3.1.tar.bz2",
                    "sha256": "29049b95895914e680390717a243b291448e76e0f82fb4d2479adee5330fbb59",
                    "type": "file",
                    "dest-filename": "external/tarballs/libwpg-0.3.1.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/libwps-0.4.7.tar.xz",
                    "sha256": "2f2cab630bceace24f9dbb7d187cd6cd1f4c9f8a7b682c5f7e49c1e2cb58b217",
                    "type": "file",
                    "dest-filename": "external/tarballs/libwps-0.4.7.tar.xz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/libzmf-0.0.1.tar.bz2",
                    "sha256": "b69f7f6e94cf695c4b672ca65def4825490a1e7dee34c2126309b96d21a19e6b",
                    "type": "file",
                    "dest-filename": "external/tarballs/libzmf-0.0.1.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/26b3e95ddf3d9c077c480ea45874b3b8-lp_solve_5.5.tar.gz",
                    "sha256": "171816288f14215c69e730f7a4f1c325739873e21f946ff83884b350574e6695",
                    "type": "file",
                    "dest-filename": "external/tarballs/26b3e95ddf3d9c077c480ea45874b3b8-lp_solve_5.5.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/mdds-1.2.3.tar.bz2",
                    "sha256": "402fec18256f95b89517d54d85f00bce1faa6e517cb3d7c98a720fddd063354f",
                    "type": "file",
                    "dest-filename": "external/tarballs/mdds-1.2.3.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/a8c2c5b8f09e7ede322d5c602ff6a4b6-mythes-1.2.4.tar.gz",
                    "sha256": "1e81f395d8c851c3e4e75b568e20fa2fa549354e75ab397f9de4b0e0790a305f",
                    "type": "file",
                    "dest-filename": "external/tarballs/a8c2c5b8f09e7ede322d5c602ff6a4b6-mythes-1.2.4.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/231adebe5c2f78fded3e3df6e958878e-neon-0.30.1.tar.gz",
                    "sha256": "00c626c0dc18d094ab374dbd9a354915bfe4776433289386ed489c2ec0845cdd",
                    "type": "file",
                    "dest-filename": "external/tarballs/231adebe5c2f78fded3e3df6e958878e-neon-0.30.1.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/openldap-2.4.44.tgz",
                    "sha256": "d7de6bf3c67009c95525dde3a0212cc110d0a70b92af2af8e3ee800e81b88400",
                    "type": "file",
                    "dest-filename": "external/tarballs/openldap-2.4.44.tgz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/liborcus-0.12.1.tar.gz",
                    "sha256": "676b1fedd721f64489650f5e76d7f98b750439914d87cae505b8163d08447908",
                    "type": "file",
                    "dest-filename": "external/tarballs/liborcus-0.12.1.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/poppler-0.57.0.tar.xz",
                    "sha256": "0ea37de71b7db78212ebc79df59f99b66409a29c2eac4d882dae9f2397fe44d8",
                    "type": "file",
                    "dest-filename": "external/tarballs/poppler-0.57.0.tar.xz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/c0b4799ea9850eae3ead14f0a60e9418-postgresql-9.2.1.tar.bz2",
                    "sha256": "db61d498105a7d5fe46185e67ac830c878cdd7dc1f82a87f06b842217924c461",
                    "type": "file",
                    "dest-filename": "external/tarballs/c0b4799ea9850eae3ead14f0a60e9418-postgresql-9.2.1.tar.bz2"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/a39f6c07ddb20d7dd2ff1f95fa21e2cd-raptor2-2.0.15.tar.gz",
                    "sha256": "ada7f0ba54787b33485d090d3d2680533520cd4426d2f7fb4782dd4a6a1480ed",
                    "type": "file",
                    "dest-filename": "external/tarballs/a39f6c07ddb20d7dd2ff1f95fa21e2cd-raptor2-2.0.15.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/1f5def51ca0026cd192958ef07228b52-rasqal-0.9.33.tar.gz",
                    "sha256": "6924c9ac6570bd241a9669f83b467c728a322470bf34f4b2da4f69492ccfd97c",
                    "type": "file",
                    "dest-filename": "external/tarballs/1f5def51ca0026cd192958ef07228b52-rasqal-0.9.33.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/e5be03eda13ef68aabab6e42aa67715e-redland-1.0.17.tar.gz",
                    "sha256": "de1847f7b59021c16bdc72abb4d8e2d9187cd6124d69156f3326dd34ee043681",
                    "type": "file",
                    "dest-filename": "external/tarballs/e5be03eda13ef68aabab6e42aa67715e-redland-1.0.17.tar.gz"
                },
                {
                    "url": "https://dev-www.libreoffice.org/src/libepubgen-0.0.1.tar.bz2",
                    "sha256": "eea910b042526ed52f7ab9292b7fa31fca32f9e042285818074ff33664db4fa2",
                    "type": "file",
                    "dest-filename": "external/tarballs/libepubgen-0.0.1.tar.bz2"
                }
            ],
            "buildsystem": "simple",
            "build-commands": [
                "./autogen.sh --prefix=/run/build/libreoffice/inst \
--with-distro=LibreOfficeFlatpak",
                "make",
                "make distro-pack-install-strip",
                "make cmd cmd='\$(SRCDIR)/solenv/bin/assemble-flatpak.sh'"
            ]
        }
    ],
    "finish-args": [
        "--share=network",
        "--share=ipc",
        "--socket=x11",
        "--socket=wayland",
        "--socket=pulseaudio",
        "--socket=system-bus",
        "--socket=session-bus",
        "--filesystem=host",
        "--env=LIBO_FLATPAK=1"
    ]
}
EOF

flatpak-builder --default-branch="${my_flatpakbranch?}" \
 --repo="${my_dir?}"/repository --gpg-homedir="${my_gpghomedir?}" \
 --gpg-sign="${my_gpgkeyid?}" --force-clean "${my_dir?}"/app \
 "${my_dir?}"/manifest.json

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
