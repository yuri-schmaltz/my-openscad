# OpenSCAD Bridge for Blender 5.x+

Addon para Blender 5.x+ que implementa um fluxo OpenSCAD-like dentro do Blender.

## Funcionalidades entregues

- Importacao de arquivo `.scad` para Text datablock.
- Parser OpenSCAD subset com suporte a:
  - `cube()`, `sphere()`, `cylinder()`
  - `translate()`, `rotate()`, `scale()`
  - `union()`, `difference()`, `intersection()`
  - `color()`
  - `include <...>;`, `include "...";`, `use <...>;`, `use "...";`
  - `module nome(params) { ... }` e chamada de modulo
  - `function nome(params)=expr;` e chamadas em argumentos
  - expressoes aritmeticas com `+`, `-`, `*`, `/`, `%` e parenteses
  - comparacoes/logica: `<`, `>`, `<=`, `>=`, `==`, `!=`, `&&`, `||`, `!`
  - `if (...) { ... } else { ... }`
  - `let(...) expr` em expressoes e atribuicao local `x = expr;`
  - operador ternario: `cond ? a : b`
  - indexacao em vetores/listas: `v[i]`, incluindo encadeamento `v[i][j]`
  - `for (i=[ini:fim]) { ... }` e `for (i=[ini:passo:fim]) { ... }`
  - list comprehension: `[for (i=[ini:fim]) expr]` e com filtro: `[for (i=[...]) if (condition) expr]`
  - funcoes built-in: `echo(...)`, `min()`, `max()`, `abs()`, `len()`, `str()`, `lookup()`, `round()`, `floor()`, `ceil()`, `pow()`
  - `hull()` e `minkowski()` com fallback aproximado para uniao no backend Blender
- Preview de geometria em colecao dedicada `OpenSCAD Preview`.
- Render com aplicacao opcional de boolean modifiers.
- Export de mesh selecionada para script `.scad` via `polyhedron()`.
- Painel no View3D e Text Editor.

## Instalacao

1. Zip a pasta `blender_openscad_addon`.
2. Blender > Edit > Preferences > Add-ons > Install...
3. Selecione o zip e habilite o addon.

## Uso rapido

1. Abra a aba `OpenSCAD` na Sidebar do View3D.
2. Clique `Import SCAD` e selecione um arquivo.
3. Clique `Preview` para gerar geometria.
4. Clique `Render` para aplicar booleanos.
5. Selecione objeto e clique `Export SCAD` para gerar script.

## Exemplos e smoke test

- Exemplos SCAD com `include/use` e `module` estao em `tests/`.
- Para smoke test do parser/evaluator (fora do Blender):

```bash
python blender_openscad_addon/tests/test_parser_eval.py
```

## Limites desta versao

Este pacote entrega uma base funcional, mas nao implementa 100% da linguagem e do engine do OpenSCAD original (ex.: parser completo, todas as funcoes builtin, semantica completa de expressoes, caching, kernel CGAL/manifold, validacao completa de semanticas e paridade total de CLI).

## Roadmap para paridade ampliada

- Parser completo da gramatica OpenSCAD.
- Suporte a includes/use e resolucao de paths.
- Sistema de parametros, funcoes e modulos do usuario.
- Executor semantico completo com escopo e avaliacoes lazy.
- Backend CSG robusto com estrategia exata para booleans complexos.
- Suite de regressao com corpus de testes OpenSCAD.
