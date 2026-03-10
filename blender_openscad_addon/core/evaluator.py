from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .ast import (
  BooleanOp,
  ColorOp,
  EvalItem,
  IncludeStmt,
  ModuleCall,
  ModuleDef,
  Primitive,
  Program,
  RawCall,
  Transform,
  UseStmt,
  VarRef,
)
from .parser import parse_scad


@dataclass
class EvalContext:
  modules: dict[str, ModuleDef] = field(default_factory=dict)
  variables: dict[str, object] = field(default_factory=dict)
  source_path: str | None = None
  include_loader: Callable[[str], str] | None = None
  visited_includes: set[str] = field(default_factory=set)


def _resolve_value(value, variables: dict[str, object]):
  if isinstance(value, VarRef):
    return variables.get(value.name, 0.0)
  if isinstance(value, list):
    return [_resolve_value(v, variables) for v in value]
  return value


def _resolve_args(args: dict[str, object], variables: dict[str, object]) -> dict[str, object]:
  return {k: _resolve_value(v, variables) for k, v in args.items()}


def _to_float_list(values, variables: dict[str, object]) -> list[float]:
  resolved = _resolve_value(values, variables)
  if not isinstance(resolved, list):
    return []
  out: list[float] = []
  for v in resolved:
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


def _eval_node(node, ctx: EvalContext, transform_chain=None, color=None):
  transform_chain = list(transform_chain or [])

  if isinstance(node, Primitive):
    resolved_args = _resolve_args(node.args, ctx.variables)
    return EvalItem(
      node_type="primitive",
      primitive=Primitive(kind=node.kind, args=resolved_args),
      transform_chain=transform_chain,
      color=color,
    )

  if isinstance(node, Transform):
    chain = transform_chain + [(node.kind, _to_float_list(node.values, ctx.variables))]
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
    rgba = _to_float_list(node.rgba, ctx.variables)
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

  if isinstance(node, ModuleCall):
    mod = ctx.modules.get(node.name)
    if mod is None:
      return EvalItem(node_type="noop", transform_chain=transform_chain)

    call_args = _resolve_args(node.args, ctx.variables)
    bound_vars = dict(ctx.variables)

    arg_index = 0
    for param_name, default_value in mod.params:
      positional_key = f"arg{arg_index}"
      if param_name in call_args:
        bound_vars[param_name] = call_args[param_name]
      elif positional_key in call_args:
        bound_vars[param_name] = call_args[positional_key]
      elif default_value is not None:
        bound_vars[param_name] = _resolve_value(default_value, ctx.variables)
      else:
        bound_vars[param_name] = 0.0
      arg_index += 1

    sub_ctx = EvalContext(
      modules=ctx.modules,
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
