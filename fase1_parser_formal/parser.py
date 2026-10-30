
from __future__ import annotations
from core.arbol import Nodo
from fase1_parser_formal.lexer import Token, tokenizar


class ErrorSintactico(ValueError):
    pass


class ParserC:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.indice = 0

    @property
    def actual(self) -> Token:
        return self.tokens[self.indice]

    def aceptar(self, valor: str) -> bool:
        if self.actual.valor == valor:
            self.indice += 1
            return True
        return False

    def esperar(self, valor: str) -> Token:
        if self.actual.valor != valor:
            self.error(f"Se esperaba {valor!r}")
        token = self.actual
        self.indice += 1
        return token

    def esperar_tipo(self, tipo: str) -> Token:
        if self.actual.tipo != tipo:
            self.error(f"Se esperaba un token de tipo {tipo}")
        token = self.actual
        self.indice += 1
        return token

    def error(self, mensaje: str) -> None:
        t = self.actual
        raise ErrorSintactico(f"{mensaje}; apareció {t.valor!r} en línea {t.linea}, columna {t.columna}")

    def analizar(self) -> Nodo:
        self.esperar('int')
        self.esperar('main')
        self.esperar('(')
        self.esperar(')')
        cuerpo = self.bloque()
        if self.actual.tipo != 'EOF':
            self.error('Se encontró texto después de la función main')
        return Nodo('Programa C', [Nodo('Función int main()', [cuerpo])])

    def sentencia(self) -> Nodo:
        valor = self.actual.valor
        if valor == 'int':
            return self.declaracion()
        if self.actual.tipo == 'IDENTIFICADOR':
            return self.asignacion()
        if valor == 'return':
            return self.retorno()
        if valor == 'if':
            return self.condicional()
        if valor == 'while':
            return self.bucle()
        if valor == '{':
            return self.bloque()
        self.error('Inicio de sentencia no válido')

    def declaracion(self) -> Nodo:
        self.esperar('int')
        nombre = self.esperar_tipo('IDENTIFICADOR').valor
        hijos = [Nodo(f'Identificador: {nombre}')]
        if self.aceptar('='):
            hijos.append(self.expresion())
        self.esperar(';')
        return Nodo('Declaración int', hijos)

    def asignacion(self) -> Nodo:
        nombre = self.esperar_tipo('IDENTIFICADOR').valor
        self.esperar('=')
        expresion = self.expresion()
        self.esperar(';')
        return Nodo('Asignación', [Nodo(f'Variable: {nombre}'), expresion])

    def retorno(self) -> Nodo:
        self.esperar('return')
        valor = self.expresion()
        self.esperar(';')
        return Nodo('Return', [valor])

    def condicional(self) -> Nodo:
        self.esperar('if')
        self.esperar('(')
        condicion = self.condicion()
        self.esperar(')')
        entonces = self.sentencia()
        hijos = [Nodo('Condición', [condicion]), Nodo('Entonces', [entonces])]
        if self.aceptar('else'):
            hijos.append(Nodo('Si no', [self.sentencia()]))
        return Nodo('Condicional if', hijos)

    def bucle(self) -> Nodo:
        self.esperar('while')
        self.esperar('(')
        condicion = self.condicion()
        self.esperar(')')
        return Nodo('Bucle while', [condicion, self.sentencia()])

    def bloque(self) -> Nodo:
        self.esperar('{')
        sentencias = []
        while self.actual.valor not in {'}', '<fin>'}:
            sentencias.append(self.sentencia())
        self.esperar('}')
        return Nodo('Bloque', sentencias)

    def condicion(self) -> Nodo:
        izquierda = self.expresion()
        if self.actual.valor not in {'==', '!=', '<', '<=', '>', '>='}:
            self.error('Se esperaba operador relacional (==, !=, <, <=, >, >=)')
        operador = self.actual.valor
        self.indice += 1
        derecha = self.expresion()
        return Nodo(f'Comparación {operador}', [izquierda, derecha])

    def expresion(self) -> Nodo:
        izquierda = self.termino()
        while self.actual.valor in {'+', '-'}:
            operador = self.actual.valor
            self.indice += 1
            derecha = self.termino()
            izquierda = Nodo(f'Expresión {operador}', [izquierda, derecha])
        return izquierda

    def termino(self) -> Nodo:
        izquierda = self.factor()
        while self.actual.valor in {'*', '/'}:
            operador = self.actual.valor
            self.indice += 1
            derecha = self.factor()
            izquierda = Nodo(f'Término {operador}', [izquierda, derecha])
        return izquierda

    def factor(self) -> Nodo:
        token = self.actual
        if token.tipo == 'NUMERO':
            self.indice += 1
            return Nodo(f'Número: {token.valor}')
        if token.tipo == 'IDENTIFICADOR':
            self.indice += 1
            return Nodo(f'Identificador: {token.valor}')
        if self.aceptar('('):
            nodo = self.expresion()
            self.esperar(')')
            return Nodo('Paréntesis', [nodo])
        if self.aceptar('-'):
            return Nodo('Negación unaria', [self.factor()])
        self.error('Se esperaba número, identificador, paréntesis o signo negativo')


def analizar_codigo(codigo: str) -> Nodo:
    """Entrada pública del módulo; otros integrantes pueden importarla."""
    return ParserC(tokenizar(codigo)).analizar()
