from __future__ import annotations
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Token:
    tipo: str
    valor: str
    linea: int
    columna: int


class ErrorLexico(ValueError):
    pass


REGLAS = re.compile(
    r'(?P<ESPACIO>\s+)|'
    r'(?P<COMENTARIO_LINEA>//[^\n]*)|'
    r'(?P<COMENTARIO_BLOQUE>/\*[\s\S]*?\*/)|'
    r'(?P<NUMERO>\d+)|'
    r'(?P<IDENTIFICADOR>[A-Za-z_][A-Za-z_0-9]*)|'
    r'(?P<OPERADOR>==|!=|<=|>=|[+\-*/=<>])|'
    r'(?P<SIMBOLO>[{}();])|'
    r'(?P<INVALIDO>.)'
)
RESERVADAS = {'int', 'main', 'if', 'else', 'while', 'return'}


def tokenizar(codigo: str) -> list[Token]:
    tokens = []
    linea, columna = 1, 1
    cursor = 0
    while cursor < len(codigo):
        coincidencia = REGLAS.match(codigo, cursor)
        if coincidencia is None:
            raise ErrorLexico(f"Caracter inesperado en {linea}:{columna}")
        tipo = coincidencia.lastgroup
        valor = coincidencia.group()
        if tipo == 'INVALIDO':
            raise ErrorLexico(f"Caracter no permitido {valor!r} en línea {linea}, columna {columna}")
        if tipo not in {'ESPACIO', 'COMENTARIO_LINEA', 'COMENTARIO_BLOQUE'}:
            tipo = 'PALABRA_CLAVE' if tipo == 'IDENTIFICADOR' and valor in RESERVADAS else tipo
            tokens.append(Token(tipo, valor, linea, columna))
        saltos = valor.count('\n')
        if saltos:
            linea += saltos
            columna = len(valor.rsplit('\n', 1)[-1]) + 1
        else:
            columna += len(valor)
        cursor = coincidencia.end()
    tokens.append(Token('EOF', '<fin>', linea, columna))
    return tokens
