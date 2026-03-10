from __future__ import annotations

from .ast import (
  Assignment,
  BinaryExpr,
  BooleanOp,
  Circle,
  ColorOp,
  Extrude,
  ForStmt,
  FunctionCallExpr,
  FunctionDef,
  IfStmt,
  IndexExpr,
  IncludeStmt,
  LetExpr,
  ListComprehensionExpr,
  Mirror,
  ModuleCall,
  ModuleDef,
  Multmatrix,
  Offset,
  Polygon,
  Primitive,
  Program,
  Projection,
  RangeExpr,
  RawCall,
  Resize,
  Square,
  TernaryExpr,
  Transform,
  UnaryExpr,
  UseStmt,
  VarRef,
)
from .tokenizer import Token, tokenize


class ParseError(ValueError):
  pass


class Parser:
  def __init__(self, source: str):
    self.tokens = tokenize(source)
    self.idx = 0

  def peek(self) -> Token:
    return self.tokens[self.idx]

  def advance(self) -> Token:
    t = self.tokens[self.idx]
    self.idx += 1
    return t

  def expect_symbol(self, sym: str) -> None:
    t = self.advance()
    if t.kind != "symbol" or t.value != sym:
      raise ParseError(f"Esperado '{sym}' na posicao {t.index}")

  def match_symbol(self, sym: str) -> bool:
    t = self.peek()
    if t.kind == "symbol" and t.value == sym:
      self.advance()
      return True
    return False

  def match_symbol_pair(self, a: str, b: str) -> bool:
    if self.idx + 1 >= len(self.tokens):
      return False
    t1 = self.tokens[self.idx]
    t2 = self.tokens[self.idx + 1]
    if t1.kind == "symbol" and t1.value == a and t2.kind == "symbol" and t2.value == b:
      self.idx += 2
      return True
    return False

  def match_keyword(self, name: str) -> bool:
    t = self.peek()
    if t.kind == "ident" and t.value == name:
      self.advance()
      return True
    return False

  def expect_ident(self) -> str:
    t = self.advance()
    if t.kind != "ident":
      raise ParseError(f"Identificador esperado na posicao {t.index}")
    return t.value

  def parse_number(self) -> float:
    t = self.advance()
    if t.kind != "number":
      raise ParseError(f"Numero esperado na posicao {t.index}")
    return float(t.value)

  def parse_string(self) -> str:
    t = self.advance()
    if t.kind != "string":
      raise ParseError(f"String esperada na posicao {t.index}")
    return t.value[1:-1]

  def parse_bracket_expr(self):
    self.expect_symbol("[")
    if self.match_symbol("]"):
      return []

    if self.match_keyword("for"):
      self.expect_symbol("(")
      bindings: list[tuple[str, object]] = []
      while True:
        var_name = self.expect_ident()
        self.expect_symbol("=")
        iterable = self.parse_expression()
        bindings.append((var_name, iterable))
        if self.match_symbol(","):
          continue
        self.expect_symbol(")")
        break
      filter_expr = None
      if self.match_keyword("if"):
        self.expect_symbol("(")
        filter_expr = self.parse_expression()
        self.expect_symbol(")")
      expr = self.parse_expression()
      self.expect_symbol("]")
      return ListComprehensionExpr(bindings=bindings, expr=expr, filter_expr=filter_expr)

    first = self.parse_expression()
    if self.match_symbol(":"):
      second = self.parse_expression()
      if self.match_symbol(":"):
        third = self.parse_expression()
        self.expect_symbol("]")
        return RangeExpr(start=first, step=second, end=third)
      self.expect_symbol("]")
      return RangeExpr(start=first, end=second)

    values: list[object] = [first]
    while self.match_symbol(","):
      values.append(self.parse_expression())
    self.expect_symbol("]")
    return values

  def parse_call_args_positional(self) -> list[object]:
    args: list[object] = []
    self.expect_symbol("(")
    while True:
      t = self.peek()
      if t.kind == "symbol" and t.value == ")":
        self.advance()
        break

      args.append(self.parse_value())
      if self.peek().kind == "symbol" and self.peek().value == ",":
        self.advance()
        continue
    return args

  def parse_args(self) -> dict[str, object]:
    args: dict[str, object] = {}
    self.expect_symbol("(")
    auto = 0
    while True:
      t = self.peek()
      if t.kind == "symbol" and t.value == ")":
        self.advance()
        break

      if t.kind == "ident":
        t2 = self.tokens[self.idx + 1]
        if t2.kind == "symbol" and t2.value == "=":
          name = self.advance().value
          self.advance()
          args[name] = self.parse_value()
        else:
          args[f"arg{auto}"] = self.parse_value()
          auto += 1
      else:
        args[f"arg{auto}"] = self.parse_value()
        auto += 1

      if self.peek().kind == "symbol" and self.peek().value == ",":
        self.advance()
        continue
    return args

  def parse_value(self):
    return self.parse_expression()

  def parse_expression(self):
    condition = self.parse_logical_or()
    if self.match_symbol("?"):
      then_expr = self.parse_expression()
      self.expect_symbol(":")
      else_expr = self.parse_expression()
      return TernaryExpr(condition=condition, then_expr=then_expr, else_expr=else_expr)
    return condition

  def parse_logical_or(self):
    left = self.parse_logical_and()
    while self.match_symbol("||"):
      right = self.parse_logical_and()
      left = BinaryExpr(op="||", left=left, right=right)
    return left

  def parse_logical_and(self):
    left = self.parse_equality()
    while self.match_symbol("&&"):
      right = self.parse_equality()
      left = BinaryExpr(op="&&", left=left, right=right)
    return left

  def parse_equality(self):
    left = self.parse_relational()
    while True:
      if self.match_symbol("=="):
        right = self.parse_relational()
        left = BinaryExpr(op="==", left=left, right=right)
        continue
      if self.match_symbol("!="):
        right = self.parse_relational()
        left = BinaryExpr(op="!=", left=left, right=right)
        continue
      break
    return left

  def parse_relational(self):
    left = self.parse_additive()
    while True:
      if self.match_symbol("<="):
        right = self.parse_additive()
        left = BinaryExpr(op="<=", left=left, right=right)
        continue
      if self.match_symbol(">="):
        right = self.parse_additive()
        left = BinaryExpr(op=">=", left=left, right=right)
        continue
      if self.match_symbol("<"):
        right = self.parse_additive()
        left = BinaryExpr(op="<", left=left, right=right)
        continue
      if self.match_symbol(">"):
        right = self.parse_additive()
        left = BinaryExpr(op=">", left=left, right=right)
        continue
      break
    return left

  def parse_additive(self):
    left = self.parse_multiplicative()
    while self.peek().kind == "symbol" and self.peek().value in {"+", "-"}:
      op = self.advance().value
      right = self.parse_multiplicative()
      left = BinaryExpr(op=op, left=left, right=right)
    return left

  def parse_multiplicative(self):
    left = self.parse_unary()
    while self.peek().kind == "symbol" and self.peek().value in {"*", "/", "%"}:
      op = self.advance().value
      right = self.parse_unary()
      left = BinaryExpr(op=op, left=left, right=right)
    return left

  def parse_unary(self):
    if self.peek().kind == "symbol" and self.peek().value in {"+", "-", "!"}:
      op = self.advance().value
      return UnaryExpr(op=op, value=self.parse_unary())
    return self.parse_primary()

  def parse_let_expr(self):
    bindings: list[tuple[str, object]] = []
    self.expect_symbol("(")
    while True:
      if self.match_symbol(")"):
        break
      name = self.expect_ident()
      self.expect_symbol("=")
      value = self.parse_expression()
      bindings.append((name, value))
      if self.match_symbol(","):
        continue
      self.expect_symbol(")")
      break
    expr = self.parse_expression()
    return LetExpr(bindings=bindings, expr=expr)

  def parse_primary(self):
    t = self.peek()
    if t.kind == "number":
      return self.parse_number()
    if t.kind == "string":
      return self.parse_string()
    if t.kind == "symbol" and t.value == "[":
      return self.parse_bracket_expr()
    if t.kind == "symbol" and t.value == "(":
      self.advance()
      expr = self.parse_expression()
      self.expect_symbol(")")
      return expr
    if t.kind == "ident":
      name = self.advance().value
      if name == "let" and self.peek().kind == "symbol" and self.peek().value == "(":
        expr = self.parse_let_expr()
      elif self.peek().kind == "symbol" and self.peek().value == "(":
        expr = FunctionCallExpr(name=name, args=self.parse_call_args_positional())
      else:
        expr = VarRef(name)

      while self.peek().kind == "symbol" and self.peek().value == "[":
        self.advance()
        idx_expr = self.parse_expression()
        self.expect_symbol("]")
        expr = IndexExpr(target=expr, index=idx_expr)
      return expr

    if t.kind == "symbol" and t.value == "(":
      self.advance()
      expr = self.parse_expression()
      self.expect_symbol(")")
      while self.peek().kind == "symbol" and self.peek().value == "[":
        self.advance()
        idx_expr = self.parse_expression()
        self.expect_symbol("]")
        expr = IndexExpr(target=expr, index=idx_expr)
      return expr
    raise ParseError(f"Valor invalido na posicao {t.index}")

  def parse_path_value(self) -> str:
    t = self.peek()
    if t.kind == "string":
      return self.parse_string()

    if t.kind == "symbol" and t.value == "<":
      self.advance()
      parts: list[str] = []
      while True:
        cur = self.peek()
        if cur.kind == "symbol" and cur.value == ">":
          self.advance()
          break
        if cur.kind in {"ident", "number", "symbol", "string"}:
          parts.append(self.advance().value.strip('"'))
          continue
        raise ParseError(f"Path invalido na posicao {cur.index}")
      return "".join(parts)

    raise ParseError(f"Path esperado na posicao {t.index}")

  def parse_module_params(self) -> list[tuple[str, object]]:
    params: list[tuple[str, object]] = []
    self.expect_symbol("(")
    while True:
      t = self.peek()
      if t.kind == "symbol" and t.value == ")":
        self.advance()
        break

      name = self.expect_ident()
      default = None
      if self.peek().kind == "symbol" and self.peek().value == "=":
        self.advance()
        default = self.parse_value()
      params.append((name, default))

      if self.peek().kind == "symbol" and self.peek().value == ",":
        self.advance()
        continue
    return params

  def parse_block(self) -> list:
    self.expect_symbol("{")
    items = []
    while not (self.peek().kind == "symbol" and self.peek().value == "}"):
      items.append(self.parse_statement())
    self.expect_symbol("}")
    return items

  def parse_body_items(self) -> list:
    if self.peek().kind == "symbol" and self.peek().value == "{":
      return self.parse_block()
    return [self.parse_statement()]

  def parse_statement(self):
    name = self.expect_ident()

    if name == "if":
      self.expect_symbol("(")
      condition = self.parse_expression()
      self.expect_symbol(")")
      then_body = self.parse_body_items()
      else_body = []
      if self.match_keyword("else"):
        else_body = self.parse_body_items()
      return IfStmt(condition=condition, then_body=then_body, else_body=else_body)

    if name == "for":
      self.expect_symbol("(")
      bindings: list[tuple[str, object]] = []
      while True:
        var_name = self.expect_ident()
        self.expect_symbol("=")
        iterable = self.parse_expression()
        bindings.append((var_name, iterable))
        if self.match_symbol(","):
          continue
        self.expect_symbol(")")
        break
      body = self.parse_body_items()
      return ForStmt(bindings=bindings, body=body)

    if name == "include":
      path = self.parse_path_value()
      self.expect_symbol(";")
      return IncludeStmt(path=path)

    if name == "use":
      path = self.parse_path_value()
      self.expect_symbol(";")
      return UseStmt(path=path)

    if name == "module":
      module_name = self.expect_ident()
      params = self.parse_module_params()
      body = self.parse_block()
      return ModuleDef(name=module_name, params=params, body=body)

    if name == "function":
      function_name = self.expect_ident()
      params = self.parse_module_params()
      self.expect_symbol("=")
      expr = self.parse_expression()
      self.expect_symbol(";")
      return FunctionDef(name=function_name, params=params, expr=expr)

    if self.match_symbol("="):
      expr = self.parse_expression()
      self.expect_symbol(";")
      return Assignment(name=name, expr=expr)

    args = self.parse_args()

    if name in {"translate", "rotate", "scale"}:
      vals = args.get("arg0")
      if not isinstance(vals, list):
        raise ParseError(f"{name} espera vetor")
      body = self.parse_body_items()
      return Transform(kind=name, values=vals, body=body)

    if name == "mirror":
      vals = args.get("arg0", args.get("v", [1, 0, 0]))
      if not isinstance(vals, list):
        vals = [1, 0, 0]
      body = self.parse_body_items()
      return Mirror(vector=vals, body=body)

    if name == "resize":
      newsize = args.get("arg0", args.get("newsize", [0, 0, 0]))
      auto = args.get("auto", False)
      if not isinstance(newsize, list):
        newsize = [0, 0, 0]
      body = self.parse_body_items()
      return Resize(newsize=newsize, auto=auto, body=body)

    if name == "multmatrix":
      mat = args.get("arg0", args.get("m", []))
      body = self.parse_body_items()
      return Multmatrix(matrix=mat, body=body)

    if name == "offset":
      body = self.parse_body_items()
      return Offset(args=args, body=body)

    if name == "projection":
      cut = bool(args.get("cut", False))
      body = self.parse_body_items()
      return Projection(cut=cut, body=body)

    if name in {"union", "difference", "intersection", "hull", "minkowski"}:
      body = self.parse_body_items()
      return BooleanOp(kind=name, body=body)

    if name == "color":
      vals = args.get("arg0")
      if not isinstance(vals, list):
        raise ParseError("color() espera vetor [r,g,b] ou [r,g,b,a]")
      body = self.parse_body_items()
      return ColorOp(rgba=vals, body=body)

    if name in {"cube", "sphere", "cylinder"}:
      self.expect_symbol(";")
      return Primitive(kind=name, args=args)

    if name == "polygon":
      self.expect_symbol(";")
      points = args.get("arg0", args.get("points"))
      paths = args.get("arg1", args.get("paths"))
      return Polygon(points=points, paths=paths)

    if name == "circle":
      self.expect_symbol(";")
      return Circle(args=args)

    if name == "square":
      self.expect_symbol(";")
      return Square(args=args)

    if name in {"linear_extrude", "rotate_extrude"}:
      kind = "linear" if name == "linear_extrude" else "rotate"
      body = self.parse_body_items()
      return Extrude(kind=kind, args=args, body=body)

    if self.peek().kind == "symbol" and self.peek().value == ";":
      self.advance()
      return ModuleCall(name=name, args=args)

    self.expect_symbol(";")
    return RawCall(name=name, args=args)

  def parse_program(self) -> Program:
    out = []
    while self.peek().kind != "eof":
      out.append(self.parse_statement())
    return Program(statements=out)


def parse_scad(source: str) -> Program:
  return Parser(source).parse_program()
