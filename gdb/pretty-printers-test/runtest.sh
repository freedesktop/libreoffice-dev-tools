#!/bin/sh

OUTDIR=`pwd`/../../../solver/unxlngx6
export LD_LIBRARY_PATH=${OUTDIR}/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
export PYTHONPATH=`pwd`/../../../solenv/gdb
binfile=`readlink -f ${OUTDIR}/bin/test_pp_$1`
runtest --srcdir `pwd`/test --tool $1 BINFILE=${binfile}

# vim:set shiftwidth=4 tabstop=4 expandtab:
