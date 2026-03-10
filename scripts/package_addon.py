from __future__ import annotations

import argparse
import fnmatch
import shutil
import zipfile
from pathlib import Path

try:
  import tomllib
except ModuleNotFoundError:  # pragma: no cover
  import tomli as tomllib  # type: ignore


def _load_manifest(repo_root: Path) -> dict:
  manifest_path = repo_root / "blender_openscad_addon" / "blender_manifest.toml"
  return tomllib.loads(manifest_path.read_text(encoding="utf-8"))


def _should_exclude(rel_path: str, patterns: list[str]) -> bool:
  rel = rel_path.replace("\\", "/")
  for pattern in patterns:
    p = pattern.replace("\\", "/")
    if p.endswith("/"):
      if rel.startswith(p):
        return True
      continue
    if fnmatch.fnmatch(rel, p):
      return True
  return False


def package_addon(repo_root: Path, output_dir: Path) -> Path:
  manifest = _load_manifest(repo_root)
  addon_id = manifest["id"]
  version = manifest["version"]
  exclude = list(manifest.get("build", {}).get("paths_exclude_pattern", []))

  addon_dir = repo_root / "blender_openscad_addon"
  if not addon_dir.exists():
    raise FileNotFoundError(f"Pasta do addon nao encontrada: {addon_dir}")

  output_dir.mkdir(parents=True, exist_ok=True)
  zip_path = output_dir / f"{addon_id}-{version}.zip"
  if zip_path.exists():
    zip_path.unlink()

  with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for path in addon_dir.rglob("*"):
      if path.is_dir():
        continue
      rel_inside_addon = path.relative_to(addon_dir).as_posix()
      if _should_exclude(rel_inside_addon, exclude):
        continue
      rel_zip = Path("blender_openscad_addon") / rel_inside_addon
      zf.write(path, rel_zip.as_posix())

  return zip_path


def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("--repo-root", default=".")
  parser.add_argument("--output-dir", default="dist")
  parser.add_argument("--clean", action="store_true")
  args = parser.parse_args()

  repo_root = Path(args.repo_root).resolve()
  output_dir = Path(args.output_dir).resolve()

  if args.clean and output_dir.exists():
    shutil.rmtree(output_dir)

  zip_path = package_addon(repo_root, output_dir)
  print(f"Pacote gerado: {zip_path}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
