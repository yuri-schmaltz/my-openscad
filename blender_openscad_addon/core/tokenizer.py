from __future__ import annotations

import re
from dataclasses import dataclass


TOKEN_REGEX = re.compile(
  r"\s*(?:(?P<number>-?\d+(?:\.\d+)?)|(?P<string>\"[^\"\\]*(?:\\.[^\"\\]*)*\")|(?P<ident>[A-Za-z_][A-Za-z0-9_]*)|(?P<symbol>[\[\]\{\}\(\),;=<>./\\-]))"
)


@dataclass
class Token:
  kind: str
  value: str
  index: int


class TokenError(ValueError):
  pass


def tokenize(source: str) -> list[Token]:
  pos = 0
  out: list[Token] = []
  n = len(source)

  while pos < n:
    if source[pos:pos + 2] == "//":
      nl = source.find("\n", pos)
      if nl == -1:
        break
      pos = nl + 1
      continue

    m = TOKEN_REGEX.match(source, pos)
    if not m:
      if source[pos].isspace():
        pos += 1
        continue
      raise TokenError(f"Token invalido na posicao {pos}: {source[pos:pos + 16]!r}")

    pos = m.end()
    if m.group("number") is not None:
      out.append(Token("number", m.group("number"), m.start()))
    elif m.group("string") is not None:
      out.append(Token("string", m.group("string"), m.start()))
    elif m.group("ident") is not None:
      out.append(Token("ident", m.group("ident"), m.start()))
    else:
      out.append(Token("symbol", m.group("symbol"), m.start()))

  out.append(Token("eof", "", n))
  return out
