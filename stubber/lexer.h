#ifndef LEXER_H
#define LEXER_H

#include <stdint.h>
#include <string.h>
#include <list>

using namespace std;

#define cmp(a,b) !strcmp(a,b)

#define isMod(t) (t > kT_ModifierB && t < kT_ModifierE)
#define isCon(t) (t > kT_ConstantB && t < kT_ConstantE)
#define isTMod(t) (t > kT_TypeModifierB && t < kT_TypeModifierE)
#define isShw(t) (t > kT_ShwModB && t < kT_ShwModE)
#define isPrag(t) (t > kT_PragmaB && t < kT_PragmaE)

enum Token {kT__End = 0, kT__Invalid,
           kT_SCol, kT_Comma, kT_Col, kT_Hash, kT_DCol,
           kT_Namespace, kT_Template, kT_Union,

           kT_ShwModB,
               kT_Public,
               kT_Private,
               kT_Protected,
           kT_ShwModE,

           kT_ModifierB,
                kT_Virtual, kT_Friend,  kT_Inline, kT_Volatile, kT_Mutable, kT_Static, kT_Explicit,
           kT_TypeModifierB,
                kT_Const,
           kT_ModifierE,
                kT_Class, kT_Struct, kT_Enum,
                kT_And, kT_Mul, kT_Signed, kT_Unsigned,
           kT_TypeModifierE,

           kT_ConstantB,
                kT_False, kT_True, kT_Int, kT_String, kT_Char, kT_Hex, kT_Double, kT_Float,
           kT_ConstantE,

           kT_LCh, kT_RCh,  kT_Tilde,
           kT_Typedef,
           kT_LParen, kT_RParen, kT_LBrace, kT_RBrace, kT_LBracket, kT_RBracket,
           kT_Ident,
           kT_Binary, kT_Unary,

           kT_PragmaB,
                kT_Define, kT_Ifdef, kT_Ifndef, kT_Endif, kT_Include,
           kT_PragmaE,

           kT_Dot, kT_Arrow
           };

class Lexer {
    char*   mCurr;
    char*   mHelper;

    char    mOld;

    list<pair<char*,char*> > mStack;

public:
    Lexer(char*);
    ~Lexer();

    void pushState();
    void popState();
    Token next();
    const char* ident();
    char* pos();
    void slice(char*&, char*, char*);

    void emitline();
};

#endif // LEXER_H
