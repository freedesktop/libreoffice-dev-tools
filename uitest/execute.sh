SRCDIR="${SRCDIR:-$(pwd)}"
$SRCDIR/instdir/program/python $SRCDIR/uitest/test_main.py --debug --soffice=path:$SRCDIR/instdir/program/soffice --userdir=file:///tmp/libreoffice_$dir_name/4 --file=$SRCDIR/uitest/calc_tests/create_range_name.py
