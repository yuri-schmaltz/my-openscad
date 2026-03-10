#pragma once

#include <memory>
#include <optional>
#include <string>

#include "core/CSGNode.h"
#include "core/RenderVariables.h"
#include "core/SourceFile.h"
#include "core/Tree.h"

class CompileOrchestrator
{
public:
  struct ParsedDocument {
    std::shared_ptr<SourceFile> sourceFile;
    int parserErrorPos{-1};
    bool success{false};
  };

  struct InstantiatedRoot {
    std::shared_ptr<AbstractNode> absoluteRootNode;
    std::shared_ptr<AbstractNode> rootNode;
    std::shared_ptr<const FileContext> fileContext;
    std::optional<Location> extraRootLocation;
    std::string documentRoot;
  };

  struct CSGCompilation {
    std::shared_ptr<CSGNode> csgRoot;
    std::shared_ptr<CSGNode> normalizedRoot;
    std::shared_ptr<CSGProducts> rootProduct;
    std::shared_ptr<CSGProducts> highlightsProducts;
    std::shared_ptr<CSGProducts> backgroundProducts;
    bool openCsgDisabledByLimit{false};
  };

  ParsedDocument parsePreparedDocument(const std::string& fulltext,
                                       const std::string& filename) const;

  InstantiatedRoot instantiateRoot(const std::shared_ptr<SourceFile>& rootFile,
                                   const std::string& documentPath,
                                   const RenderVariables& renderVariables) const;

  CSGCompilation compileCSG(const Tree& tree, const std::shared_ptr<AbstractNode>& rootNode,
                            size_t openCsgLimit, bool emitCacheTelemetry) const;
};
