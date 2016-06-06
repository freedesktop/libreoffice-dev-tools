#include <fstream>
#include <iostream>
#include <set>
#include <sstream>

#include <clang/AST/ASTConsumer.h>
#include <clang/AST/ASTContext.h>
#include <clang/AST/RecursiveASTVisitor.h>
#include <clang/Rewrite/Core/Rewriter.h>
#include <clang/Tooling/CommonOptionsParser.h>
#include <clang/Tooling/Tooling.h>

class RenameRewriter : public clang::Rewriter
{
    /// Old names -> new names map.
    std::map<std::string, std::string> maNameMap;
    bool mbDump;

public:
    RenameRewriter(const std::map<std::string, std::string>& rNameMap, bool bDump)
        : maNameMap(rNameMap),
          mbDump(bDump)
    {
    }

    const std::map<std::string, std::string>& getNameMap()
    {
        return maNameMap;
    }

    bool getDump()
    {
        return mbDump;
    }
};

class RenameVisitor : public clang::RecursiveASTVisitor<RenameVisitor>
{
    RenameRewriter& mrRewriter;
    // A set of handled locations, so in case a location would be handled
    // multiple times due to macro usage, we only do the rewrite once.
    // Otherwise an A -> BA replacement would be done twice.
    std::set<clang::SourceLocation> maHandledLocations;

    void RewriteText(clang::SourceLocation aStart, unsigned nLength, const std::string& rOldName, const std::string& rPrefix = std::string())
    {
        std::string aOldName = rOldName;
        if (!rPrefix.empty())
            // E.g. rOldName is '~C' and rPrefix is '~', then check if 'C' is to be renamed.
            aOldName = aOldName.substr(rPrefix.size());
        const std::map<std::string, std::string>::const_iterator it = mrRewriter.getNameMap().find(aOldName);
        if (it != mrRewriter.getNameMap().end())
        {
            if (aStart.isMacroID())
                /*
                 * int foo(int x);
                 * #define FOO(a) foo(a)
                 * FOO(aC.nX); <- Handles this.
                 */
                aStart = mrRewriter.getSourceMgr().getSpellingLoc(aStart);
            if (maHandledLocations.find(aStart) == maHandledLocations.end())
            {
                std::string aNewName = it->second;
                if (!rPrefix.empty())
                    // E.g. aNewName is 'D' and rPrefix is '~', then rename to '~D'.
                    aNewName = rPrefix + aNewName;
                mrRewriter.ReplaceText(aStart, nLength, aNewName);
                maHandledLocations.insert(aStart);
            }
        }
    }

public:
    explicit RenameVisitor(RenameRewriter& rRewriter)
        : mrRewriter(rRewriter)
    {
    }

    // Data member names.

    /*
     * class C
     * {
     * public:
     *     int nX; <- Handles this declaration.
     * };
     */
    bool VisitFieldDecl(clang::FieldDecl* pDecl)
    {
        // Qualified name includes "C::" as a prefix, normal name does not.
        std::string aName = pDecl->getQualifiedNameAsString();
        RewriteText(pDecl->getLocation(), pDecl->getNameAsString().length(), aName);
        return true;
    }

    /*
     * class C
     * {
     * public:
     *     static const int aS[]; <- Handles e.g. this declaration;
     * };
     */
    bool VisitVarDecl(clang::VarDecl* pDecl)
    {
        std::string aName = pDecl->getQualifiedNameAsString();
        RewriteText(pDecl->getLocation(), pDecl->getNameAsString().length(), aName);

        /*
         * C* pC = 0;
         * ^ Handles this.
         */
        clang::QualType pType = pDecl->getType();
        const clang::RecordDecl* pRecordDecl = pType->getPointeeCXXRecordDecl();
        if (pRecordDecl)
        {
            aName = pRecordDecl->getNameAsString();
            RewriteText(pDecl->getTypeSpecStartLoc(), pRecordDecl->getNameAsString().length(), aName);
        }
        return true;
    }

    /*
     * C::C()
     *     : nX(0) <- Handles this initializer.
     * {
     * }
     */
    bool VisitCXXConstructorDecl(clang::CXXConstructorDecl* pDecl)
    {
        for (clang::CXXConstructorDecl::init_const_iterator itInit = pDecl->init_begin(); itInit != pDecl->init_end(); ++itInit)
        {
            const clang::CXXCtorInitializer* pInitializer = *itInit;

            // Ignore implicit initializers.
            if (pInitializer->getSourceOrder() == -1)
                continue;

            if (const clang::FieldDecl* pFieldDecl = pInitializer->getAnyMember())
            {
                std::string aName = pFieldDecl->getQualifiedNameAsString();
                RewriteText(pInitializer->getSourceLocation(), pFieldDecl->getNameAsString().length(), aName);
            }
        }

        std::string aName = pDecl->getNameAsString();
        /*
         * Foo::Foo(...) {}
         * ^~~ Handles this.
         */
        RewriteText(pDecl->getLocStart(), pDecl->getNameAsString().length(), aName);

        /*
         * Foo::Foo(...) {}
         *      ^~~ Handles this.
         */
        RewriteText(pDecl->getLocation(), pDecl->getNameAsString().length(), aName);

        return true;
    }

    bool VisitCXXDestructorDecl(clang::CXXDestructorDecl* pDecl)
    {
        std::string aName = pDecl->getNameAsString();
        std::string aPrefix("~");
        if (pDecl->isThisDeclarationADefinition())
            /*
             * Foo::~Foo(...) {}
             * ^~~ Handles this.
             */
            RewriteText(pDecl->getLocStart(), pDecl->getNameAsString().length() - aPrefix.size(), aName.substr(aPrefix.size()));

        /*
         * Foo::~Foo(...) {}
         *      ^~~ Handles this.
         */
        RewriteText(pDecl->getLocation(), pDecl->getNameAsString().length(), aName, aPrefix);

        return true;
    }

    /*
     * C aC;
     * aC.nX = 1; <- Handles e.g. this...
     * int y = aC.nX; <- ...and this.
     */
    bool VisitMemberExpr(clang::MemberExpr* pExpr)
    {
        if (clang::ValueDecl* pDecl = pExpr->getMemberDecl())
        {
            std::string aName = pDecl->getQualifiedNameAsString();
            RewriteText(pExpr->getMemberLoc(), pDecl->getNameAsString().length(), aName);
        }
        return true;
    }

    /*
     * class C
     * {
     * public:
     *     static const int aS[];
     *     static const int* getS() { return aS; } <- Handles this.
     * };
     */
    bool VisitDeclRefExpr(clang::DeclRefExpr* pExpr)
    {
        if (clang::ValueDecl* pDecl = pExpr->getDecl())
        {
            std::string aName = pDecl->getQualifiedNameAsString();
            RewriteText(pExpr->getLocation(), pDecl->getNameAsString().length(), aName);
        }
        return true;
    }

    // Member function names.

    /*
     * class C
     * {
     * public:
     *     foo(); <- Handles this.
     * };
     *
     * C::foo() <- And this.
     * {
     * }
     *
     * ...
     *
     * aC.foo(); <- And this.
     */
    bool VisitCXXMethodDecl(const clang::CXXMethodDecl* pDecl)
    {
        std::string aName = pDecl->getQualifiedNameAsString();
        RewriteText(pDecl->getLocation(), pDecl->getNameAsString().length(), aName);
        return true;
    }

    // Class names.

    /*
     * class C <- Handles this.
     * {
     * };
     */
    bool VisitCXXRecordDecl(const clang::CXXRecordDecl* pDecl)
    {
        std::string aName = pDecl->getQualifiedNameAsString();
        RewriteText(pDecl->getLocation(), pDecl->getNameAsString().length(), aName);
        return true;
    }

    /*
     * ... new C(...); <- Handles this.
     */
    bool VisitCXXConstructExpr(const clang::CXXConstructExpr* pExpr)
    {
        if (const clang::CXXConstructorDecl* pDecl = pExpr->getConstructor())
        {
            std::string aName = pDecl->getNameAsString();
            RewriteText(pExpr->getLocation(), pDecl->getNameAsString().length(), aName);
        }
        return true;
    }

    /*
     * ... static_cast<const C*>(...) ...;
     *                       ^ Handles this...
     *
     * ... static_cast<const C&>(...) ...;
     *                       ^ ... and this.
     *
     * ... and the same for dynamic_cast<>().
     */
    bool handleCXXNamedCastExpr(clang::CXXNamedCastExpr* pExpr)
    {
        clang::QualType pType = pExpr->getType();
        const clang::RecordDecl* pDecl = pType->getPointeeCXXRecordDecl();
        if (!pDecl)
            pDecl = pType->getAsCXXRecordDecl();
        if (pDecl)
        {
            std::string aName = pDecl->getNameAsString();
            clang::SourceLocation aLocation = pExpr->getTypeInfoAsWritten()->getTypeLoc().getBeginLoc();
            RewriteText(aLocation, pDecl->getNameAsString().length(), aName);
        }
        return true;
    }

    bool VisitCXXStaticCastExpr(clang::CXXStaticCastExpr* pExpr)
    {
        return handleCXXNamedCastExpr(pExpr);
    }

    bool VisitCXXDynamicCastExpr(clang::CXXDynamicCastExpr* pExpr)
    {
        return handleCXXNamedCastExpr(pExpr);
    }
};

class RenameASTConsumer : public clang::ASTConsumer
{
    RenameRewriter& mrRewriter;

    std::string getNewName(const clang::FileEntry& rEntry)
    {
        std::stringstream ss;
        ss << rEntry.getName();
        ss << ".new-rename";
        return ss.str();
    }

public:
    RenameASTConsumer(RenameRewriter& rRewriter)
        : mrRewriter(rRewriter)
    {
    }

    virtual void HandleTranslationUnit(clang::ASTContext& rContext)
    {
        if (rContext.getDiagnostics().hasErrorOccurred())
            return;

        RenameVisitor aVisitor(mrRewriter);
        mrRewriter.setSourceMgr(rContext.getSourceManager(), rContext.getLangOpts());
        aVisitor.TraverseDecl(rContext.getTranslationUnitDecl());

        for (clang::Rewriter::buffer_iterator it = mrRewriter.buffer_begin(); it != mrRewriter.buffer_end(); ++it)
        {
            if (mrRewriter.getDump())
                it->second.write(llvm::errs());
            else
            {
                const clang::FileEntry* pEntry = rContext.getSourceManager().getFileEntryForID(it->first);
                if (!pEntry)
                    continue;
                std::string aNewName = getNewName(*pEntry);
#if (__clang_major__ == 3 && __clang_minor__ >= 6) || __clang_major__ > 3
                std::error_code aError;
                std::unique_ptr<llvm::raw_fd_ostream> pStream(new llvm::raw_fd_ostream(aNewName, aError, llvm::sys::fs::F_None));
                if (!aError)
#else
                std::string aError;
                std::unique_ptr<llvm::raw_fd_ostream> pStream(new llvm::raw_fd_ostream(aNewName.c_str(), aError, llvm::sys::fs::F_None));
                if (aError.empty())
#endif
                    it->second.write(*pStream);
            }
        }
    }
};

class RenameFrontendAction
{
    RenameRewriter& mrRewriter;

public:
    RenameFrontendAction(RenameRewriter& rRewriter)
        : mrRewriter(rRewriter)
    {
    }

#if (__clang_major__ == 3 && __clang_minor__ >= 6) || __clang_major__ > 3
    std::unique_ptr<clang::ASTConsumer> newASTConsumer()
    {
        return llvm::make_unique<RenameASTConsumer>(mrRewriter);
    }
#else
    clang::ASTConsumer* newASTConsumer()
    {
        return new RenameASTConsumer(mrRewriter);
    }
#endif
};

/// Parses rCsv and puts the first two column of it into rNameMap.
static bool parseCsv(const std::string& rCsv, std::map<std::string, std::string>& rNameMap)
{
    std::ifstream aStream(rCsv);
    if (!aStream.is_open())
    {
        std::cerr << "parseCsv: failed to open " << rCsv << std::endl;
        return false;
    }

    std::string aLine;
    while (std::getline(aStream, aLine))
    {
        std::stringstream ss(aLine);
        std::string aOldName;
        std::getline(ss, aOldName, ',');
        if (aOldName.empty())
        {
            std::cerr << "parseCsv: first column is empty for line '" << aLine << "'" << std::endl;
            return false;
        }
        std::string aNewName;
        std::getline(ss, aNewName, ',');
        if (aNewName.empty())
        {
            std::cerr << "parseCsv: second column is empty for line '" << aLine << "'" << std::endl;
            return false;
        }
        rNameMap[aOldName] = aNewName;
    }

    aStream.close();
    return true;
}

int main(int argc, const char** argv)
{
    llvm::cl::OptionCategory aCategory("rename options");
    llvm::cl::opt<std::string> aOldName("old-name",
                                        llvm::cl::desc("Old, qualified name (Class::member)."),
                                        llvm::cl::cat(aCategory));
    llvm::cl::opt<std::string> aNewName("new-name",
                                        llvm::cl::desc("New, non-qualified name (without Class::)."),
                                        llvm::cl::cat(aCategory));
    llvm::cl::opt<std::string> aCsv("csv",
                                    llvm::cl::desc("Path to a CSV file, containing multiple renames -- seprator must be a comma (,)."),
                                    llvm::cl::cat(aCategory));
    llvm::cl::opt<bool> bDump("dump",
                              llvm::cl::desc("Dump output on the console instead of writing to .new files."),
                              llvm::cl::cat(aCategory));
    clang::tooling::CommonOptionsParser aParser(argc, argv, aCategory);

    std::map<std::string, std::string> aNameMap;
    if (!aOldName.empty() && !aNewName.empty())
        aNameMap[aOldName] = aNewName;
    else if (!aCsv.empty())
    {
        if (!parseCsv(aCsv, aNameMap))
            return 1;
    }
    else
    {
        std::cerr << "either -old-name + -new-name or -csv is required." << std::endl;
        return 1;
    }

    clang::tooling::ClangTool aTool(aParser.getCompilations(), aParser.getSourcePathList());

    RenameRewriter aRewriter(aNameMap, bDump);
    RenameFrontendAction aAction(aRewriter);
    std::unique_ptr<clang::tooling::FrontendActionFactory> pFactory = clang::tooling::newFrontendActionFactory(&aAction);
    return aTool.run(pFactory.get());
}

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
