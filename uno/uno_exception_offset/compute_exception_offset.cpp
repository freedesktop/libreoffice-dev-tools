/* -*- Mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*- */
/*
* This file is part of the LibreOffice project.
*
* This Source Code Form is subject to the terms of the Mozilla Public
* License, v. 2.0. If a copy of the MPL was not distributed with this
* file, You can obtain one at https://mozilla.org/MPL/2.0/.
*/

#include <iostream>     /* cout */
#include <stddef.h>     /* offsetof */
#include <mtdll.h>      /* _tiddata */

using namespace std;

int main()
{
    int offset_curexception = (int)offsetof(struct _tiddata, _curexception);
    int offset_tpxcptinfoptrs = (int)offsetof(struct _tiddata, _tpxcptinfoptrs);

    cout << "Computing uno exception offset on platform: " <<
#if defined (_M_X64)
        "X86-64"
#elif defined (_M_IX86)
        "intel"
#else
        error: unknown prltform
#endif
        << endl;
    cout << "offsetof(struct _tiddata,_curexception) is: 0x" << std::hex
        << offset_curexception << endl;
    cout << "offsetof(struct _tiddata,_tpxcptinfoptrs) is: 0x" << std::hex
        <<  offset_tpxcptinfoptrs << endl;
    cout << "offsetof(_curexception) - offsetof(_tpxcptinfoptrs): 0x" << std::hex
        << offset_curexception - offset_tpxcptinfoptrs << endl;

    cout << "Enter any key to continue...";
    cin.get();
    return 0;
}

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
