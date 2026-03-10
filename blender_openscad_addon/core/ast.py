from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class Node:
  pass


@dataclass
class Program(Node):
  statements: List[Node] = field(default_factory=list)


@dataclass
class UnaryExpr(Node):
  op: str
  value: Any


@dataclass
class BinaryExpr(Node):
  op: str
  left: Any
  right: Any


@dataclass
class TernaryExpr(Node):
  condition: Any
  then_expr: Any
  else_expr: Any


@dataclass
class IndexExpr(Node):
  target: Any
  index: Any


@dataclass
class RangeExpr(Node):
  start: Any
  end: Any
  step: Any = None


@dataclass
class ListComprehensionExpr(Node):
  bindings: list[tuple[str, Any]] = field(default_factory=list)
  expr: Any = None
  filter_expr: Any = None


@dataclass
class FunctionCallExpr(Node):
  name: str
  args: list[Any] = field(default_factory=list)


@dataclass
class LetExpr(Node):
  bindings: list[tuple[str, Any]] = field(default_factory=list)
  expr: Any = None


@dataclass
class VarRef(Node):
  name: str


@dataclass
class IncludeStmt(Node):
  path: str


@dataclass
class UseStmt(Node):
  path: str


@dataclass
class ModuleDef(Node):
  name: str
  params: list[tuple[str, Any]] = field(default_factory=list)
  body: list[Node] = field(default_factory=list)


@dataclass
class FunctionDef(Node):
  name: str
  params: list[tuple[str, Any]] = field(default_factory=list)
  expr: Any = None


@dataclass
class Assignment(Node):
  name: str
  expr: Any


@dataclass
class IfStmt(Node):
  condition: Any
  then_body: list[Node] = field(default_factory=list)
  else_body: list[Node] = field(default_factory=list)


@dataclass
class ForStmt(Node):
  bindings: list[tuple[str, Any]] = field(default_factory=list)
  body: list[Node] = field(default_factory=list)


@dataclass
class ModuleCall(Node):
  name: str
  args: dict[str, Any]
  body: list[Node] = field(default_factory=list)


@dataclass
class Primitive(Node):
  kind: str
  args: dict[str, Any]


@dataclass
class Transform(Node):
  kind: str
  values: list[float]
  body: list[Node] = field(default_factory=list)


@dataclass
class Extrude(Node):
  kind: str  # "linear" or "rotate"
  args: dict[str, Any]
  body: list[Node] = field(default_factory=list)


@dataclass
class Mirror(Node):
  vector: list[float]
  body: list[Node] = field(default_factory=list)


@dataclass
class Resize(Node):
  newsize: list[float]
  auto: Any  # bool ou lista de bools
  body: list[Node] = field(default_factory=list)


@dataclass
class Multmatrix(Node):
  matrix: list[list[float]]
  body: list[Node] = field(default_factory=list)


@dataclass
class Offset(Node):
  args: dict[str, Any]
  body: list[Node] = field(default_factory=list)


@dataclass
class Projection(Node):
  cut: bool
  body: list[Node] = field(default_factory=list)


@dataclass
class Polygon(Node):
  points: Any
  paths: Any = None


@dataclass
class Circle(Node):
  args: dict[str, Any]


@dataclass
class Square(Node):
  args: dict[str, Any]


@dataclass
class BooleanOp(Node):
  kind: str
  body: list[Node] = field(default_factory=list)


@dataclass
class ColorOp(Node):
  rgba: list[float]
  body: list[Node] = field(default_factory=list)


@dataclass
class RawCall(Node):
  name: str
  args: dict[str, Any]


@dataclass
class ModifierStmt(Node):
  modifier: str  # "#", "%", "!", "*"
  body: Node = None


@dataclass
class TextPrimitive(Node):
  args: dict[str, Any]


@dataclass
class ImportStmt(Node):
  path: str
  args: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalItem:
  node_type: str
  primitive: Optional[Primitive] = None
  transform_chain: list[tuple[str, list[float]]] = field(default_factory=list)
  boolean_kind: Optional[str] = None
  children: list["EvalItem"] = field(default_factory=list)
  color: Optional[list[float]] = None
