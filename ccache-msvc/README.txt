ccache for MSVC
===============

This is a series of patches that enable ccache to work with Microsoft Visual
C++ compiler.  This is an experimental work - works for me for building LibreOffice,
but of course is not guaranteed to work for you :-)

How to make it work for you with LibreOffice:

# copy it somewhere visible in your PATH
cp bin/ccache.exe ~/bin

ccache -M 10G

# enjoy it! :-)
cd LibreOffice/master
./autogen.sh --enable-ccache
# check that ccache is visible in the output of autogen.sh before running make
make

# you can check from time to time that ccache is being filed in / used
ccache -s

How to build your own version
-----------------------------

If you do not trust the ccache.exe binary, you can build your own.
The patches are based on 3.1.8 so they may not apply on a different version.

# get it and apply the patches
git clone git//git.samba.org/ccache.git ~/ccache
cd ~/ccache
git am ~/dev-tools/ccache-msvc/patches/*

# build it
./autogen.sh
./configure
make
