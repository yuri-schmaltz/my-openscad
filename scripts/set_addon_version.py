from __future__ import annotations

import argparse
import re
from pathlib import Path


def _validate_version(version: str) -> tuple[int, int, int]:
  m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)
  if not m:
    raise ValueError("Versao invalida. Use MAJOR.MINOR.PATCH, ex: 0.2.0")
  return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _update_manifest(manifest_path: Path, version: str) -> None:
  content = manifest_path.read_text(encoding="utf-8")
  pattern = r'(?m)^version\s*=\s*"[0-9]+\.[0-9]+\.[0-9]+"\s*\r?$'
  if re.search(pattern, content) is None:
    raise RuntimeError("Nao foi possivel atualizar version em blender_manifest.toml")
  updated = re.sub(pattern, f'version = "{version}"', content)
  manifest_path.write_text(updated, encoding="utf-8")


def _update_init(init_path: Path, version_tuple: tuple[int, int, int]) -> None:
  content = init_path.read_text(encoding="utf-8")
  new_tuple = f"({version_tuple[0]}, {version_tuple[1]}, {version_tuple[2]})"
  pattern = r'(?m)^\s*"version"\s*:\s*\([0-9]+,\s*[0-9]+,\s*[0-9]+\),\s*\r?$'
  if re.search(pattern, content) is None:
    raise RuntimeError("Nao foi possivel atualizar bl_info.version em __init__.py")
  updated = re.sub(pattern, f'  "version": {new_tuple},', content)
  init_path.write_text(updated, encoding="utf-8")


def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("version", help="Nova versao no formato MAJOR.MINOR.PATCH")
  parser.add_argument("--repo-root", default=".")
  args = parser.parse_args()

  version_tuple = _validate_version(args.version)
  repo_root = Path(args.repo_root).resolve()

  manifest_path = repo_root / "blender_openscad_addon" / "blender_manifest.toml"
  init_path = repo_root / "blender_openscad_addon" / "__init__.py"

  _update_manifest(manifest_path, args.version)
  _update_init(init_path, version_tuple)

  print(f"Versao atualizada para {args.version}")
  print(f"Manifest: {manifest_path}")
  print(f"Addon init: {init_path}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
