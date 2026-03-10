from __future__ import annotations

import re
from dataclasses import dataclass


TOKEN_REGEX = re.compile(
  r"(?P<number>\d+(?:\.\d+)?)|(?P<string>\"[^\"\\]*(?:\\.[^\"\\]*)*\")|(?P<ident>\$?[A-Za-z_][A-Za-z0-9_]*)|(?P<symbol>[\[\]\{\}\(\),;=<>./\\\-+*%!&|?:#])"
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
    # Pular espaços em branco antes de qualquer verificação
    while pos < n and source[pos] in ' \t\r\n':
      pos += 1
    if pos >= n:
      break

    if source[pos:pos + 2] == "//":
      nl = source.find("\n", pos)
      if nl == -1:
        break
      pos = nl + 1
      continue

    m = TOKEN_REGEX.match(source, pos)
    if not m:
      raise TokenError(f"Token invalido na posicao {pos}: {source[pos:pos + 16]!r}")

    pos = m.end()
    if m.group("number") is not None:
      out.append(Token("number", m.group("number"), m.start()))
    elif m.group("string") is not None:
      out.append(Token("string", m.group("string"), m.start()))
    elif m.group("ident") is not None:
      out.append(Token("ident", m.group("ident"), m.start()))
    else:
      sym = m.group("symbol")
      start_idx = m.start()
      # Handle multi-character operators
      if sym == "=" and pos < n and source[pos] == "=":
        out.append(Token("symbol", "==", start_idx))
        pos += 1
      elif sym == "!" and pos < n and source[pos] == "=":
        out.append(Token("symbol", "!=", start_idx))
        pos += 1
      elif sym == "<" and pos < n and source[pos] == "=":
        out.append(Token("symbol", "<=", start_idx))
        pos += 1
      elif sym == ">" and pos < n and source[pos] == "=":
        out.append(Token("symbol", ">=", start_idx))
        pos += 1
      elif sym == "&" and pos < n and source[pos] == "&":
        out.append(Token("symbol", "&&", start_idx))
        pos += 1
      elif sym == "|" and pos < n and source[pos] == "|":
        out.append(Token("symbol", "||", start_idx))
        pos += 1
      else:
        out.append(Token("symbol", sym, start_idx))

  out.append(Token("eof", "", n))
  return out
