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
  count_functions = run_smoke(root / "sample_main_functions.scad")
  count_if_let = run_smoke(root / "sample_if_let.scad")
  count_for_ternary_index = run_smoke(root / "sample_for_ternary_index.scad")
  count_comprehension = run_smoke(root / "sample_comprehension.scad")
  count_comprehension_filter = run_smoke(root / "sample_comprehension_filter.scad")
  count_echo_debug = run_smoke(root / "sample_echo_debug.scad")
  count_hull_minkowski = run_smoke(root / "sample_hull_minkowski.scad")

  if (
    count_include <= 0
    or count_use <= 0
    or count_functions <= 0
    or count_if_let <= 0
    or count_for_ternary_index <= 0
    or count_comprehension <= 0
    or count_comprehension_filter <= 0
    or count_echo_debug <= 0
    or count_hull_minkowski <= 0
  ):
    raise SystemExit(1)

  print("Smoke parser/evaluator OK")


if __name__ == "__main__":
  main()
