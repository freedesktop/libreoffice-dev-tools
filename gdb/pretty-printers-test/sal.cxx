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
#include <fstream>
#include <string>

#include <rtl/ref.hxx>
#include <rtl/strbuf.hxx>
#include <rtl/string.h>
#include <rtl/string.hxx>
#include <rtl/ustrbuf.hxx>
#include <rtl/ustring.h>
#include <rtl/ustring.hxx>

void stop() {}

using namespace rtl;

void getline(std::ifstream& is, OUString& out)
{
    std::string line;
    getline(is, line);
    out = OUString(line.c_str(), line.size(), RTL_TEXTENCODING_UTF8);
}

class foo : public IReference
{
public:
    foo() : m_val(42), m_count(0)
    {
    }

    virtual oslInterlockedCount SAL_CALL acquire()
    {
        m_count += 1;
        return m_count;
    }

    virtual oslInterlockedCount SAL_CALL release()
    {
        m_count -= 1;
        oslInterlockedCount const count(m_count);
        if (m_count == 0)
            delete this;
        return count;
    }

protected:
    ~foo() {}

private:
    foo(foo const&);
    foo& operator=(foo const&);

private:
    int m_val;
    oslInterlockedCount m_count;
};

int main()
{
    rtl_String* rtl_string(0);
    rtl_string_newFromStr_WithLength(&rtl_string,
            RTL_CONSTASCII_STRINGPARAM("rtl_String"));
    rtl_uString* rtl_ustring(0);
    rtl_uString_newFromAscii(&rtl_ustring, "rtl_uString");
    OString string("rtl::OString");
    OUString ustring(OUString(RTL_CONSTASCII_USTRINGPARAM("rtl::OUString")));
    OStringBuffer string_buffer("rtl::OStringBuffer");
    OUStringBuffer ustring_buffer(OUString(RTL_CONSTASCII_USTRINGPARAM("rtl::OUStringBuffer")));

    OUString ustring_western;
    OUString ustring_ctl;
    OUString ustring_cjk;
    {
        std::ifstream is("strings.txt");
        getline(is, ustring_western);
        getline(is, ustring_ctl);
        getline(is, ustring_cjk);
    }

    Reference<foo> foo_ref(new foo);

    stop();
}

// vim: set sts=4 sw=4 et:
