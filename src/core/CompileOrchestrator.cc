#include "core/CompileOrchestrator.h"

#include <memory>
#include <string>

#include "core/BuiltinContext.h"
#include "core/CSGTreeEvaluator.h"
#include "core/Context.h"
#include "core/EvaluationSession.h"
#include "geometry/GeometryEvaluator.h"
#include "glview/preview/CSGTreeNormalizer.h"
#include "openscad.h"

CompileOrchestrator::ParsedDocument CompileOrchestrator::parsePreparedDocument(
  const std::string& fulltext, const std::string& filename) const
{
  const auto parseResult = parse_with_result(fulltext, filename, filename, false);

  ParsedDocument result;
  result.parserErrorPos = parseResult.parserErrorPos;
  result.success = parseResult.success;
  result.sourceFile = std::shared_ptr<SourceFile>(parseResult.file);
  return result;
}

CompileOrchestrator::InstantiatedRoot CompileOrchestrator::instantiateRoot(
  const std::shared_ptr<SourceFile>& rootFile, const std::string& documentPath,
  const RenderVariables& renderVariables) const
{
  InstantiatedRoot result;
  if (!rootFile) return result;

  AbstractNode::resetIndexCounter();

  EvaluationSession session{documentPath};
  ContextHandle<BuiltinContext> builtinContext{Context::create<BuiltinContext>(&session)};
  renderVariables.applyToContext(builtinContext);

  result.absoluteRootNode = rootFile->instantiate(*builtinContext, &result.fileContext);
  if (!result.absoluteRootNode) return result;

  const Location *nextLocation = nullptr;
  result.rootNode = find_root_tag(result.absoluteRootNode, &nextLocation);
  if (!result.rootNode) {
    result.rootNode = result.absoluteRootNode;
  }
  if (nextLocation) {
    result.extraRootLocation = *nextLocation;
    result.documentRoot = builtinContext->documentRoot();
  }

  return result;
}

CompileOrchestrator::CSGCompilation CompileOrchestrator::compileCSG(
  const Tree& tree, const std::shared_ptr<AbstractNode>& rootNode, size_t openCsgLimit,
  bool emitCacheTelemetry) const
{
  CSGCompilation result;
  if (!rootNode) return result;

  GeometryEvaluator geomevaluator(tree);
  CSGTreeEvaluator csgrenderer(tree, &geomevaluator);

  result.csgRoot = csgrenderer.buildCSGTree(*rootNode);
  if (emitCacheTelemetry) {
    geomevaluator.printCacheTelemetry();
  }

  const size_t normalizeLimit = 2ul * openCsgLimit;
  CSGTreeNormalizer normalizer(normalizeLimit);

  if (result.csgRoot) {
    result.normalizedRoot = normalizer.normalize(result.csgRoot);
    if (result.normalizedRoot) {
      result.rootProduct = std::make_shared<CSGProducts>();
      result.rootProduct->import(result.normalizedRoot);
    }
  }

  const auto& highlightTerms = csgrenderer.getHighlightNodes();
  if (!highlightTerms.empty()) {
    result.highlightsProducts = std::make_shared<CSGProducts>();
    for (const auto& highlightTerm : highlightTerms) {
      auto normalized = normalizer.normalize(highlightTerm);
      if (normalized) {
        result.highlightsProducts->import(normalized);
      }
    }
  }

  const auto& backgroundTerms = csgrenderer.getBackgroundNodes();
  if (!backgroundTerms.empty()) {
    result.backgroundProducts = std::make_shared<CSGProducts>();
    for (const auto& backgroundTerm : backgroundTerms) {
      auto normalized = normalizer.normalize(backgroundTerm);
      if (normalized) {
        result.backgroundProducts->import(normalized);
      }
    }
  }

  result.openCsgDisabledByLimit =
    result.rootProduct && (result.rootProduct->size() > openCsgLimit);

  return result;
}
