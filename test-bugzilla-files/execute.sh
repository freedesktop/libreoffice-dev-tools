ulimit -c unlimited
dir_name=$(basename $1)
dir=${PWD}
source ${dir}/config
mkdir -p ${CRASHTESTDATA}/control/$dir_name
cd ${CRASHTESTDATA}/control/$dir_name
TMPDIR=${CRASHTESTDATA}/tmpdir ${INSTDIR}/program/python ${dir}/test-bugzilla-files.py --soffice=path:${INSTDIR}/program/soffice --userdir=file://${USERDIR}/libreoffice_$dir_name/4 $1 2>&1 | tee ${CRASHTESTDATA}/console_$dir_name.log
