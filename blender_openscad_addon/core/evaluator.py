from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .ast import (
  Assignment,
  BinaryExpr,
  BooleanOp,
  ColorOp,
  EvalItem,
  ForStmt,
  FunctionCallExpr,
  FunctionDef,
  IfStmt,
  IndexExpr,
  IncludeStmt,
  LetExpr,
  ListComprehensionExpr,
  ModuleCall,
  ModuleDef,
  Primitive,
  Program,
  RangeExpr,
  RawCall,
  TernaryExpr,
  Transform,
  UnaryExpr,
  UseStmt,
  VarRef,
)
from .parser import parse_scad


@dataclass
class EvalContext:
  modules: dict[str, ModuleDef] = field(default_factory=dict)
  functions: dict[str, FunctionDef] = field(default_factory=dict)
  variables: dict[str, object] = field(default_factory=dict)
  source_path: str | None = None
  include_loader: Callable[[str], str] | None = None
  visited_includes: set[str] = field(default_factory=set)


def _eval_binary(op: str, left, right):
  if op == "+":
    return left + right
  if op == "-":
    return left - right
  if op == "*":
    return left * right
  if op == "/":
    return 0.0 if right == 0 else left / right
  if op == "%":
    return 0.0 if right == 0 else left % right
  if op == "<":
    return left < right
  if op == ">":
    return left > right
  if op == "<=":
    return left <= right
  if op == ">=":
    return left >= right
  if op == "==":
    return left == right
  if op == "!=":
    return left != right
  if op == "&&":
    return _truthy(left) and _truthy(right)
  if op == "||":
    return _truthy(left) or _truthy(right)
  return 0.0


def _truthy(value) -> bool:
  if isinstance(value, bool):
    return value
  if isinstance(value, (int, float)):
    return value != 0
  if isinstance(value, str):
    return len(value) > 0
  if isinstance(value, list):
    return len(value) > 0
  return bool(value)


def _as_number(value) -> float:
  if isinstance(value, bool):
    return 1.0 if value else 0.0
  if isinstance(value, (int, float)):
    return float(value)
  return 0.0


def _expand_range(start, end, step=None):
  s = int(_as_number(start))
  e = int(_as_number(end))
  if step is None:
    step_v = 1 if s <= e else -1
  else:
    step_v = int(_as_number(step))
    if step_v == 0:
      step_v = 1
  if step_v > 0:
    return list(range(s, e + 1, step_v))
  return list(range(s, e - 1, step_v))


def _iter_values(value):
  if isinstance(value, RangeExpr):
    return []
  if isinstance(value, list):
    return value
  return [value]


def _eval_function_call(expr: FunctionCallExpr, ctx: EvalContext):
  resolved_args = [_resolve_value(v, ctx.variables, ctx) for v in expr.args]

  if expr.name == "min":
    return min(resolved_args) if resolved_args else 0.0
  if expr.name == "max":
    return max(resolved_args) if resolved_args else 0.0
  if expr.name == "abs":
    return abs(float(resolved_args[0])) if resolved_args else 0.0

  fn = ctx.functions.get(expr.name)
  if fn is None:
    return 0.0

  bound_vars = dict(ctx.variables)
  for idx, (param_name, default_value) in enumerate(fn.params):
    if idx < len(resolved_args):
      bound_vars[param_name] = resolved_args[idx]
    elif default_value is not None:
      bound_vars[param_name] = _resolve_value(default_value, ctx.variables, ctx)
    else:
      bound_vars[param_name] = 0.0

  sub_ctx = EvalContext(
    modules=ctx.modules,
    functions=ctx.functions,
    variables=bound_vars,
    source_path=ctx.source_path,
    include_loader=ctx.include_loader,
    visited_includes=ctx.visited_includes,
  )
  return _resolve_value(fn.expr, sub_ctx.variables, sub_ctx)


def _resolve_value(value, variables: dict[str, object], ctx: EvalContext | None = None):
  if isinstance(value, VarRef):
    if value.name == "true":
      return True
    if value.name == "false":
      return False
    return variables.get(value.name, 0.0)
  if isinstance(value, UnaryExpr):
    val = _resolve_value(value.value, variables, ctx)
    if value.op == "-":
      return -float(val)
    if value.op == "!":
      return not _truthy(val)
    return float(val)
  if isinstance(value, BinaryExpr):
    left = _resolve_value(value.left, variables, ctx)
    right = _resolve_value(value.right, variables, ctx)
    return _eval_binary(value.op, _as_number(left), _as_number(right))
  if isinstance(value, TernaryExpr):
    cond = _resolve_value(value.condition, variables, ctx)
    if _truthy(cond):
      return _resolve_value(value.then_expr, variables, ctx)
    return _resolve_value(value.else_expr, variables, ctx)
  if isinstance(value, IndexExpr):
    target = _resolve_value(value.target, variables, ctx)
    idx = int(_as_number(_resolve_value(value.index, variables, ctx)))
    if isinstance(target, list) and 0 <= idx < len(target):
      return target[idx]
    return 0.0
  if isinstance(value, RangeExpr):
    start = _resolve_value(value.start, variables, ctx)
    end = _resolve_value(value.end, variables, ctx)
    step = _resolve_value(value.step, variables, ctx) if value.step is not None else None
    return _expand_range(start, end, step)
  if isinstance(value, ListComprehensionExpr):
    out: list[object] = []

    def run_binding(binding_index: int, local_vars: dict[str, object]):
      if binding_index >= len(value.bindings):
        out.append(_resolve_value(value.expr, local_vars, ctx))
        return

      var_name, iterable_expr = value.bindings[binding_index]
      iter_values = _resolve_value(iterable_expr, local_vars, ctx)
      for v in _iter_values(iter_values):
        next_vars = dict(local_vars)
        next_vars[var_name] = v
        run_binding(binding_index + 1, next_vars)

    run_binding(0, dict(variables))
    return out
  if isinstance(value, FunctionCallExpr):
    if ctx is None:
      return 0.0
    return _eval_function_call(value, ctx)
  if isinstance(value, LetExpr):
    local_vars = dict(variables)
    for name, expr in value.bindings:
      local_vars[name] = _resolve_value(expr, local_vars, ctx)
    return _resolve_value(value.expr, local_vars, ctx)
  if isinstance(value, list):
    return [_resolve_value(v, variables, ctx) for v in value]
  return value


def _to_float_list(values) -> list[float]:
  if not isinstance(values, list):
    return []
  out: list[float] = []
  for v in values:
    if isinstance(v, (int, float)):
      out.append(float(v))
  return out


def _resolve_include_path(path_value: str, source_path: str | None) -> str:
  p = Path(path_value)
  if p.is_absolute() or source_path is None:
    return str(p)
  return str((Path(source_path).parent / p).resolve())


def _read_file(path: str) -> str:
  with open(path, "r", encoding="utf-8") as f:
    return f.read()


def _register_modules_only(program: Program, ctx: EvalContext) -> None:
  for stmt in program.statements:
    if isinstance(stmt, ModuleDef):
      ctx.modules[stmt.name] = stmt
    if isinstance(stmt, FunctionDef):
      ctx.functions[stmt.name] = stmt


def _eval_node(node, ctx: EvalContext, transform_chain=None, color=None):
  transform_chain = list(transform_chain or [])

  if isinstance(node, Primitive):
    resolved_args = {k: _resolve_value(v, ctx.variables, ctx) for k, v in node.args.items()}
    return EvalItem(
      node_type="primitive",
      primitive=Primitive(kind=node.kind, args=resolved_args),
      transform_chain=transform_chain,
      color=color,
    )

  if isinstance(node, Transform):
    resolved_values = _resolve_value(node.values, ctx.variables, ctx)
    chain = transform_chain + [(node.kind, _to_float_list(resolved_values))]
    return EvalItem(
      node_type="group",
      transform_chain=transform_chain,
      children=[_eval_node(ch, ctx, chain, color) for ch in node.body],
      color=color,
    )

  if isinstance(node, BooleanOp):
    return EvalItem(
      node_type="boolean",
      boolean_kind=node.kind,
      transform_chain=transform_chain,
      children=[_eval_node(ch, ctx, transform_chain, color) for ch in node.body],
      color=color,
    )

  if isinstance(node, ColorOp):
    rgba = _to_float_list(_resolve_value(node.rgba, ctx.variables, ctx))
    if len(rgba) == 3:
      rgba.append(1.0)
    return EvalItem(
      node_type="group",
      transform_chain=transform_chain,
      children=[_eval_node(ch, ctx, transform_chain, rgba) for ch in node.body],
      color=rgba,
    )

  if isinstance(node, ModuleDef):
    ctx.modules[node.name] = node
    return EvalItem(node_type="noop", transform_chain=transform_chain)

  if isinstance(node, FunctionDef):
    ctx.functions[node.name] = node
    return EvalItem(node_type="noop", transform_chain=transform_chain)

  if isinstance(node, Assignment):
    ctx.variables[node.name] = _resolve_value(node.expr, ctx.variables, ctx)
    return EvalItem(node_type="noop", transform_chain=transform_chain)

  if isinstance(node, IfStmt):
    cond = _resolve_value(node.condition, ctx.variables, ctx)
    chosen = node.then_body if _truthy(cond) else node.else_body
    return EvalItem(
      node_type="group",
      transform_chain=transform_chain,
      children=[_eval_node(ch, ctx, transform_chain, color) for ch in chosen],
      color=color,
    )

  if isinstance(node, ForStmt):
    expanded_children: list[EvalItem] = []

    def run_binding(binding_index: int, current_vars: dict[str, object]):
      if binding_index >= len(node.bindings):
        sub_ctx = EvalContext(
          modules=ctx.modules,
          functions=ctx.functions,
          variables=current_vars,
          source_path=ctx.source_path,
          include_loader=ctx.include_loader,
          visited_includes=ctx.visited_includes,
        )
        for ch in node.body:
          expanded_children.append(_eval_node(ch, sub_ctx, transform_chain, color))
        return

      var_name, iterable_expr = node.bindings[binding_index]
      iter_values = _resolve_value(iterable_expr, current_vars, ctx)
      for v in _iter_values(iter_values):
        next_vars = dict(current_vars)
        next_vars[var_name] = v
        run_binding(binding_index + 1, next_vars)

    run_binding(0, dict(ctx.variables))
    return EvalItem(
      node_type="group",
      transform_chain=transform_chain,
      children=expanded_children,
      color=color,
    )

  if isinstance(node, ModuleCall):
    mod = ctx.modules.get(node.name)
    if mod is None:
      return EvalItem(node_type="noop", transform_chain=transform_chain)

    call_args = {k: _resolve_value(v, ctx.variables, ctx) for k, v in node.args.items()}
    bound_vars = dict(ctx.variables)

    arg_index = 0
    for param_name, default_value in mod.params:
      positional_key = f"arg{arg_index}"
      if param_name in call_args:
        bound_vars[param_name] = call_args[param_name]
      elif positional_key in call_args:
        bound_vars[param_name] = call_args[positional_key]
      elif default_value is not None:
        bound_vars[param_name] = _resolve_value(default_value, ctx.variables, ctx)
      else:
        bound_vars[param_name] = 0.0
      arg_index += 1

    sub_ctx = EvalContext(
      modules=ctx.modules,
      functions=ctx.functions,
      variables=bound_vars,
      source_path=ctx.source_path,
      include_loader=ctx.include_loader,
      visited_includes=ctx.visited_includes,
    )

    return EvalItem(
      node_type="group",
      transform_chain=transform_chain,
      children=[_eval_node(ch, sub_ctx, transform_chain, color) for ch in mod.body],
      color=color,
    )

  if isinstance(node, IncludeStmt):
    include_path = _resolve_include_path(node.path, ctx.source_path)
    if include_path in ctx.visited_includes:
      return EvalItem(node_type="noop", transform_chain=transform_chain)

    ctx.visited_includes.add(include_path)
    loader = ctx.include_loader or _read_file
    loaded_source = loader(include_path)
    loaded_program = parse_scad(loaded_source)

    sub_ctx = EvalContext(
      modules=ctx.modules,
      functions=ctx.functions,
      variables=ctx.variables,
      source_path=include_path,
      include_loader=ctx.include_loader,
      visited_includes=ctx.visited_includes,
    )

    return EvalItem(
      node_type="group",
      transform_chain=transform_chain,
      children=[_eval_node(ch, sub_ctx, transform_chain, color) for ch in loaded_program.statements],
      color=color,
    )

  if isinstance(node, UseStmt):
    include_path = _resolve_include_path(node.path, ctx.source_path)
    if include_path in ctx.visited_includes:
      return EvalItem(node_type="noop", transform_chain=transform_chain)

    ctx.visited_includes.add(include_path)
    loader = ctx.include_loader or _read_file
    loaded_source = loader(include_path)
    loaded_program = parse_scad(loaded_source)
    _register_modules_only(loaded_program, ctx)
    return EvalItem(node_type="noop", transform_chain=transform_chain)

  if isinstance(node, RawCall):
    return EvalItem(node_type="noop", transform_chain=transform_chain)

  return EvalItem(node_type="noop", transform_chain=transform_chain)


def evaluate_program(
  program: Program,
  source_path: str | None = None,
  include_loader: Callable[[str], str] | None = None,
) -> list[EvalItem]:
  ctx = EvalContext(source_path=source_path, include_loader=include_loader)
  return [_eval_node(stmt, ctx) for stmt in program.statements]
