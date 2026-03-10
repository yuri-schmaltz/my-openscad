from pathlib import Path
import sys

ADDON_ROOT = Path(__file__).resolve().parents[1]
if str(ADDON_ROOT) not in sys.path:
  sys.path.insert(0, str(ADDON_ROOT))

from core.parser import parse_scad
from core.evaluator import evaluate_program


def run_smoke(source_file: Path) -> int:
  src = source_file.read_text(encoding="utf-8")
  program = parse_scad(src)
  items = evaluate_program(program, source_path=str(source_file))

  primitive_items = [i for i in items if i.node_type in {"primitive", "group", "boolean"}]
  print(f"{source_file.name}: {len(primitive_items)} item(ns) de avaliacao")
  return len(primitive_items)


def main():
  root = Path(__file__).resolve().parent
  count_include = run_smoke(root / "sample_main_include.scad")
  count_use = run_smoke(root / "sample_main_use.scad")

  if count_include <= 0 or count_use <= 0:
    raise SystemExit(1)

  print("Smoke parser/evaluator OK")


if __name__ == "__main__":
  main()
