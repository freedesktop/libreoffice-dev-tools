#include "lexer.h"
#include <ctype.h>
#include <stdlib.h>
#include <string.h>

#define chr(c,tok) \
    if(*mCurr == c) {\
        mCurr++;\
        mOld = *mCurr;\
        *mCurr = 0;\
        return tok;\
    }

#define chr2(c1,tok1,c2,tok2) \
    if(*mCurr == c1) {\
        mCurr++;\
        if(*mCurr == c2) {\
            mCurr++;\
            mOld = *mCurr;\
            *mCurr = 0;\
            return tok2;\
        }\
        mOld = *mCurr;\
        *mCurr = 0;\
        return tok1;\
    }

#define ret(tok) {\
        mOld = *mCurr;\
        *mCurr = 0;\
        return tok;\
}

#define str(s,tok) {\
    char* tmp = s;\
    for(long i = 0; 1; i++) {\
        if(!tmp[i]) {\
            if(!isalnum(*mCurr)) {ret(tok);}\
            else break;\
        }\
        if(tmp[i] != *mCurr) break;\
        if(!*mCurr) break;\
        mCurr++;\
    }\
    mCurr = mHelper;\
}

Lexer::Lexer(char* pSource) {
    mCurr = pSource;
    mHelper = pSource;
}

Lexer::~Lexer() {

}

char* Lexer::pos() {
    return mCurr;
}

void Lexer::slice(char*& dest, char* begin, char* end) {
    char tmp = *end;
    *end = 0;
    uint32_t siz = strlen(begin);
    dest = new char[siz+1];
    strcpy(dest,begin);
    *end = tmp;
}

const char* Lexer::ident() {
    return mHelper;
}

void Lexer::pushState() {
    mStack.push_back(pair<char*,char*>(mCurr, mHelper));
}

void Lexer::popState() {
    if(mCurr != mHelper)
        *mCurr = mOld;
    mCurr = mStack.back().first;
    mHelper = mStack.back().second;
    if(mCurr != mHelper) {
        mOld = *mCurr;
        *mCurr = 0;
    }
    mStack.pop_back();
}

void Lexer::rmState() {
    mStack.pop_back();
}

char* Lexer::emitline() {
    if(mCurr != mHelper) *mCurr = mOld;
    while(*mCurr != '\n' && *mCurr != '\0') mCurr++;
    if(*mCurr) mCurr++;
    mHelper = mCurr;
    return mCurr;
}

Token Lexer::next() {
    if(mCurr != mHelper) *mCurr = mOld;
    step:
    while(*mCurr == ' ' || *mCurr == '\n' || *mCurr == '\t') mCurr++;
    if(*mCurr=='/' && *(mCurr+1)=='/') {
        mCurr=mCurr+2;
        while(*mCurr != '\n' && *mCurr) mCurr++;
        if(!*mCurr) ret(kT__End);
        mCurr++;
        goto step;
    }
    if(*mCurr=='/' && *(mCurr+1)=='*') {
        mCurr=mCurr+2;
        while(!(*mCurr == '*' && *(mCurr+1) == '/') && *mCurr) mCurr++;
        if(!*mCurr) ret(kT__End);
        mCurr+=2;
        goto step;
    }
    if(*mCurr == 0) ret(kT__End);

    mHelper = mCurr;

    //simple symbols
    chr(';', kT_SCol);
    chr(',', kT_Comma);
    chr('#', kT_Hash);
    chr('(', kT_LParen);
    chr(')', kT_RParen);
    chr('[', kT_LBracket);
    chr(']', kT_RBracket);
    chr('{', kT_LBrace);
    chr('}', kT_RBrace);
    chr('<', kT_LCh);
    chr('>', kT_RCh);
    chr('&', kT_And);
    chr('*', kT_Mul);
    chr('~', kT_Tilde);
    chr('.', kT_Dot);

    chr2(':', kT_Col, ':', kT_DCol);

    //keywords
    //...
    //types aren't keywords, but identifiers

    str("class", kT_Class);
    str("private", kT_Private);
    str("public", kT_Public);
    str("protected", kT_Protected);
    str("const", kT_Const);
    str("typedef", kT_Typedef);
    str("virtual", kT_Virtual);
    str("friend", kT_Friend);
    str("namespace", kT_Namespace);
    str("mutable", kT_Mutable);
    str("volatile", kT_Volatile);
    str("static", kT_Static);
    str("inline", kT_Inline);
    str("signed", kT_Signed);
    str("unsigned", kT_Unsigned);
    str("define", kT_Define);
    str("ifdef", kT_Ifdef);
    str("ifndef", kT_Ifndef);
    str("endif", kT_Endif);
    str("include", kT_Include);
    str("template", kT_Template);
    str("struct", kT_Struct);
    str("enum", kT_Enum);
    str("union", kT_Union);
    str("explicit", kT_Explicit);
    str("throw", kT_Throw);

    //constants
    if(*mCurr == '-') {
        mCurr++;
        if(isdigit(*mCurr)) {
            mCurr++;
            goto digittok;
        } else if(*mCurr == '>') {
            mCurr++;
            ret(kT_Arrow);
        } else ret(kT__Invalid);
    }

    if(isdigit(*mCurr)) {
        if(*mCurr == '0') {
            mCurr++;
            if(*mCurr == 'x') { //hexa
                mCurr++;
                while(('0' <= *mCurr && '9' >= *mCurr) || ('a' <= *mCurr && 'f' >= *mCurr)) mCurr++;
                ret(kT_Hex);
            }
        } else mCurr++;
        digittok:
        while(isdigit(*mCurr)) *mCurr++;
        if(*mCurr == '.') {
            mCurr++;
            while(isdigit(*mCurr)) mCurr++;
            if(*mCurr == 'f') {
                mCurr++;
                ret(kT_Float);
            } else ret(kT_Double);
        } else ret(kT_Int);
    }

    if(*mCurr == '\"') {
        while(*mCurr && *(mCurr+1) && !(*mCurr != '\\' && *(mCurr+1) =='\"')) mCurr++;
        mCurr+=2;
        ret(kT_String);
    }

    //todo: i should check for correct content
    if(*mCurr == '\'') {
        while(*mCurr && *(mCurr+1) && !(*mCurr != '\\' && *(mCurr+1) =='\'')) mCurr++;
        mCurr+=2;
        ret(kT_Char);
    }

    str("false", kT_False);
    str("true", kT_True);

    //identifiers
    if(isalpha(*mCurr) || *mCurr == '_') {
        mCurr++;
        while(isalnum(*mCurr) || *mCurr == '_') *mCurr++;
        ret(kT_Ident);
    }

    //operators
    chr2('=', kT_Binary, '=', kT_Binary);

    mCurr++;
    ret(kT__Invalid);
}
