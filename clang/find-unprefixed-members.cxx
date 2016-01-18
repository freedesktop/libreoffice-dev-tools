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

class Context
{
    std::string m_aClassName;
    std::string m_aClassPrefix;
    std::set<std::string> m_aClassExcludedPrefixes;
    bool m_bPoco;

public:
    Context(const std::string& rClassName, const std::string& rClassPrefix, const std::string& rClassExcludedPrefix, bool bPoco)
        : m_aClassName(rClassName),
          m_aClassPrefix(rClassPrefix),
          m_bPoco(bPoco)
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
        if (m_bPoco)
            return rName.find("_") == 0;
        else
            return rName.find("m") == 0;
    }

    /// Checks if a static member has an expected name
    bool checkStatic(const std::string& rName) const
    {
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
};

class Visitor : public clang::RecursiveASTVisitor<Visitor>
{
    const Context m_rContext;
    /// List of qualified class name -- member name pairs.
    std::vector<std::pair<std::string, std::string>> m_aResults;
    /// List of qualified class names which have member functions.
    std::set<std::string> m_aFunctions;

public:
    Visitor(const Context& rContext)
        : m_rContext(rContext)
    {
    }

    const std::vector<std::pair<std::string, std::string>>& getResults()
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
        clang::RecordDecl* pRecord = pDecl->getParent();

        if (m_rContext.match(pRecord->getQualifiedNameAsString()))
        {
            std::string aName = pDecl->getNameAsString();
            if (!m_rContext.checkNonStatic(aName))
            {
                m_rContext.suggestNonStatic(aName);
                std::stringstream ss;
                ss << pDecl->getNameAsString() << "," << aName;
                m_aResults.push_back(std::make_pair(pRecord->getQualifiedNameAsString(), ss.str()));
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
        if (!pDecl->getQualifier())
            return true;

        clang::RecordDecl* pRecord = pDecl->getQualifier()->getAsType()->getAsCXXRecordDecl();

        if (pRecord && m_rContext.match(pRecord->getQualifiedNameAsString()))
        {
            std::string aName = pDecl->getNameAsString();
            if (!m_rContext.checkStatic(aName))
            {
                m_rContext.suggestStatic(aName);
                std::stringstream ss;
                ss << pDecl->getNameAsString() << "," << aName;
                m_aResults.push_back(std::make_pair(pRecord->getQualifiedNameAsString(), ss.str()));
            }
        }

        return true;
    }

    bool VisitCXXMethodDecl(clang::CXXMethodDecl* pDecl)
    {
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
    const Context& m_rContext;

public:
    ASTConsumer(const Context& rContext)
        : m_rContext(rContext)
    {
    }

    virtual void HandleTranslationUnit(clang::ASTContext& rContext)
    {
        if (rContext.getDiagnostics().hasErrorOccurred())
            return;

        Visitor aVisitor(m_rContext);
        aVisitor.TraverseDecl(rContext.getTranslationUnitDecl());
        const std::set<std::string>& rFunctions = aVisitor.getFunctions();
        const std::vector<std::pair<std::string, std::string>>& rResults = aVisitor.getResults();
        // Ignore missing prefixes in structs without member functions.
        bool bFound = false;
        for (const std::string& rFunction : rFunctions)
        {
            for (const std::pair<std::string, std::string>& rResult : rResults)
            {
                if (rResult.first == rFunction)
                {
                    std::cerr << rResult.first << "::" << rResult.second << std::endl;
                    bFound = true;
                }
            }
        }
        if (bFound)
            exit(1);
    }
};

class FrontendAction
{
    const Context& m_rContext;

public:
    FrontendAction(const Context& rContext)
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
    clang::tooling::CommonOptionsParser aParser(argc, argv, aCategory);

    clang::tooling::ClangTool aTool(aParser.getCompilations(), aParser.getSourcePathList());

    Context aContext(aClassName, aClassPrefix, aClassExcludedPrefix, bPoco);
    FrontendAction aAction(aContext);
    std::unique_ptr<clang::tooling::FrontendActionFactory> pFactory = clang::tooling::newFrontendActionFactory(&aAction);
    return aTool.run(pFactory.get());
}

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
