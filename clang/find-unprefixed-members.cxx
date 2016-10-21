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

class RenameResult
{
public:
    std::string m_aScope;
    std::string m_aOldName;
    std::string m_aNewName;

    RenameResult(const std::string& rScope, const std::string& rOldName, const std::string& rNewName)
        : m_aScope(rScope),
          m_aOldName(rOldName),
          m_aNewName(rNewName)
    {
    }
};

class Context
{
    std::string m_aClassName;
    std::string m_aClassPrefix;
    std::set<std::string> m_aClassExcludedPrefixes;
    bool m_bPoco;
    bool m_bYaml;
    std::string m_aPathPrefix;
    clang::ASTContext* m_pContext;

public:
    Context(const std::string& rClassName, const std::string& rClassPrefix, const std::string& rClassExcludedPrefix, bool bPoco, bool bYaml, const std::string& rPathPrefix)
        : m_aClassName(rClassName),
          m_aClassPrefix(rClassPrefix),
          m_bPoco(bPoco),
          m_bYaml(bYaml),
          m_aPathPrefix(rPathPrefix),
          m_pContext(nullptr)
    {
        std::stringstream aStream(rClassExcludedPrefix);
        std::string aExclude;
        while (std::getline(aStream, aExclude, ','))
            m_aClassExcludedPrefixes.insert(aExclude);
    }

    bool match(const std::string& rName) const
    {
        if (m_aClassName == "")
        {
            bool bRet = rName.find(m_aClassPrefix) == 0;
            if (bRet)
            {
                for (const std::string& rPrefix : m_aClassExcludedPrefixes)
                    if (rName.find(rPrefix) == 0)
                        return false;
                return true;
            }
            else
                return false;
        }
        else
            return rName == m_aClassName;
    }

    /// Checks if a non-static member has an expected name
    bool checkNonStatic(const std::string& rName) const
    {
        if (rName.empty())
            return true;

        if (m_bPoco)
            return rName.find("_") == 0;
        else
            return rName.find("m") == 0;
    }

    /// Checks if a static member has an expected name
    bool checkStatic(const std::string& rName) const
    {
        if (rName.empty())
            return true;

        if (m_bPoco)
            return !rName.empty() && rName[0] >= 'A' && rName[0] <= 'Z';
        else
            return rName.find("s") == 0;
    }

    /// Suggest a better name, provided that checkNonStatic() returned false.
    void suggestNonStatic(std::string& rName) const
    {
        if (m_bPoco)
            rName.insert(0, "_");
        else
            rName.insert(0, "m_");
    }

    /// Suggest a better name, provided that checkStatic() returned false.
    void suggestStatic(std::string& rName) const
    {
        if (m_bPoco)
        {
            if (!rName.empty())
                rName[0] = toupper(rName[0]);
        }
        else
            rName.insert(0, "s_");
    }

    void setASTContext(clang::ASTContext& rContext)
    {
        m_pContext = &rContext;
    }

    bool ignoreLocation(const clang::SourceLocation& rLocation)
    {
        bool bRet = false;

        clang::SourceLocation aLocation = m_pContext->getSourceManager().getExpansionLoc(rLocation);
        if (m_pContext->getSourceManager().isInSystemHeader(aLocation))
            bRet = true;
        else if (m_aPathPrefix.empty())
        {
            bRet = false;
        }
        else
        {
            const char* pName = m_pContext->getSourceManager().getPresumedLoc(aLocation).getFilename();
            bRet = std::string(pName).find(m_aPathPrefix) != 0;
        }

        return bRet;
    }

    bool getYaml() const
    {
        return m_bYaml;
    }
};

class Visitor : public clang::RecursiveASTVisitor<Visitor>
{
    Context m_rContext;
    /// List of qualified class name -- member name pairs.
    std::vector<RenameResult> m_aResults;
    /// List of qualified class names which have member functions.
    std::set<std::string> m_aFunctions;

public:
    Visitor(Context& rContext, clang::ASTContext& rASTContext)
        : m_rContext(rContext)
    {
        m_rContext.setASTContext(rASTContext);
    }

    const std::vector<RenameResult>& getResults()
    {
        return m_aResults;
    }

    const std::set<std::string>& getFunctions()
    {
        return m_aFunctions;
    }

    /*
     * class C
     * {
     * public:
     *     int nX; <- Handles this declaration.
     * };
     */
    bool VisitFieldDecl(clang::FieldDecl* pDecl)
    {
        if (m_rContext.ignoreLocation(pDecl->getLocation()))
            return true;

        clang::RecordDecl* pRecord = pDecl->getParent();

        if (m_rContext.match(pRecord->getQualifiedNameAsString()))
        {
            std::string aName = pDecl->getNameAsString();
            if (!m_rContext.checkNonStatic(aName))
            {
                m_rContext.suggestNonStatic(aName);
                m_aResults.push_back(RenameResult(pRecord->getQualifiedNameAsString(), pDecl->getNameAsString(), aName));
            }
        }

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
        if (m_rContext.ignoreLocation(pDecl->getLocation()))
            return true;

        if (!pDecl->getQualifier())
            return true;

        clang::RecordDecl* pRecord = pDecl->getQualifier()->getAsType()->getAsCXXRecordDecl();

        if (pRecord && m_rContext.match(pRecord->getQualifiedNameAsString()))
        {
            std::string aName = pDecl->getNameAsString();
            if (!m_rContext.checkStatic(aName))
            {
                m_rContext.suggestStatic(aName);
                m_aResults.push_back(RenameResult(pRecord->getQualifiedNameAsString(), pDecl->getNameAsString(), aName));
            }
        }

        return true;
    }

    bool VisitCXXMethodDecl(clang::CXXMethodDecl* pDecl)
    {
        if (m_rContext.ignoreLocation(pDecl->getLocation()))
            return true;

        if (clang::isa<clang::CXXConstructorDecl>(pDecl) || clang::isa<clang::CXXDestructorDecl>(pDecl))
            return true;

        clang::CXXRecordDecl* pRecord = pDecl->getParent();
        if (pRecord->getKindName().str() == "struct")
            return true;

        m_aFunctions.insert(pRecord->getQualifiedNameAsString());
        return true;
    }
};

class ASTConsumer : public clang::ASTConsumer
{
    Context& m_rContext;

public:
    ASTConsumer(Context& rContext)
        : m_rContext(rContext)
    {
    }

    virtual void HandleTranslationUnit(clang::ASTContext& rContext)
    {
        if (rContext.getDiagnostics().hasErrorOccurred())
            return;

        Visitor aVisitor(m_rContext, rContext);
        aVisitor.TraverseDecl(rContext.getTranslationUnitDecl());
        const std::set<std::string>& rFunctions = aVisitor.getFunctions();
        const std::vector<RenameResult>& rResults = aVisitor.getResults();
        // Ignore missing prefixes in structs without member functions.
        bool bFound = false;
        if (m_rContext.getYaml())
            std::cerr << "---" << std::endl;
        for (const std::string& rFunction : rFunctions)
        {
            for (const RenameResult& rResult : rResults)
            {
                if (rResult.m_aScope == rFunction)
                {
                    if (m_rContext.getYaml())
                    {
                        std::cerr << "- QualifiedName:  " << rResult.m_aScope << "::" << rResult.m_aOldName << std::endl;
                        std::cerr << "  NewName:        " << rResult.m_aNewName << std::endl;
                    }
                    else
                        std::cerr << rResult.m_aScope << "::" << rResult.m_aOldName << "," << rResult.m_aNewName << std::endl;
                    bFound = true;
                }
            }
        }
        if (m_rContext.getYaml())
            std::cerr << "..." << std::endl;
        if (bFound)
            exit(1);
    }
};

class FrontendAction
{
    Context& m_rContext;

public:
    FrontendAction(Context& rContext)
        : m_rContext(rContext)
    {
    }

#if (__clang_major__ == 3 && __clang_minor__ >= 6) || __clang_major__ > 3
    std::unique_ptr<clang::ASTConsumer> newASTConsumer()
    {
        return llvm::make_unique<ASTConsumer>(m_rContext);
    }
#else
    clang::ASTConsumer* newASTConsumer()
    {
        return new ASTConsumer(m_rContext);
    }
#endif
};

int main(int argc, const char** argv)
{
    llvm::cl::OptionCategory aCategory("find-unprefixed-members options");
    llvm::cl::opt<std::string> aClassName("class-name",
                                          llvm::cl::desc("Qualified name (namespace::Class)."),
                                          llvm::cl::cat(aCategory));
    llvm::cl::opt<std::string> aClassPrefix("class-prefix",
                                            llvm::cl::desc("Qualified name prefix (e.g. namespace::Cl)."),
                                            llvm::cl::cat(aCategory));
    llvm::cl::opt<std::string> aClassExcludedPrefix("class-excluded-prefix",
            llvm::cl::desc("Qualified name prefix to exclude (e.g. std::), has priority over the -class-prefix include."),
            llvm::cl::cat(aCategory));
    llvm::cl::opt<bool> bPoco("poco",
                              llvm::cl::desc("Expect Poco-style '_' instead of LibreOffice-style 'm_' as prefix."),
                              llvm::cl::cat(aCategory));
    llvm::cl::opt<bool> bYaml("yaml",
                              llvm::cl::desc("Output YAML instead of CSV, for clang-rename."),
                              llvm::cl::cat(aCategory));
    llvm::cl::opt<std::string> aPathPrefix("path-prefix",
                                            llvm::cl::desc("If not empty, ignore all source code paths not matching this prefix."),
                                            llvm::cl::cat(aCategory));
    clang::tooling::CommonOptionsParser aParser(argc, argv, aCategory);

    clang::tooling::ClangTool aTool(aParser.getCompilations(), aParser.getSourcePathList());

    Context aContext(aClassName, aClassPrefix, aClassExcludedPrefix, bPoco, bYaml, aPathPrefix);
    FrontendAction aAction(aContext);
    std::unique_ptr<clang::tooling::FrontendActionFactory> pFactory = clang::tooling::newFrontendActionFactory(&aAction);
    return aTool.run(pFactory.get());
}

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
