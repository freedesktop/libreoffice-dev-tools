/*
*
*
* TODO: parsing the templated stuffs the right way
*
*
*/

#include <iostream>
#include <list>
#include <set>
#include <map>
#include <sstream>
#include <string>
#include <fstream>

#include "lexer.h"

#include <fcntl.h>
#include <ctype.h>
#include <math.h>

using namespace std;


//---------------------------------

#define COUT   "#COUT"   //the terminal output
#define VARG   "#VARG"   //the name of the actual passed variable
#define VOUT   "#VOUT"   //the out var
#define TWHOLE "#TWHOLE" //the whole type with modifiers (but not with '&')
#define TTYPE  "#TTYPE"  //the type withput modifiers
#define TOUTER "#TOUTER" //the main of the type

map<string,string> rules_ret;
map<string,string> rules_print;

//---------------------------------

enum shw {kS_Public, kS_Private, kS_Protected, kS_None};

enum ItemT {kItem_Namespace, kItem_Class, kItem_Other, kItem_Union,
            kItem_Function, kItem_TypedefT, kItem_TypedefF, kItem_Struct, kItem_Var, kItem_Shw, kItem_Macro, kItem_Include};

stringstream& operator<<(stringstream& f, list<string>& t) {
    for(auto it = t.begin(); it != t.end(); it++) {
        f << *it;
        auto it2 = it;
        it2++;
        if(it2 != t.end()) {
            if(*it == "<" && *it2 == "::") f << " ";
            else if(isalnum((*it).back()) && isalnum((*it2).front())) f << " ";
        }
    }
    return f;
}

class nsT;

struct itemT {
    nsT* parent;
    shw sh;
    list<string> name;
    ItemT itemType;
    bool isForward;
};

//temporally
struct macroT : public itemT {
    list<list<string> > par;
    bool hasBody;
};

struct typeT {
    list<string> lmod;
    list<string> rmod;
    list<string> type;
    string outer;

    typeT() {}
    void clear() {
        type.clear();
        lmod.clear();
        rmod.clear();
        outer = "";
    }

    friend stringstream& operator<<(stringstream& f, typeT& t) {
        for(auto it = t.lmod.begin(); it != t.lmod.end(); it++) f << *it << " ";
        f << t.type;
        if(!t.rmod.empty() && isalnum(t.rmod.begin()->front())) f << " ";
        for(auto it = t.rmod.begin(); it != t.rmod.end(); it++) f << *it << " ";
        return f;
    }
};

struct tabulator {
    uint32_t s;
    friend stringstream& operator<<(stringstream& f, tabulator& tab) {
        for(uint32_t i = 0; i < tab.s; i++) f << "\t";
        return f;
    }

    tabulator() {s=0;}
    tabulator& operator++() {s++;return *this;}
    tabulator& operator--() {s--;return *this;}
};

struct paramT {
    string name;
    list<string> def;

    typeT type;

    paramT() {}
    void clear() {
        name = "";
        def.clear();
        type.clear();
    }
};

struct member : public itemT {
    bool isStatic;
    bool isVolatile;
    bool isMutable;

    member() {
        isStatic = false;
        isVolatile = false;
        isMutable = false;
    }

    void clear() {
        isStatic = false;
        isVolatile = false;
        isMutable = false;
    }
};

struct methodT : public member {
    bool isConst;
    bool isNull;
    bool isVirtual;
    bool isFriend;
    bool isExplicit;
    //bool isInline;

    typeT ret;
    list<paramT> par;
    string content;
    bool isTor;
    bool isOp;

    methodT() : member() {
        isTor = false;
        isOp = false;

        isConst = false;
        isNull = false;
        isVirtual = false;
        isFriend = false;
        isExplicit = false;
    }
    void clear() {
        ret.clear();
        content = "";
        member::clear();
        isConst = false;
        isNull = false;
        isVirtual = false;
        isExplicit = false;
        isFriend = false;
        //isInline = false;
        par.clear();
        isTor = false;
    }
};

struct varT : member {
    typeT type;
    list<string> def;

    varT() : member() {}
};

class classT;
class structT;
class methodT;
class typedefT;
class typedefF;

//At structs and classes we don't care what is the content,
//we just copy it into the new file.
struct nsT : public itemT {
    list<string> temp;
    list<pair<ItemT, itemT*> > items;

    nsT() {parent = 0;}
    nsT(const list<string>& n, nsT* p = 0) {name = n;parent = p;}
    ~nsT() {
        for(auto it = items.begin(); it != items.end(); it++)
            delete it->second;
    }
};

struct classT : public nsT {
    list<string> lmod;
    list<string> rmod;

    classT() {}
};

struct structT : public nsT {
    list<string> lmod;
    list<string> rmod;

    structT() {}
};

struct typedefB : public itemT {

};

struct typedefT : public typedefB {
    typeT type;

    typedefT() {}
    ~typedefT() {}
};

struct typedefF : public typedefB {
    typeT ret;
    string lmod;
    list<typeT> par;
    string rmod;

    typedefF() {}
    ~typedefF() {}
};

string ifile;
string iruler;
string irulep;
Token tok;
Lexer* lex;
list<nsT*> route;
bool empty;

void loadfile(const char*, char*&);
bool parse(nsT*);
bool parsetype(typeT&, bool ret=false, bool=false);
bool parsens(list<string>&);
bool parsechr(typeT&);
bool parsetypedef(typedefB*&,bool&);
bool parselmodifier(list<string>&);
bool parsermodifier(list<string>&);
bool (*custom)(ItemT,itemT*) = 0; //custom filter for methods
bool (*define)(ItemT,itemT*) = 0; //if we want to avoid definig something
void filter(nsT*);
void gen(nsT*);
void printns(nsT*, stringstream&, tabulator&);
void printfunc(methodT*, stringstream&, tabulator&);
void printmacr(macroT*, stringstream&, tabulator&);
void stubns(nsT*, stringstream&, tabulator&);
void replace(string&, const string&, const string&);
void loadrulefile(const string& f, map<string, string>& to);
bool parsecmdlargs(const uint32_t&, char**);
bool parsevalue(list<string>&);

#define next tok = lex->next()
#define is(t) (tok == kT_##t)
#define ident lex->ident()

int main(int argc, char* argv[]) {
    //------------testing------------//

    argc = 4;
    argv[1] = (char*)"-ifdoc.hxx";
    argv[2] = (char*)"-rrrule_ret.txt";
    argv[3] = (char*)"-rprule_print.txt";

    //---------------------------------

    //we only have to have protected and public methods
    custom = [&](ItemT type, itemT* item){
            if(item->sh == kS_Private && (type == kItem_Function || type == kItem_Var)) return false;
            if(type == kItem_Function) {
                methodT* m = (methodT*) item;
                if(m->parent->name.empty() && m->name.size() > 1) return false;//!!!temporally!!!//
                m->isForward = true;
                if(!m->parent->name.empty() && m->name.back() == m->parent->name.back()) {
                    m->isTor = true;
                }
                if(!m->isStatic) m->isVirtual = true;
            }
            return true;
    };

    //we don't want do define constuctors and destructor
    define = [&](ItemT type ,itemT* item) {
            if(type == kItem_Function) {
            methodT* m = (methodT*) item;
                return !m->isTor;
            } else if(type == kItem_Macro) {
                macroT* m = (macroT*) item;
                if(m->name.back() == "DECL_LINK" || m->name.back() == "DECL_DLLPRIVATE_LINK") {
                    m->hasBody = true;
                    m->name.back() = "IMPL_LINK";
                    m->par.push_front(list<string>());
                    m->par.front().push_back(m->parent->name.back());
                    m->par.push_back(list<string>());
                    m->par.back().push_back("EMPTYARG");
                } else if(m->name.back() == "DECL_STATIC_LINK" || m->name.back() == "DECL_DLLPRIVATE_STATIC_LINK") {
                    m->hasBody = true;
                    m->name.back() = "IMPL_STATIC_LINK";
                    m->par.push_back(list<string>());
                    m->par.back().push_back("EMPTYARG");
                } else if(m->name.back() == "SV_DECL_PTRARR_DEL") {
                    m->hasBody = false;
                    m->name.back() = "SV_IMPL_PTRARR_GEN";
                    m->par.back().clear();
                    m->par.back().push_back("SvPtrarr");
                }
                return true;
            } else return false;
            return true;
    };
    //---------------------------------

    if(!parsecmdlargs(argc, argv)) {
        cout << "Example usage: sm -ifdoc.hxx -rrrule_ret.txt -rprule_print.txt\n";
        return 1;
    }

    char* buff;
    loadfile(ifile.c_str(), buff);
    if(!buff) return 1;
    lex = new Lexer(buff);
    nsT global;
    global.itemType = kItem_Namespace;
    if(parse(&global)) {        
        filter(&global);
        loadrulefile(iruler,rules_ret);
        loadrulefile(irulep,rules_print);
        gen(&global);
        delete lex;
        delete[] buff;
        return 0;
    } else {
        delete lex;
        delete[] buff;
        return 1;
    }
}

void loadfile(const char* fn, char*& bo) {
    long len;
    FILE* f;
    f = fopen(fn, "r");
    if(!f) {
        bo = NULL;
        return;
    }
    fseek(f, 0, SEEK_END);
    len = ftell(f);
    fseek(f, 0, SEEK_SET);
    bo = new char[len+1];
    fread(bo, 1, len, f);
    fclose(f);

    //just to be sure
    bo[len] = 0;
}

bool parse(nsT* ns) {
    shw sh = kS_None;
    if(ns->itemType == kItem_Class) sh = kS_Private;
    else if(ns->itemType == kItem_Struct) sh = kS_Public;

    nsT* nns = 0;
    next;
    while(1) {
        if(is(_End)) break;
        if(isShw(tok)) {            
            if(is(Public)) sh = kS_Public;
            else if(is(Private)) sh = kS_Private;
            else sh = kS_Protected;
            next;
            itemT* nsh = new itemT;
            nsh->sh = sh;
            nsh->parent = ns;
            nsh->itemType = kItem_Shw;
            ns->items.push_back(pair<ItemT, itemT*>(kItem_Shw, nsh));
        } else if(is(Namespace)) {
            next;
            nns = new nsT;
            nns->parent = ns;
            parsens(((nsT*)nns)->name);
            nns->sh = sh;
            nns->itemType = kItem_Namespace;
            if(is(SCol)) nns->isForward = true;
            else {
                nns->isForward = false;                
                parse(nns);
            }
            ns->items.push_back(pair<ItemT, itemT*>(kItem_Namespace, nns));
        } else if(is(Class)) {
            next;
            nns = (nsT*) new classT;
            parseclass:
            nns->parent = ns;
            classT * cp = (classT*) nns;
            while(is(Ident)) {cp->lmod.push_back(ident);next;}
            cp->name.push_back(cp->lmod.back());
            parsens(cp->name);
            cp->lmod.pop_back();
            cp->sh = sh;
            nns->itemType = kItem_Class;
            if(is(SCol)) cp->isForward = true;
            else {
                while(!is(LBrace)) {cp->rmod.push_back(ident);next;}
                cp->isForward = false;
                parse(nns);
            }
            ns->items.push_back(pair<ItemT, itemT*>(kItem_Class, nns));
        } else if(is(Struct)) {
            next;
            nns = (nsT*) new structT;
            parsestruct:
            nns->parent = ns;
            structT* cp = (structT*) nns;
            while(is(Ident)) {cp->lmod.push_back(ident);next;}
            cp->name.push_back(cp->lmod.back());
            parsens(cp->name);
            cp->lmod.pop_back();
            cp->sh = sh;
            cp->itemType = kItem_Struct;
            if(is(SCol)) nns->isForward = true;
            else {
                while(!is(LBrace)) {cp->rmod.push_back(ident);next;}
                nns->isForward = false;
                parse(nns);
            }
            ns->items.push_back(pair<ItemT, itemT*>(kItem_Struct, nns));
        } else if(is(Union)) {
            next;
            nns = new nsT;
            nns->sh = sh;
            nns->itemType = kItem_Union;
            if(is(Ident)) {
                nns->name.push_back(ident);
                next;
            }
            if(is(SCol)) nns->isForward = true;
            else {
                nns->isForward = false;
                parse(nns);
            }
            ns->items.push_back(pair<ItemT, itemT*>(kItem_Union, nns));
        } else if(is(Hash)) {
            next;
            if(is(Include)) {
                next;
                itemT* nin = new itemT;
                nin->sh = sh;
                nin->itemType = kItem_Include;
                if(is(String)) {
                    nin->name.push_back(ident);
                } else if(is(LCh)) {
                    next;
                    stringstream s;
                    s << "<";                    
                    while(!is(RCh)) {
                        s << ident;
                        next;
                    }
                    s << ">";
                    nin->name.push_back(s.str());
                }
                ns->items.push_back(pair<ItemT, itemT*>(kItem_Include, nin));
            } else lex->emitline();
        } else if(is(Typedef)) {
            typedefB* tdef;
            bool func;
            parsetypedef(tdef, func);
            tdef->sh = sh;
            tdef->parent = ns;
            ItemT type = (func)?kItem_TypedefF:kItem_TypedefT;
            tdef    ->itemType = type;
            ns->items.push_back(pair<ItemT, itemT*>(type, tdef));
        } else if(is(Template)) {
            list<string> temp;
            temp.push_back(ident);
            next;
            temp.push_back(ident);
            next;
            while(is(Class)) {
                temp.push_back(ident);
                next;
                if(is(Comma)) {
                    temp.push_back(ident);
                    next;
                }
            }
            temp.push_back(ident);
            next;
            if(is(Class)) {
                next;
                nns = (nsT*) new classT;
                nns->temp.swap(temp);
                goto parseclass;
            } else if(is(Struct)) {
                next;
                nns = (nsT*) new classT;
                nns->temp.swap(temp);
                goto parsestruct;
            }

        } else if(is(RBrace)) {
            break;
        } else if(isMod(tok) || is(DCol) || is(Ident) || is(Tilde)) {
            list<string> lmod;
            parselmodifier(lmod);
            typeT t;
            parsetype(t, true);
            list<string> name;
            parsens(name);
            bool isop = false;
            if(name.back() == "operator") {
                if(is(LParen)) {
                    next;
                    next;
                    name.back() += "()";
                } else {
                    stringstream op;
                    while(!is(LParen)) {
                        op << ident;
                        next;
                    }
                    name.push_back(op.str());
                }
                isop = true;
                goto ismethod;
            }
            if(t.outer.empty() && (ns->name.empty() || ns->name.back() != name.back())) { //it's probably a macro
                macroT* m = new macroT;
                m->parent = ns;
                m->name.swap(name);
                m->itemType = kItem_Macro;
                next;
                m->par.push_back(list<string>());
                uint32_t s = 0;
                while(!is(RParen)) {
                    m->par.back().push_back(ident);
                    if(is(LParen) || is(LBrace) || is(LBracket)) s++;
                    else if(is(RParen) || is(RBrace) || is(RBracket)) s--;
                    next;
                    if(!s && is(Comma)) {
                        m->par.push_back(list<string>());
                        next;
                    }
                }
                if(m->par.back().empty()) m->par.pop_back();
                ns->items.push_back(pair<ItemT, itemT*>(kItem_Macro, m));
            }
            else if(is(LParen)) {
                ismethod:
                methodT* m = new methodT;
                m->parent = ns;
                next;
                m->sh = sh;
                m->name.swap(name);
                m->isOp = isop;
                m->ret = t;
                for(auto it = lmod.begin(); it != lmod.end(); it++) {
                    if(*it == "virtual") m->isVirtual = true;
                    else if(*it == "static") m->isStatic = true;
                    else if(*it == "explicit") m->isExplicit = true;
                    else if(*it == "mutable") m->isMutable = true;
                    else if(*it == "volatile") m->isVolatile = true;
                    else if(*it == "friend") m->isFriend = true;
                }
                m->itemType = kItem_Function;
                while(!is(RParen)) {
                    m->par.push_back(paramT());
                    bool once = false;
                    parsetype(m->par.back().type);
                    if(is(Ident)) {
                        once = true;
                        m->par.back().name = ident;
                        next;
                    }
                    if(is(Binary)) {
                        next;
                        list<string> val;
                        parsevalue(val);
                        m->par.back().def.swap(val);
                        if(!once) goto noname;
                    }
                    if(is(Comma)) {
                        next;
                        if(!once) goto noname;
                    } else if(is(RParen)) {
                        if(!once) goto noname;
                        break;
                    }
                    continue;
                    noname:
                    uint32_t idx = 0;
                    constexpr uint32_t s32 = floor(log10(pow(2,sizeof(uint32_t))))+6.0;
                    char argbuff[s32];
                    again:
                    idx++;
                    sprintf(argbuff, "arg%d", idx);
                    for(auto it = m->par.begin(); it != --m->par.end(); it++) if(cmp(it->name.c_str(), argbuff)) goto again;
                    m->par.back().name = argbuff;
                }
                next;
                if(is(Const)) {
                    m->isConst = true;
                    next;
                }
                if(is(Col)) {//emit initializer-list
                    next;
                    while(is(Ident)) {
                        next;
                        next;
                        if(!is(RParen)) {
                            list<string> unused;
                            parsevalue(unused);
                        }
                        next;
                        if(is(Comma)) next;
                    }
                } else if(is(Binary)) {
                    m->isNull = true;
                    next;
                    next;
                }
                if(is(LBrace)) {
                    m->isForward = false;
                    char* begin = lex->pos();
                    uint32_t s = 1;
                    while(s) {
                        next;
                        if(is(RBrace)) s--;
                        else if(is(LBrace)) s++;
                    }
                    char* tmp;
                    char* end = lex->pos()-1;
                    while(begin < end && ((*begin == ' ' || *begin == '\t') && *begin != '\n')) begin++;
                    if(*begin == '\n') begin++;
                    while(begin < end && ((*end == ' ' || *end == '\t') && *end != '\n')) end--;
                    if(*end == '\n') end++;
                    lex->slice(tmp, begin, end);
                    m->content = tmp;
                    delete[] tmp;
                } else m->isForward = true;
                ns->items.push_back(pair<ItemT, itemT*>(kItem_Function, m));
            } else {
                varT* v = new varT;
                v->parent = ns;
                v->name.swap(name);
                for(auto it = lmod.begin(); it != lmod.end(); it++) {
                    if(*it == "static") v->isStatic = true;
                    else if(*it == "mutable") v->isMutable = true;
                    else if(*it == "volatile") v->isVolatile = true;
                }
                v->itemType = kItem_Var;
                v->type = t;
                if(is(Col) || is(Binary)) {
                    next;
                    parsevalue(v->def);
                }
                v->sh = sh;
                ns->items.push_back(pair<ItemT, itemT*>(kItem_Var, v));
            }
        }
        next;
    }

    return true;
}

bool parsetype(typeT& t, bool ret, bool req) {
    bool once = false;
    while(isTMod(tok)) {
        once = true;
        t.lmod.push_back(ident);
        next;
    }

    //we need to look ahead (for constuctors, destructors, etc.)
    if(ret) {
        if(is(Tilde)) {
            return !once;
        } else if(is(Ident)) {
            lex->pushState();
            #pragma push_macro("next")
            #undef next
            Token peek = tok;
            if(peek == kT_Ident) peek = lex->next();
            while(1) {
                if(peek == kT_DCol) {
                    peek = lex->next();
                    if(peek == kT_Ident) peek = lex->next();
                    else break;
                } else break;
            }
            #pragma pop_macro("next")
            lex->popState();
            if(peek == kT_LParen) return !once;
        }
    }

    if(!parsens(t.type)) return false;
    if(!t.type.empty() && t.outer.empty())
        t.outer = *(--t.type.end());
    if(is(LCh)) {
        if(!parsechr(t)) return false;
    }
    list<string>* dest = (req)?&t.type:&t.rmod;
    while(is(Mul) || is(Const)) {
        if(is(Const)) {
            if(dest->back() == "const") return false;
        }
        dest->push_back(ident);
        next;
    }
    if(is(And)) {
        dest->push_back("&");
        next;
    }
    return true;
}

bool parsechr(typeT& t) {
    t.type.push_back("<");
    next;
    if(is(LCh)) return false;
    while(1) {
        if(!parsetype(t, false, true)) return false;
        if(tok != kT_Comma) break;
        else t.type.push_back(ident);
        next;
    };
    if(is(RCh)) {
        t.type.push_back(">");
        next;
        return true;
    }
    return false;
}

bool parsens(list<string>& t) {
    bool one = false;
    if(is(Ident)) {
        one = true;
        t.push_back(ident);
        next;
    } else if (is(Tilde)) {
        t.push_back(ident);
        next;
        if(is(Ident)) {
            t.push_back(ident);
            next;
            return true;
        } else return false;
    }

    while(1) {
        if(is(DCol)) {
            one = true;
            next;
            t.push_back("::");

            if(is(Ident)) {
                t.push_back(ident);
                next;
            } else if (is(Tilde)) {
                t.push_back(ident);
                next;
                if(is(Ident)) {
                    t.push_back(ident);
                    next;
                    break;
                }
                else return false;
            } else return false;
        } else break;
    }
    return one;
}

bool parselmodifier(list<string>& m) {
    while(isMod(tok) && tok != kT_Const) {
        m.push_back(ident);
        next;
    }
    if(is(Ident) || is(DCol) || is(Const) || is(Tilde)) return true;
    return false;
}
bool parsermodifier(list<string>& m) {
    if(is(Const)) {
        m.push_back(ident);
        next;
    }
    if(is(Binary)) {
        next;
        if(cmp(ident, "0")) next;
        else return false;
    }
    if(tok != kT_SCol && tok != kT_LBrace) return false;
    return true;
}
void filter(nsT* ns) {
    if(custom) {
        for(auto it = ns->items.begin(); it != ns->items.end();) {
            if(it->first == kItem_Namespace || it->first == kItem_Class || it->first == kItem_Struct) {filter((nsT*)it->second);it++;}
            else if(!custom(it->first, it->second)) {
                auto tit = it;
                it++;
                ns->items.erase(tit);
            } else it++;
        }
    }
}

bool parsevalue(list<string>& str) {
    if(is(RParen) || is(Comma)) return false;
    if(isCon(tok)) {//leaf
        str.push_back(ident);
        next;
        return true;
    }
    typeT tmp;
    amember:
    parsetype(tmp, false);
    str.insert(str.end(), tmp.type.begin(), tmp.type.end());
    if(is(Dot) || is(Arrow)) {
        str.push_back(ident);
        next;
        goto amember;
    }
    if(is(LParen)) {
        str.push_back("(");
        next;
        while(tok != kT_RParen) {
            if(!parsevalue(str)) return false;
            if(is(Comma)) {
                str.push_back(",");
                next;
            }
        }
        str.push_back(")");
        next;
    }
    return true;
}

bool parsetypedef(typedefB*& td, bool& func) {
    if(tok != kT_Typedef) return false;
    next;
    typeT type;
    if(!parsetype(type, true, false)) return false;
    if(is(LParen)) {
        func = true;
        td = new typedefF;
        typedefF* pt = (typedefF*)td;
        pt->ret = type;
        next;
        if(is(Ident)) {
            lex->pushState();
            #pragma push_macro("next")
            #undef next
            Token peek = lex->next();
            #pragma pop_macro("next")
            lex->popState();
            if(peek == kT_Mul) {
                pt->lmod = ident;
            } else pt->name.push_back(ident);
            next;
        }
        while(is(DCol) || is(Ident)) {
            pt->name.push_back(ident);
            next;
        }
        if(is(Mul)) {
            next;
            pt->name.push_back(ident);
            next;
        } else return false;
        if(is(RParen)) {
            next;
            if(is(LParen)) {
                next;
                while(tok != kT_RParen) {
                    typeT tmp;
                    if(!parsetype(tmp, false, false)) return false;
                    pt->par.push_back(tmp);
                    if(is(Comma)) next;
                }
                next;
                if(is(Const)) {
                    pt->rmod = ident;
                    next;
                }
                if(is(SCol)) {
                    return true;
                } else return false;
            } else return false;
        } else return false;
    } else if(is(Ident)) {
        func = false;
        td = new typedefT;
        typedefT* pt = (typedefT*)td;
        parsens(pt->name);
        pt->type = type;
        if(tok != kT_SCol) return false;
        return true;
    }
    return false;
}
bool parsecmdlargs(const uint32_t& argc, char** argv) {
    if(argc < 3) return false;
    for(uint32_t i = 1; i < argc; i++) {
        if(argv[i][0] == '-') {
            if(argv[i][1] == 'i') {
                if(argv[i][2] == 'f') ifile = argv[i]+3;               
                else return false;
            } else if(argv[i][1] == 'r') {
                if(argv[i][2] == 'r') iruler = argv[i]+3;
                else if(argv[i][2] == 'p') irulep = argv[i]+3;
                else return false;
            } else return false;
        } else return false;
    }
    return (ifile != "");
}
void loadrulefile(const string& f, map<string, string>& to) {
    char* rf;
    loadfile(f.c_str(), rf);
    if(!rf) return;
    char* c = rf;
    while(*c) {
        while(*c == '\t' || *c == '\n' || *c == ' ') c++;
        if(*c == '/' && *(c+1) == '/') {
            while(*c != '\n' && *c != 0) c++;
            if(!*c) break;
            c++;
            continue;
        }
        char* nh = c;
        while(*c != '\t' && *c != '{' && *c != '\n' && *c != ' ' && *c) c++;
        if(!*c) break;
        *c = 0;
        c++;

        while(*c == '\t' || *c == ' ') c++;
        if(!*c || *c == '\n') {
            break;
        }

        char* ah;
        if(*c == '{') {
            ah = c+1;
            uint32_t stack = 1;
            while(stack) {
                c++;
                if(*c == '}') stack--;
                else if(*c == '{') stack++;
                else if(!*c) goto end;
            }
            char old = *c;
            *c = 0;
            to.insert(pair<string,string>(nh, ah));
            *c = old;
            c++;
        } else {
            ah = c;
            while(*c && *c != '\n') c++;
            if(*c) c++;
            char old = *c;
            *c = 0;
            to.insert(pair<string,string>(nh, ah));
            *c = old;
        }
    }
    end:
    delete[] rf;
}
void replace(string& from, const string& what, const string& to) {
    uint32_t pos = 0;
    while((pos = from.find(what, pos)) <= from.length()) {
        from.replace(pos, what.length(), to);
        pos += to.length();
    }
}

void printns(nsT* ns, stringstream& ss, tabulator& tab) {    
    for(auto it = ns->items.begin(); it != ns->items.end(); it++) {
        if(it->first == kItem_Namespace) {
            nsT* p = (nsT*) it->second;
            ss << tab << "namespace ";ss << p->name;
            if(p->isForward) ss << ";\n";
            else {
                ss << " {\n";
                ++tab;
                printns(p, ss, tab);
                --tab;
                ss << tab << "};\n";
            }
        } else if(it->first == kItem_Class) {
            classT* p = (classT*) it->second;
            ss << tab << p->temp;
            if(!p->temp.empty()) ss << " ";
            ss << "class ";ss << p->lmod;
            if(!p->lmod.empty()) ss << " ";
            ss << p->name;
            if(p->isForward) ss << ";\n";
            else {
                if(!p->rmod.empty()) {
                    ss << " ";
                    for(auto jt = p->rmod.begin(); jt != p->rmod.end(); jt++) {
                        ss << *jt;
                        if(*jt == ":" || *jt == "public" || *jt == "private" || *jt == "protected") ss << " ";                        
                        if(*jt == ",") {ss << "\n\t";ss << tab;}
                    }
                }
                ss << " {\n";
                ++tab;
                printns(p, ss, tab);
                --tab;
                ss << tab << "};\n";
            }
        } else if(it->first == kItem_Struct) {
            structT* p = (structT*) it->second;
            ss << tab << p->temp;
            if(!p->temp.empty()) ss << " ";
            ss << "struct ";ss << p->name;
            if(p->isForward) ss << ";\n";
            else {
                if(!p->rmod.empty()) {
                    ss << " ";
                    for(auto jt = p->rmod.begin(); jt != p->rmod.end(); jt++) {
                        if(*jt == ":" || *jt == "public" || *jt == "private" || *jt == "protected") ss << " ";
                        ss << *jt;
                        if(*jt == ",") {ss << "\n\t";ss << tab;}
                    }
                }
                ss << " {\n";
                ++tab;
                printns(p, ss, tab);
                --tab;
                ss << tab << "};\n";
            }
        } else if(it->first == kItem_Union) {
            nsT* p = (nsT*) it->second;
            ss << tab << "union ";ss << p->name;
            if(p->isForward) ss << ";\n";
            else {
                ss << " {\n";
                ++tab;
                printns(p, ss, tab);
                --tab;
                ss << tab << "};\n";
            }
        } else if(it->first == kItem_Function) {
            methodT* p = (methodT*) it->second;            
            ss << tab;
            if(p->isStatic) ss << "static ";
            if(p->isVirtual) ss << "virtual ";
            if(p->isExplicit) ss << "explicit ";
            if(p->isVolatile) ss << "volatile ";
            if(p->isMutable) ss << "mutable ";
            if(p->isFriend) ss << "friend ";
            ss << p->ret;
            if(!p->ret.outer.empty()) ss << " ";
            ss << p->name << "(";
            for(auto jt = p->par.begin(); jt != p->par.end(); jt++) {
                if(jt != p->par.begin()) ss << ", ";
                ss << jt->type << " " << jt->name;
                if(!jt->def.empty()) {ss << " = ";ss << jt->def;}
            }
            ss << ")";
            if(p->isConst) ss << "const";
            if(p->isNull) ss << " = 0";
            if(p->isForward) ss << ";\n";
            else {
                ss << " {";
                if(!p->content.empty()) {
                    ss << "\n\t";ss << tab;
                    for(uint32_t i = 0; i < p->content.length(); i++) {
                        ss << p->content[i];
                        if(i < p->content.length()-1 && p->content[i+1] && p->content[i] == '\n') ss << tab << "\t";
                    }
                }
                ss << "}\n";
            }
        } else if(it->first == kItem_TypedefT) {
            typedefT* p = (typedefT*) it->second;
            ss << tab << "typedef ";ss << p->type << " ";ss << p->name << ";\n";
        } else if(it->first == kItem_TypedefF) {
            typedefF* p = (typedefF*) it->second;
            ss << tab << "typedef ";ss << p->ret << "(";
            ss << p->lmod;
            if(!p->lmod.empty() && !p->name.size() > 1) ss << " ";
            for(auto jt = p->name.begin(); jt != --p->name.end(); jt++) ss << *jt;
            ss << "*";ss << p->name.back() << ")(";
            for(auto jt = p->par.begin(); jt != p->par.end(); jt++) {
                if(jt != p->par.begin()) ss << ", ";
                ss << *jt;
            }
            ss << ")";
            if(!p->rmod.empty()) ss << " " << p->rmod;
            ss << ";\n";
        } else if(it->first == kItem_Shw) {
            --tab;
            ss << tab;
            ++tab;
            itemT* p = (itemT*) it->second;
            if(p->sh == kS_Public) ss << "public:\n";
            else if(p->sh == kS_Protected) ss << "protected:\n";
            else ss << "private:\n";
        } else if(it->first == kItem_Var) {
            varT* p = (varT*) it->second;
            ss << tab;
            if(p->isStatic) ss << "static ";
            if(p->isVolatile) ss << "volatile ";
            if(p->isMutable) ss << "mutable ";
            ss << p->type << " ";ss << p->name;
            if(!p->def.empty()) {
                ss << "\t";
                if(p->isStatic) ss << ":";
                else ss << "=";
                ss << "\t";
                ss << p->def;
            }
            ss << ";\n";
        } else if(it->first == kItem_Macro) {
            macroT* p = (macroT*) it->second;
            ss << tab << p->name << "(";
            for(auto jt = p->par.begin(); jt != p->par.end(); jt++) {
                if(jt != p->par.begin()) ss << ", ";
                ss << *jt;
            }
            ss << ")\n";
        } else if(it->first == kItem_Include) {
            ss << tab;
            itemT* p = (itemT*) it->second;
            ss << "#include ";ss << p->name << "\n";
        }
    }
}

void printfunc(methodT* m, stringstream& ss, tabulator& tab) {
    empty = false;
    ss << tab << m->ret;
    if(!m->ret.outer.empty()) ss << " ";
    for(auto it = route.begin(); it != route.end(); it++) ss << (*it)->name << "::";
    ss << m->name << "(";
    for(auto it = m->par.begin(); it != m->par.end(); it++) {
        if(it != m->par.begin()) ss << ", ";
        ss << it->type << " ";
        ss << it->name;
        if(!it->def.empty()) {ss << " = ";ss << it->def;}
    }
    ss << ") ";
    if(m->isConst) ss << "const ";
    ss << "{\n";
    string pcout = "cout";
    string pvout = "out";
    string ptwhole;
    {
        stringstream tmp;
        bool was = !m->ret.rmod.empty() && m->ret.rmod.back() == "&";
        if(was) m->ret.rmod.pop_back();
        tmp << m->ret;
        if(was) m->ret.rmod.push_back("&");
        ptwhole = tmp.str();
    }
    string pttype;
    {
        stringstream tmp;
        tmp << m->ret.type;
        pttype = tmp.str();
    }
    string pouter = m->ret.outer;

    ++tab;
    if(!m->ret.outer.empty() && m->ret.outer != "void") {
        auto it = m->ret.rmod.rbegin();
        for(;it != m->ret.rmod.rend() && *it != "*"; it++);
        if(it != m->ret.rmod.rend()) {
            ss << tab << ptwhole << " out = NULL;\n";
        } else {
            auto rit = rules_ret.find(ptwhole);
            if(rit != rules_ret.end()) {
                string str = rit->second;
                replace(str, COUT, pcout);
                replace(str, VOUT, pvout);
                replace(str, TTYPE, pttype);
                replace(str, TOUTER, pouter);
                replace(str, TWHOLE, ptwhole);

                ss << tab;
                for(uint32_t i = 0; i < str.length()-1; i++) {
                    if(str[i] == '\n' && str[i+1] != 0) {ss << "\n";ss << tab;}
                    else ss << str[i];
                }
                ss << str[str.length()-1];
            } else {
                ss << tab << ptwhole << " out;\n";
            }
        }
    }
    ss << tab << "cout << \"";ss << m->name << "(\";\n";
    for(auto it = m->par.begin(); it != m->par.end(); it++) {
        if(it != m->par.begin()) ss << tab << "cout << \", \";\n";
        string ptwhole;
        {
            stringstream tmp;
            bool was = !it->type.rmod.empty() && it->type.rmod.back() == "&";
            if(was) it->type.rmod.pop_back();
            tmp << it->type.type;
            if(was) it->type.rmod.push_back("&");
            ptwhole = tmp.str();
        }
        string pttype;
        {
            stringstream tmp;
            tmp << it->type.type;
            pttype = tmp.str();
        }
        string pouter = it->type.outer;
        auto jt = rules_print.find(ptwhole);
        if(jt != rules_print.end()) {
            string str = jt->second;
            replace(str, COUT, pcout);
            replace(str, VARG, it->name);
            replace(str, VOUT, pvout);
            replace(str, TWHOLE, ptwhole);
            replace(str, TOUTER, pouter);
            replace(str, TTYPE, pttype);
            ss << tab << str;
        } else {
            ss << tab << "cout << \""<< ptwhole <<"\";\n";
        }
    }
    ss << tab << "cout << \") -> \";\n";
    {
        auto it = rules_print.find(ptwhole);
        if(it != rules_print.end()) {
            string str = it->second;
            replace(str, COUT, pcout);
            replace(str, VARG, pvout);
            replace(str, VOUT, pvout);
            replace(str, TWHOLE, ptwhole);
            replace(str, TOUTER, pouter);
            replace(str, TTYPE, pttype);
            ss << tab << str;
        } else {
            ss << tab << "cout << \"type: " << ((!ptwhole.empty())?ptwhole:"void") << "\";\n";
        }
    }
    ss << tab << "cout << \"\\n\";\n";
    if(!m->ret.outer.empty() && m->ret.outer != "void") {
        ss << tab << "return out;\n";
    }
    --tab;
    ss << tab << "}\n\n";
}

void printmacr(macroT* m, stringstream& ss, tabulator& tab) {
    empty = false;
    ss << tab << m->name << "(";
    for(auto it = m->par.begin(); it != m->par.end(); it++) {
        if(it != m->par.begin()) ss << ", ";
        ss << *it;
    }
    ss << ")";
    if(m->hasBody) {
        ss << " {\n";
        ss << tab << "\treturn 0;\n";
        ss << tab << "}\n\n";
    } else ss << "\n\n";
}

void stubns(nsT* ns, stringstream& ss, tabulator& tab) {
    for(auto mit = ns->items.begin(); mit != ns->items.end(); mit++) {
        if(mit->first == kItem_Class) {
            route.push_back((nsT*)mit->second);
            stubns((nsT*)mit->second, ss, tab);
            route.pop_back();
            continue;
        } else if(mit->first == kItem_Struct) {
            route.push_back((nsT*)mit->second);
            stubns((nsT*)mit->second, ss, tab);
            route.pop_back();
            continue;
        } else if(mit->first == kItem_Namespace) {
            ss << tab << "namespace ";
            ss << mit->second->name << "{\n";
            ++tab;
            stubns((nsT*)mit->second, ss, tab);
            --tab;
            ss << tab << "}\n";
            continue;
        }
        if(!define(mit->first, mit->second)) continue;
        empty = false;
        if(mit->first == kItem_Macro) {
            printmacr((macroT*)mit->second, ss, tab);
        } else if(mit->first == kItem_Function) {
            printfunc((methodT*)mit->second, ss, tab);
        }
    }
}

void gen(nsT* ns) {
    stringstream ss;    
    tabulator tab;
    printns(ns, ss, tab);
    string tmps = ifile.substr(0,ifile.find_last_of('.'));

    string hxx = tmps;
    hxx+="Stub.hxx";

    ofstream f;
    f.open("out/"+hxx);
    f << ss.str();
    f.close();

    stringstream gs;
    bool gempty = true;
    for(auto it = ns->items.begin(); it != ns->items.end(); it++) {
        ss.str("");
        ss << "#include <" << ifile << ">\n";
        ss << "#include <iostream>\n";
        ss << "\nusing namespace std;\n\n";
        if(it->second->isForward) continue;
        empty = true;
        if(it->second->itemType == kItem_Namespace) {
            ss << "namespace ";
            ss << it->second->name << " {\n";
            ++tab;
            stubns((nsT*)it->second, ss, tab);
            --tab;
            ss << "}\n";
        } else if(it->second->itemType == kItem_Class) {
            route.push_back((nsT*)it->second);
            stubns((nsT*)it->second, ss, tab);
            route.pop_back();
        } else if(it->second->itemType == kItem_Struct) {
            route.push_back((nsT*)it->second);
            stubns((nsT*)it->second, ss, tab);
            route.pop_back();
        } else if(it->second->itemType == kItem_Function) {
            define(it->first, it->second);
            printfunc((methodT*)it->second, gs, tab);
            if(!empty) gempty = false;
            continue;
        } else if(it->second->itemType == kItem_Macro) {
            define(it->first, it->second);
            printmacr((macroT*)it->second, gs, tab);
            if(!empty) gempty = false;
            continue;
        } else continue;

        if(empty) continue;

        stringstream name;
        name << it->second->name << "Stub.cxx";

        f.open("out/"+name.str());
        f << ss.str();
        f.close();
    }

    if(!gempty) {
        f.open("out/_globalScope.cxx");
        f << gs.str();
        f.close();
    }
}
