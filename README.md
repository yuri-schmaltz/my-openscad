# OpenSCAD Bridge Addon Repository

Este repositorio agora contem apenas o addon Blender e seus testes.

## Estrutura

- blender_openscad_addon/
: Codigo do addon, parser/evaluator OpenSCAD-like, operadores e UI.
- blender_openscad_addon/tests/
: Suites de teste (smoke, extensiva e integracao headless).
- COPYING
: Licenca do projeto.

## Requisitos

- Blender 5.x (testado com C:/Blender/blender.exe)
- Python 3.11+ para testes fora do Blender

## Testes

- Smoke parser/evaluator:

  python blender_openscad_addon/tests/test_parser_eval.py

- Suite extensa parser/evaluator:

  python blender_openscad_addon/tests/test_extensive_parser_evaluator.py

- Integracao end-to-end no Blender headless:

  python blender_openscad_addon/tests/test_blender_headless_integration.py

## Instalacao do Addon

1. Compacte a pasta blender_openscad_addon em .zip.
2. No Blender: Edit > Preferences > Add-ons > Install.
3. Selecione o zip e habilite o addon.
