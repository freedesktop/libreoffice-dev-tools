/*
 * Version: MPL 1.1 / GPLv3+ / LGPLv3+
 *
 * The contents of this file are subject to the Mozilla Public License Version
 * 1.1 (the "License"); you may not use this file except in compliance with
 * the License or as specified alternatively below. You may obtain a copy of
 * the License at https://www.mozilla.org/MPL/
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

#include <cstdarg>

#include <com/sun/star/beans/Optional.hpp>
#include <com/sun/star/beans/StringPair.hpp>
#include <com/sun/star/lang/EventObject.hpp>
#include <com/sun/star/uno/Any.h>
#include <com/sun/star/uno/Exception.hpp>
#include <com/sun/star/uno/Sequence.h>
#include <com/sun/star/uno/Type.h>
#include <com/sun/star/uno/TypeClass.hpp>
#include <com/sun/star/uno/XComponentContext.hpp>
#include <com/sun/star/uno/XInterface.hpp>

#include <cppu/unotype.hxx>

#include <rtl/ustring.hxx>

#include <sal/types.h>

void stop() {}

namespace beans = com::sun::star::beans;
namespace lang = com::sun::star::lang;
using namespace com::sun::star::uno;

template<typename T, int N>
T* get_array()
{
    static T data[N];

    for (int i(0); i != N; ++i)
        data[i] = i;

    return data;
}

int main()
{
    using cppu::UnoSequenceType;
    using cppu::UnoType;
    using rtl::OUString;

    Type type_void;
    Type type_boolean(UnoType<bool>::get());
    Type type_byte(UnoType<sal_Int8>::get());
    Type type_short(UnoType<sal_Int16>::get());
    Type type_long(UnoType<sal_Int32>::get());
    Type type_hyper(UnoType<sal_Int64>::get());
    Type type_float(UnoType<float>::get());
    Type type_double(UnoType<double>::get());
    Type type_char(UnoType<cppu::UnoCharType>::get());
    Type type_string(UnoType<OUString>::get());
    Type type_type(UnoType<Type>::get());
    Type type_any(UnoType<Any>::get());
    Type type_sequence(UnoType<UnoSequenceType<sal_Int8> >::get());
    Type type_sequence_sequence(UnoType<UnoSequenceType<UnoSequenceType<sal_Int8> > >::get());
    Type type_enum(UnoType<TypeClass>::get());
    Type type_struct(UnoType<lang::EventObject>::get());
    Type type_generic_struct(UnoType<beans::Optional<sal_Int8> >::get());
    Type type_exception(UnoType<Exception>::get());
    Type type_interface(UnoType<XInterface>::get());
    Type type_interface_reference(UnoType<Reference<XInterface> >::get());
    Type type_derived_interface(UnoType<XComponentContext>::get());

    Any empty_any;
    Any any_boolean(true);
    Any any_int(static_cast<sal_Int32>(42));
    Any any_double(3.14);
    Any any_char;
        any_char <<= static_cast<sal_Unicode>('c');
    Any any_string(OUString(RTL_CONSTASCII_USTRINGPARAM("hello, gdb")));
    Any any_type(type_string);
    Any any_sequence;
    Any any_enum(TypeClass_STRING);
    Any any_struct;
    {
        beans::StringPair pair(OUString(RTL_CONSTASCII_USTRINGPARAM("hello")), OUString(RTL_CONSTASCII_USTRINGPARAM("gdb")));
        // any_struct <<= pair;
    }
    // Any any_interface((Reference<XInterface>()));

    Sequence<sal_Int8> empty_sequence;
    Sequence<sal_Bool> sequence_boolean(get_array<sal_Bool, 2>(), 2);
    Sequence<sal_Int8> sequence_byte(get_array<sal_Int8, 4>(), 4);
    Sequence<sal_Int16> sequence_short(get_array<sal_Int16, 4>(), 4);
    Sequence<sal_Int32> sequence_long(get_array<sal_Int32, 4>(), 4);
    any_sequence <<= sequence_long;
    Sequence<sal_Int64> sequence_hyper(get_array<sal_Int64, 4>(), 4);
    Sequence<sal_Unicode> sequence_char;
    {
        OUString str(RTL_CONSTASCII_USTRINGPARAM("hello, gdb"));
        Sequence<sal_Unicode> tmp(str.getStr(), str.getLength());
        sequence_char = tmp;
    }
    Sequence<OUString> sequence_string(2);
    sequence_string[0] = OUString(RTL_CONSTASCII_USTRINGPARAM("hello, gdb"));
    sequence_string[1] = OUString(RTL_CONSTASCII_USTRINGPARAM("blah blah"));
    Sequence<Type> sequence_type(2);
    sequence_type[0] = type_long;
    sequence_type[1] = type_string;
    Sequence<Any> sequence_any(2);
    sequence_any[0] = any_int;
    sequence_any[1] = any_sequence;
    Sequence<Sequence<sal_Int32> > sequence_sequence(2);
    {
        Sequence<sal_Int32> tmp(get_array<sal_Int32, 2>(), 2);
        sequence_sequence[0] = sequence_long;
        sequence_sequence[1] = tmp;
    }

    stop();
}

// vim: set ts=4 sw=4 et:
