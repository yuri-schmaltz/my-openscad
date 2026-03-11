from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
import sys

ADDON_ROOT = Path(__file__).resolve().parents[1]
if str(ADDON_ROOT) not in sys.path:
  sys.path.insert(0, str(ADDON_ROOT))

from core.ast import ModifierStmt, ModuleCall, TextPrimitive, ImportStmt
from core.evaluator import evaluate_program
from core.parser import ParseError, parse_scad
from core.tokenizer import TokenError, tokenize


def _eval_source(source: str):
  program = parse_scad(source)
  return evaluate_program(program)


def _flatten(items):
  out = []

  def walk(item):
    out.append(item)
    for ch in item.children:
      walk(ch)

  for it in items:
    walk(it)
  return out


class TestTokenizerExtensive(unittest.TestCase):
  def test_accepts_special_identifiers_and_modifiers(self):
    src = "$fn=32; #cube([1,2,3]);"
    toks = tokenize(src)
    values = [t.value for t in toks if t.kind != "eof"]
    self.assertIn("$fn", values)
    self.assertIn("#", values)

  def test_handles_all_boolean_operators(self):
    src = "a==b; a!=b; a<=b; a>=b; a&&b; a||b;"
    toks = tokenize(src)
    values = [t.value for t in toks]
    for op in ["==", "!=", "<=", ">=", "&&", "||"]:
      self.assertIn(op, values)

  def test_rejects_invalid_token(self):
    with self.assertRaises(TokenError):
      tokenize("cube([1,2,3]) @")


class TestParserExtensive(unittest.TestCase):
  def test_parses_modifier_text_import(self):
    src = '#text("abc", size=4); import("x.stl");'
    prog = parse_scad(src)
    self.assertEqual(len(prog.statements), 2)
    self.assertIsInstance(prog.statements[0], ModifierStmt)
    self.assertIsInstance(prog.statements[0].body, TextPrimitive)
    self.assertIsInstance(prog.statements[1], ImportStmt)

  def test_parses_module_call_with_body_for_children(self):
    src = "wrap(){ cube([1,1,1]); sphere(1); }"
    prog = parse_scad(src)
    self.assertEqual(len(prog.statements), 1)
    self.assertIsInstance(prog.statements[0], ModuleCall)
    self.assertEqual(len(prog.statements[0].body), 2)

  def test_raises_parse_error_on_missing_delimiter(self):
    with self.assertRaises(ParseError):
      parse_scad("cube([1,2,3)")


class TestEvaluatorExtensive(unittest.TestCase):
  def test_special_constants_and_defaults(self):
    src = "echo(PI,pi,$fa,$fs,$fn); x=undef; echo(is_undef(x));"
    buf = io.StringIO()
    with redirect_stdout(buf):
      _eval_source(src)
    out = buf.getvalue()
    self.assertIn("3.141592653589793", out)
    self.assertIn("12.0", out)
    self.assertIn("2.0", out)
    self.assertIn("0.0", out)
    self.assertIn("true", out)

  def test_chr_ord_search(self):
    src = 'echo(chr(65), ord("A"), search(2,[1,2,2,3]), search("ana","banana"));'
    buf = io.StringIO()
    with redirect_stdout(buf):
      _eval_source(src)
    out = buf.getvalue()
    self.assertIn('"A"', out)
    self.assertIn("65.0", out)
    self.assertIn("[1.0, 2.0]", out)
    self.assertIn("[1.0, 3.0]", out)

  def test_assert_false_reports_but_does_not_crash(self):
    src = 'assert(1==0, "falhou"); cube([1,1,1]);'
    buf = io.StringIO()
    with redirect_stdout(buf):
      items = _eval_source(src)
    out = buf.getvalue()
    self.assertIn("ASSERT FAILED", out)
    flat = _flatten(items)
    self.assertTrue(any(it.node_type == "primitive" for it in flat))

  def test_children_and_children_index(self):
    src = (
      "module wrap(){ echo($children); children(1); } "
      "wrap(){ cube([1,1,1]); sphere(1); }"
    )
    buf = io.StringIO()
    with redirect_stdout(buf):
      items = _eval_source(src)
    out = buf.getvalue()
    self.assertIn("2.0", out)
    flat = _flatten(items)
    kinds = [it.primitive.kind for it in flat if it.primitive is not None]
    self.assertIn("sphere", kinds)
    self.assertNotIn("cube", kinds)

  def test_prefix_star_disables_node(self):
    src = "*cube([1,1,1]); sphere(1);"
    items = _flatten(_eval_source(src))
    kinds = [it.primitive.kind for it in items if it.primitive is not None]
    self.assertIn("sphere", kinds)
    self.assertNotIn("cube", kinds)

  def test_text_import_and_polyhedron_eval_nodes(self):
    src = 'text("oi", size=3); import("/tmp/a.svg"); polyhedron(points=[[0,0,0],[1,0,0],[0,1,0],[0,0,1]], faces=[[0,1,2],[0,1,3],[1,2,3],[0,2,3]]);'
    items = _flatten(_eval_source(src))
    node_types = [it.node_type for it in items]
    self.assertIn("primitive", node_types)
    self.assertIn("import", node_types)
    self.assertIn("polyhedron", node_types)
    prim_kinds = [it.primitive.kind for it in items if it.primitive is not None]
    self.assertIn("text", prim_kinds)
    self.assertIn("import", prim_kinds)
    self.assertIn("polyhedron", prim_kinds)

  def test_transforms_include_mirror_resize_multmatrix(self):
    src = (
      "mirror([1,0,0]) resize([3,4,5], auto=[true,true,true]) "
      "multmatrix([[1,0,0,0],[0,1,0,0],[0,0,1,0]]) cube([1,1,1]);"
    )
    items = _flatten(_eval_source(src))
    prim = [it for it in items if it.primitive is not None and it.primitive.kind == "cube"]
    self.assertEqual(len(prim), 1)
    chain_kinds = [k for k, _ in prim[0].transform_chain]
    self.assertIn("mirror", chain_kinds)
    self.assertIn("resize", chain_kinds)
    self.assertIn("multmatrix", chain_kinds)

  def test_boolean_and_color_pipeline(self):
    src = "color([1,0,0,0.5]) union(){ cube([1,1,1]); sphere(1); }"
    items = _flatten(_eval_source(src))
    has_boolean = any(it.node_type == "boolean" for it in items)
    has_colored = any(it.color is not None for it in items)
    self.assertTrue(has_boolean)
    self.assertTrue(has_colored)

  def test_include_and_use_with_loader(self):
    with tempfile.TemporaryDirectory() as td:
      root = Path(td)
      lib = root / "lib.scad"
      lib.write_text(
        "module m(){ cube([1,1,1]); } function f(a)=a+1; x=7;",
        encoding="utf-8",
      )
      main = root / "main.scad"
      main.write_text(
        'include <lib.scad>; use <lib.scad>; m(); echo(f(1)); echo(x);',
        encoding="utf-8",
      )
      src = main.read_text(encoding="utf-8")
      buf = io.StringIO()
      with redirect_stdout(buf):
        program = parse_scad(src)
        items = evaluate_program(program, source_path=str(main))
      out = buf.getvalue()
      self.assertIn("2.0", out)
      self.assertIn("7.0", out)
      flat = _flatten(items)
      self.assertTrue(any(it.primitive is not None and it.primitive.kind == "cube" for it in flat))

  def test_linear_and_rotate_extrude_nodes(self):
    src = (
      "linear_extrude(height=5) square([1,2]);"
      "rotate_extrude(angle=270) polygon(points=[[0,0],[1,0],[1,1]]);"
    )
    items = _flatten(_eval_source(src))
    self.assertTrue(any(it.node_type == "extrude" for it in items))
    kinds = [it.primitive.kind for it in items if it.primitive is not None]
    self.assertIn("linear_extrude", kinds)
    self.assertIn("rotate_extrude", kinds)


if __name__ == "__main__":
  unittest.main()
