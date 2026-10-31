"""Lexico del subconjunto controlado del espanol.

Cada palabra se declara junto con sus rasgos morfologicos (genero, numero,
persona, tiempo). El conjunto de valores posibles es finito y esta fijado aqui
a proposito: una CFG solo puede imponer concordancia si esos rasgos se
codifican dentro de los no terminales, y eso exige conocer de antemano todos
los valores. Ese detalle es exactamente el que despues explica la explosion
combinatoria de la version 2 de la gramatica.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass

GENEROS = ('m', 'f')
NUMEROS = ('sg', 'pl')
PERSONAS = ('1', '2', '3')
TIEMPOS = ('pres', 'pas')

# Valores que puede tomar cada rasgo. La cardinalidad de este diccionario es la
# que multiplica el tamanio de la gramatica en gramatica.construir_v2 / _v3.
VALORES_POR_RASGO: dict[str, tuple[str, ...]] = {
    'genero': GENEROS,
    'numero': NUMEROS,
    'persona': PERSONAS,
}

CATEGORIAS_LEXICAS = frozenset({
    'DET', 'SUST', 'ADJ', 'V_INTR', 'V_TRANS', 'COP',
    'ADV', 'PREP', 'PRON_REL', 'CONJ', 'RESP',
})

# Que rasgos tiene realmente cada categoria. Un adverbio no se flexiona, asi
# que no participa en la explosion; un sustantivo si.
RASGOS_POR_CATEGORIA: dict[str, tuple[str, ...]] = {
    'DET': ('genero', 'numero'),
    'SUST': ('genero', 'numero'),
    'ADJ': ('genero', 'numero'),
    'V_INTR': ('numero', 'persona'),
    'V_TRANS': ('numero', 'persona'),
    'COP': ('numero', 'persona'),
    'ADV': (),
    'PREP': (),
    'PRON_REL': (),
    'CONJ': (),
    'RESP': (),
}


@dataclass(frozen=True)
class Entrada:
    """Una forma flexionada concreta con sus rasgos."""

    palabra: str
    categoria: str
    genero: str | None = None
    numero: str | None = None
    persona: str | None = None
    tiempo: str | None = None

    def rasgo(self, nombre: str) -> str | None:
        return getattr(self, nombre, None)

    def cumple(self, exigidos: dict[str, str]) -> bool:
        """True si la entrada satisface todos los rasgos pedidos."""
        return all(self.rasgo(clave) == valor for clave, valor in exigidos.items())

    def etiqueta(self) -> str:
        rasgos = [v for v in (self.genero, self.numero) if v]
        sufijo = f" [{','.join(rasgos)}]" if rasgos else ''
        return f'{ABREVIATURAS.get(self.categoria, self.categoria)}: {self.palabra}{sufijo}'


ABREVIATURAS = {
    'DET': 'Det', 'SUST': 'Sust', 'ADJ': 'Adj', 'V_INTR': 'V.intr',
    'V_TRANS': 'V.trans', 'COP': 'Cop', 'ADV': 'Adv', 'PREP': 'Prep',
    'PRON_REL': 'Rel', 'CONJ': 'Conj', 'RESP': 'Adv.resp',
}


def _cuatro_formas(categoria: str, ms: str, fs: str, mp: str, fp: str) -> tuple[Entrada, ...]:
    """Paradigma completo de genero x numero (determinantes y adjetivos)."""
    return (
        Entrada(ms, categoria, genero='m', numero='sg', persona='3'),
        Entrada(fs, categoria, genero='f', numero='sg', persona='3'),
        Entrada(mp, categoria, genero='m', numero='pl', persona='3'),
        Entrada(fp, categoria, genero='f', numero='pl', persona='3'),
    )


def _sustantivo(genero: str, singular: str, plural: str) -> tuple[Entrada, ...]:
    """Un sustantivo tiene genero fijo y solo varia en numero."""
    return (
        Entrada(singular, 'SUST', genero=genero, numero='sg', persona='3'),
        Entrada(plural, 'SUST', genero=genero, numero='pl', persona='3'),
    )


def _verbo(categoria: str, sg_pres: str, pl_pres: str,
           sg_pas: str | None = None, pl_pas: str | None = None) -> tuple[Entrada, ...]:
    """Tercera persona en los dos tiempos que cubre el subconjunto."""
    formas = [
        Entrada(sg_pres, categoria, numero='sg', persona='3', tiempo='pres'),
        Entrada(pl_pres, categoria, numero='pl', persona='3', tiempo='pres'),
    ]
    if sg_pas:
        formas.append(Entrada(sg_pas, categoria, numero='sg', persona='3', tiempo='pas'))
    if pl_pas:
        formas.append(Entrada(pl_pas, categoria, numero='pl', persona='3', tiempo='pas'))
    return tuple(formas)


def _invariables(categoria: str, *palabras: str) -> tuple[Entrada, ...]:
    return tuple(Entrada(p, categoria) for p in palabras)


VOCABULARIO: tuple[Entrada, ...] = (
    # --- determinantes ---
    *_cuatro_formas('DET', 'el', 'la', 'los', 'las'),
    *_cuatro_formas('DET', 'un', 'una', 'unos', 'unas'),
    # --- sustantivos ---
    *_sustantivo('m', 'gato', 'gatos'),
    *_sustantivo('f', 'gata', 'gatas'),
    *_sustantivo('m', 'perro', 'perros'),
    *_sustantivo('f', 'perra', 'perras'),
    *_sustantivo('m', 'niño', 'niños'),
    *_sustantivo('f', 'niña', 'niñas'),
    *_sustantivo('m', 'libro', 'libros'),
    *_sustantivo('f', 'casa', 'casas'),
    *_sustantivo('m', 'jardín', 'jardines'),
    *_sustantivo('m', 'telescopio', 'telescopios'),
    *_sustantivo('m', 'hombre', 'hombres'),
    *_sustantivo('f', 'mujer', 'mujeres'),
    *_sustantivo('m', 'ratón', 'ratones'),
    *_sustantivo('f', 'ventana', 'ventanas'),
    # --- adjetivos ---
    *_cuatro_formas('ADJ', 'negro', 'negra', 'negros', 'negras'),
    *_cuatro_formas('ADJ', 'pequeño', 'pequeña', 'pequeños', 'pequeñas'),
    *_cuatro_formas('ADJ', 'viejo', 'vieja', 'viejos', 'viejas'),
    *_cuatro_formas('ADJ', 'alto', 'alta', 'altos', 'altas'),
    *_cuatro_formas('ADJ', 'bajo', 'baja', 'bajos', 'bajas'),
    # --- verbos intransitivos ---
    *_verbo('V_INTR', 'duerme', 'duermen', 'durmió', 'durmieron'),
    *_verbo('V_INTR', 'ladra', 'ladran', 'ladró', 'ladraron'),
    # "baja" es a la vez ADJ [f,sg] y V_INTR [sg]: ambiguedad lexica deliberada.
    *_verbo('V_INTR', 'baja', 'bajan'),
    # --- verbos transitivos ---
    *_verbo('V_TRANS', 've', 'ven', 'vio', 'vieron'),
    *_verbo('V_TRANS', 'come', 'comen', 'comió', 'comieron'),
    *_verbo('V_TRANS', 'compra', 'compran', 'compró', 'compraron'),
    *_verbo('V_TRANS', 'persigue', 'persiguen', 'persiguió', 'persiguieron'),
    # --- copula (necesaria para la construccion con "respectivamente") ---
    *_verbo('COP', 'es', 'son'),
    # --- invariables ---
    *_invariables('ADV', 'rápidamente', 'lentamente', 'siempre', 'ayer'),
    *_invariables('PREP', 'con', 'en', 'de', 'sobre'),
    *_invariables('PRON_REL', 'que'),
    *_invariables('CONJ', 'y'),
    *_invariables('RESP', 'respectivamente'),
)


def _sin_acentos(palabra: str) -> str:
    """Quita tildes y la virgulilla para tolerar entradas sin acentuar."""
    descompuesta = unicodedata.normalize('NFD', palabra)
    return ''.join(c for c in descompuesta if not unicodedata.combining(c))


def _construir_indices() -> tuple[dict[str, tuple[Entrada, ...]], dict[str, tuple[Entrada, ...]]]:
    exacto: dict[str, list[Entrada]] = {}
    relajado: dict[str, list[Entrada]] = {}
    for entrada in VOCABULARIO:
        exacto.setdefault(entrada.palabra, []).append(entrada)
        relajado.setdefault(_sin_acentos(entrada.palabra), []).append(entrada)
    return ({k: tuple(v) for k, v in exacto.items()},
            {k: tuple(v) for k, v in relajado.items()})


INDICE, INDICE_RELAJADO = _construir_indices()

_PUNTUACION = str.maketrans('', '', '.,;:!?"()')


def tokenizar(oracion: str) -> list[str]:
    """Separa una oracion en palabras en minuscula, sin signos de puntuacion."""
    return oracion.lower().translate(_PUNTUACION).split()


def candidatos(palabra: str, categoria: str | None = None,
               rasgos: dict[str, str] | None = None) -> tuple[Entrada, ...]:
    """Entradas del lexico compatibles con una palabra, categoria y rasgos.

    Devuelve mas de una entrada cuando la palabra es ambigua ("baja").
    """
    clave = palabra.lower()
    entradas = INDICE.get(clave) or INDICE_RELAJADO.get(_sin_acentos(clave)) or ()
    if categoria is not None:
        entradas = tuple(e for e in entradas if e.categoria == categoria)
    if rasgos:
        entradas = tuple(e for e in entradas if e.cumple(rasgos))
    return tuple(entradas)


def resumen() -> dict[str, int]:
    """Cuantas formas hay por categoria (lo uso en el informe)."""
    conteo: dict[str, int] = {}
    for entrada in VOCABULARIO:
        conteo[entrada.categoria] = conteo.get(entrada.categoria, 0) + 1
    return dict(sorted(conteo.items()))
