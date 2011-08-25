/*
 * Version: MPL 1.1 / GPLv3+ / LGPLv3+
 *
 * The contents of this file are subject to the Mozilla Public License Version
 * 1.1 (the "License"); you may not use this file except in compliance with
 * the License or as specified alternatively below. You may obtain a copy of
 * the License at http://www.mozilla.org/MPL/
 *
 * Software distributed under the License is distributed on an "AS IS" basis,
 * WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
 * for the specific language governing rights and limitations under the
 * License.
 *
 * Major Contributor(s):
 * Copyright (C) 2011 David Tardon, Red Hat Inc. <dtardon@redhat.com> (initial developer)
 *
 * All Rights Reserved.
 *
 * For minor contributions see the git repository.
 *
 * Alternatively, the contents of this file may be used under the terms of
 * either the GNU General Public License Version 3 or later (the "GPLv3+"), or
 * the GNU Lesser General Public License Version 3 or later (the "LGPLv3+"),
 * in which case the provisions of the GPLv3+ or the LGPLv3+ are applicable
 * instead of those above.
 */

#include <limits>

#include <sal/types.h>

#include <tools/bigint.hxx>
#include <tools/color.hxx>
#include <tools/date.hxx>
#include <tools/datetime.hxx>
#include <tools/dynary.hxx>
#include <tools/fract.hxx>
#include <tools/list.hxx>
#include <tools/stack.hxx>
#include <tools/string.hxx>
#include <tools/table.hxx>
#include <tools/time.hxx>

typedef int* value_type;

DECLARE_DYNARRAY(dynarray_type, value_type);
DECLARE_LIST(list_type, value_type);
DECLARE_STACK(stack_type, value_type);
DECLARE_TABLE(table_type, value_type);

void stop() {}

int main()
{
    // old-style strings
    ByteString bs("ByteString");
    UniString us(UniString::CreateFromAscii("UniString"));
    UniString su_(UniString::CreateFromAscii("sal_Unicode"));
    sal_Unicode* su(su_.GetBufferAccess());

    // old-style containers
    dynarray_type empty_dynarray;
    dynarray_type dynarray;
    dynarray.Put(0, new int(0));
    dynarray.Put(1, new int(1));

    list_type empty_list;
    list_type list;
    list.Insert(new int(0));
    list.Insert(new int(1));

    stack_type empty_stack;
    stack_type stack;
    stack.Push(new int(0));
    stack.Push(new int(1));

    table_type empty_table;
    table_type table;
    table.Insert(2, new int(0));
    table.Insert(8, new int(1));

    // various types
    BigInt small_int(42);
    BigInt max_uint(std::numeric_limits<sal_uInt32>::max());
    BigInt big_int(String::CreateFromAscii("123456789123456789"));

    Color color_black;
    Color color_red_transparent(COL_RED);
    color_red_transparent.SetTransparency(0x80);

    Fraction fraction_0;
    Fraction fraction_simple(2L);
    Fraction fraction(1, 5);

    Date date_empty;
    Date date(21, 7, 2011);

    Time time_empty;
    Time time_no_100sec(15, 52, 1);
    Time time(15, 52, 28, 42);

    DateTime date_time_empty;
    DateTime date_time_no_time(date);
    DateTime date_time_no_date(time);
    DateTime date_time(date, time);

    stop();
}

// vim: set sts=4 sw=4 et:
