ccache for MSVC
===============

This is a serie of patches that enable ccache to work with Microsoft Visual
C++ compiler.  This is an experimental work - works for me for the LibreOffice
building, but of course in is not guaranteed to work for you :-)  Also the
time saved is not that huge, the preprocessing takes quite some time with MSVC.

How to make it work for you with LibreOffice:

# copy it somewhere visible in your PATH
cp bin/ccache.exe ~/bin

# set it up (and make sure the variables are setup in your environment)
cat >> ~/.bashrc << EOF
export PATH=~/bin:"$PATH"
export CC="ccache C:/PROGRA~1/MICROS~1.0/VC/bin/cl.exe"
export CXX="ccache C:/PROGRA~1/MICROS~1.0/VC/bin/cl.exe"
EOF

ccache -M 10G

# enjoy it! :-)
cd LibreOffice/master
./autogen.sh
# check that ccache is visible in the output of autogen.sh before running make
make

# you can check from time to time that ccache is being filed in / used
ccache -s

How to build your own version
-----------------------------

If you do not trust the ccache.exe binary, you can build your own.  It is
based on a pre-historic 2.4 release, but I did not have the energy to update
my old patches against anything more recent, so I am afraid you have to live
with that ;-)

# get it and apply the patches
git clone git//git.samba.org/ccache.git ~/ccache
cd ~/ccache
git checkout -b ccache-msvc v2.4
git am ~/dev-tools/ccache-msvc/patches/*

# build it
./configure
make
