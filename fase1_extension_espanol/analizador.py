"""Analizador descendente recursivo con retroceso que enumera TODAS las derivaciones.

Por que cambie de estrategia respecto a la fase 1: el parser de C es
descendente recursivo determinista porque la gramatica de ese subconjunto es
LL(1). La gramatica del espanol no lo es, y no por un defecto de diseno que se
pueda corregir: v3 es ambigua, y una gramatica ambigua no es LL(k) para ningun
k, porque existen cadenas con mas de un arbol de derivacion y un analizador
determinista solo puede devolver uno. Asi que aqui conservo el analisis
descendente pero le agrego retroceso completo y enumeracion de derivaciones.

Dos modos:
  contar(oracion)  -> cuantas derivaciones hay (exacto, por programacion
                      dinamica; no construye arboles, asi que es barato aunque
                      el numero de derivaciones sea enorme)
  analizar(oracion)-> el conteo exacto mas los primeros N arboles concretos
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from core.arbol import Nodo
from fase1_extension_espanol.gramatica import (
    Gramatica,
    es_categoria_lexica,
    partes,
)
from fase1_extension_espanol.lexico import candidatos, tokenizar

LIMITE_ARBOLES = 50

NOMBRES_LEGIBLES = {
    'O': 'Oracion',
    'FN': 'Frase nominal',
    'FV': 'Frase verbal',
    'NUC': 'Nucleo nominal',
    'NUCV': 'Nucleo verbal',
    'MODN': 'Mods. del nombre',
    'MODV': 'Mods. del verbo',
    'FPREP': 'Frase preposicional',
    'SUBORD': 'Subordinada relativa',
    'ORESP': 'Oracion distributiva',
}


class ErrorLexicoEspanol(ValueError):
    """La oracion contiene una palabra que no esta en el lexico declarado."""


def etiqueta_de(simbolo_: str) -> str:
    """Nombre legible de un no terminal, conservando sus rasgos."""
    nombre, rasgos = partes(simbolo_)
    base = NOMBRES_LEGIBLES.get(nombre, nombre)
    if rasgos:
        base += ' [' + ','.join(rasgos[k] for k in sorted(rasgos)) + ']'
    return base


def podar_vacios(nodo: Nodo) -> Nodo:
    """Quita los nodos que solo derivaron epsilon, para que el arbol se lea."""
    hijos = []
    for hijo in nodo.hijos:
        if len(hijo.hijos) == 1 and hijo.hijos[0].etiqueta == 'epsilon' and not hijo.hijos[0].hijos:
            continue
        hijos.append(podar_vacios(hijo))
    return Nodo(nodo.etiqueta, hijos)


@dataclass
class Resultado:
    oracion: str
    palabras: list[str] = field(default_factory=list)
    gramatica: str = ''
    derivaciones: int = 0
    arboles: list[Nodo] = field(default_factory=list)

    @property
    def aceptada(self) -> bool:
        return self.derivaciones > 0

    @property
    def ambigua(self) -> bool:
        return self.derivaciones > 1

    @property
    def truncado(self) -> bool:
        return self.derivaciones > len(self.arboles)

    def resumen(self) -> str:
        if not self.aceptada:
            return f'RECHAZADA por {self.gramatica}: "{self.oracion}"'
        marca = ' (AMBIGUA)' if self.ambigua else ''
        return (f'ACEPTADA por {self.gramatica}: "{self.oracion}" '
                f'-> {self.derivaciones} derivacion(es){marca}')


class Analizador:
    def __init__(self, gramatica: Gramatica) -> None:
        self.gramatica = gramatica
        self._indice: dict[str, list] = {}
        for produccion in gramatica.producciones:
            self._indice.setdefault(produccion.izquierda, []).append(produccion)
        self._palabras: list[str] = []
        self._memo: dict[tuple[str, int], dict[int, int]] = {}
        self._en_proceso: set[tuple[str, int]] = set()

    # -- preparacion ------------------------------------------------------
    def _preparar(self, oracion: str) -> list[str]:
        palabras = tokenizar(oracion)
        if not palabras:
            raise ErrorLexicoEspanol('La oracion esta vacia')
        desconocidas = [p for p in palabras if not candidatos(p)]
        if desconocidas:
            raise ErrorLexicoEspanol(
                'Palabra(s) fuera del lexico declarado: ' + ', '.join(desconocidas))
        self._palabras = palabras
        self._memo = {}
        self._en_proceso = set()
        return palabras

    # -- conteo exacto de derivaciones ------------------------------------
    def contar(self, oracion: str) -> int:
        palabras = self._preparar(oracion)
        return self._contar(self.gramatica.inicial, 0).get(len(palabras), 0)

    def _contar(self, simbolo_: str, pos: int) -> dict[int, int]:
        """Para un simbolo en una posicion: cuantas derivaciones terminan en cada fin."""
        clave = (simbolo_, pos)
        if clave in self._memo:
            return self._memo[clave]
        if clave in self._en_proceso:
            raise RecursionError(
                f'Recursion izquierda en {simbolo_} (posicion {pos}): '
                'el analisis descendente no termina con esta gramatica')
        self._en_proceso.add(clave)
        try:
            if es_categoria_lexica(simbolo_):
                resultado = self._contar_lexico(simbolo_, pos)
            else:
                acumulado: Counter[int] = Counter()
                for produccion in self._indice.get(simbolo_, ()):
                    for fin, cuenta in self._contar_secuencia(produccion.derecha, pos).items():
                        acumulado[fin] += cuenta
                resultado = dict(acumulado)
        finally:
            self._en_proceso.discard(clave)
        self._memo[clave] = resultado
        return resultado

    def _contar_secuencia(self, simbolos: tuple[str, ...], pos: int) -> dict[int, int]:
        actual: dict[int, int] = {pos: 1}
        for simbolo_ in simbolos:
            siguiente: Counter[int] = Counter()
            for posicion, cuenta in actual.items():
                for fin, cuenta_hijo in self._contar(simbolo_, posicion).items():
                    siguiente[fin] += cuenta * cuenta_hijo
            actual = dict(siguiente)
            if not actual:
                return {}
        return actual

    def _contar_lexico(self, simbolo_: str, pos: int) -> dict[int, int]:
        if pos >= len(self._palabras):
            return {}
        categoria, rasgos = partes(simbolo_)
        coincidencias = candidatos(self._palabras[pos], categoria, rasgos)
        return {pos + 1: len(coincidencias)} if coincidencias else {}

    # -- construccion de arboles concretos --------------------------------
    def analizar(self, oracion: str, maximo: int = LIMITE_ARBOLES) -> Resultado:
        palabras = self._preparar(oracion)
        total = self._contar(self.gramatica.inicial, 0).get(len(palabras), 0)
        arboles: list[Nodo] = []
        if total:
            for nodo, fin in self._generar(self.gramatica.inicial, 0):
                if fin == len(palabras):
                    arboles.append(podar_vacios(nodo))
                    if len(arboles) >= maximo:
                        break
        return Resultado(oracion, palabras, self.gramatica.nombre, total, arboles)

    def _generar(self, simbolo_: str, pos: int):
        """Genera perezosamente los arboles de un simbolo desde una posicion."""
        if es_categoria_lexica(simbolo_):
            if pos >= len(self._palabras):
                return
            categoria, rasgos = partes(simbolo_)
            for entrada in candidatos(self._palabras[pos], categoria, rasgos):
                yield Nodo(entrada.etiqueta()), pos + 1
            return
        etiqueta = etiqueta_de(simbolo_)
        for produccion in self._indice.get(simbolo_, ()):
            if produccion.es_vacia:
                yield Nodo(etiqueta, [Nodo('epsilon')]), pos
                continue
            for hijos, fin in self._generar_secuencia(produccion.derecha, pos):
                yield Nodo(etiqueta, hijos), fin

    def _generar_secuencia(self, simbolos: tuple[str, ...], pos: int):
        if not simbolos:
            yield [], pos
            return
        primero, resto = simbolos[0], simbolos[1:]
        for nodo, medio in self._generar(primero, pos):
            for hijos, fin in self._generar_secuencia(resto, medio):
                yield [nodo, *hijos], fin


def analizar(gramatica: Gramatica, oracion: str, maximo: int = LIMITE_ARBOLES) -> Resultado:
    """Entrada publica del modulo; los demas integrantes pueden importarla."""
    return Analizador(gramatica).analizar(oracion, maximo)
