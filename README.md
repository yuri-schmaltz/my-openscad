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

## Empacotamento

- Gerar zip instalavel do addon:

  python scripts/package_addon.py --clean

- Saida esperada:

  dist/openscad_bridge-<versao>.zip

## Versionamento

- Atualizar versao de forma sincronizada no addon:

  python scripts/set_addon_version.py 0.2.0

Este comando atualiza:

- blender_openscad_addon/blender_manifest.toml
- blender_openscad_addon/__init__.py

## CI

Pipeline em GitHub Actions:

- .github/workflows/addon-ci.yml

Jobs atuais:

- lint: analise estatica com Ruff (checks de logica)
- unit-tests: smoke + suite extensa + build do zip
- blender-headless: instala Blender no Windows e roda teste de integracao

## Release

Workflow de release:

- .github/workflows/release.yml

Fluxo:

1. Atualize versao com scripts/set_addon_version.py.
2. Commit e push.
3. Crie e envie a tag no formato vMAJOR.MINOR.PATCH.
4. O workflow gera o zip e publica no GitHub Release.

Exemplo:

git tag v0.2.0
git push origin v0.2.0

### Release assistido (manual)

Workflow:

- .github/workflows/release-assist.yml

Uso:

1. Execute o workflow manualmente em Actions.
2. Informe `version` (ex.: `0.2.0`) e `target_branch` (ex.: `master`).
3. O workflow atualiza versao, cria commit, cria tag `v0.2.0` e faz push.
4. Em seguida, o workflow de release por tag publica automaticamente o zip.

## Instalacao do Addon

1. Compacte a pasta blender_openscad_addon em .zip.
2. No Blender: Edit > Preferences > Add-ons > Install.
3. Selecione o zip e habilite o addon.
