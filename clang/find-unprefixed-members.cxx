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

public:
    Context(const std::string& rClassName, const std::string& rClassPrefix)
        : m_aClassName(rClassName),
          m_aClassPrefix(rClassPrefix)
    {
    }

    bool match(const std::string& rName) const
    {
        if (m_aClassName == "")
            return rName.find(m_aClassPrefix) == 0;
        else
            return rName == m_aClassName;
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
            if (aName.find("m") != 0)
            {
                aName.insert(0, "m_");
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
            if (aName.find("s") != 0)
            {
                aName.insert(0, "s_");
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
    clang::tooling::CommonOptionsParser aParser(argc, argv, aCategory);

    if (aClassName.empty() && aClassPrefix.empty())
    {
        std::cerr << "-class-name or -class-prefix is required." << std::endl;
        return 1;
    }

    clang::tooling::ClangTool aTool(aParser.getCompilations(), aParser.getSourcePathList());

    Context aContext(aClassName, aClassPrefix);
    FrontendAction aAction(aContext);
    std::unique_ptr<clang::tooling::FrontendActionFactory> pFactory = clang::tooling::newFrontendActionFactory(&aAction);
    return aTool.run(pFactory.get());
}

/* vim:set shiftwidth=4 softtabstop=4 expandtab: */
