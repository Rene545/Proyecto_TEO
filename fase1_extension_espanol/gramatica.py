"""Las tres versiones de la gramatica del espanol, como producciones explicitas.

Represento las producciones como datos (no como funciones de un parser
descendente escrito a mano) por una razon concreta: asi puedo CONTAR cuantas
reglas necesita cada version. La explosion combinatoria deja de ser una
afirmacion y pasa a ser un numero medible.

Las tres versiones son incrementales y cada una existe para mostrar una cosa:

  v1  CFG ingenua, categorias sin rasgos. Acepta oraciones mal formadas
      (sobregenera) porque nada liga el determinante con el sustantivo.
  v2  Concordancia real, codificada partiendo cada no terminal en una copia
      por combinacion de rasgos. Funciona, pero |P| crece como el producto de
      las cardinalidades de los rasgos.
  v3  v2 + modificadores (adjetivo, adverbio, frase preposicional) + una
      subordinada relativa. Sigue siendo CFG, pero aparece ambiguedad
      estructural genuina y el numero de arboles por oracion se dispara.

El limite que ya NO es libre de contexto esta en muro_cfg.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from fase1_extension_espanol.lexico import (
    CATEGORIAS_LEXICAS,
    RASGOS_POR_CATEGORIA,
    VALORES_POR_RASGO,
)

RASGOS_NOMINALES = ('genero', 'numero')
RASGOS_VERBALES = ('numero', 'persona')
RASGOS_POR_DEFECTO = ('genero', 'numero')


@dataclass(frozen=True)
class Produccion:
    izquierda: str
    derecha: tuple[str, ...]

    def __str__(self) -> str:
        cuerpo = ' '.join(self.derecha) if self.derecha else 'epsilon'
        return f'{self.izquierda} -> {cuerpo}'

    @property
    def es_vacia(self) -> bool:
        return not self.derecha


@dataclass(frozen=True)
class Gramatica:
    nombre: str
    inicial: str
    producciones: tuple[Produccion, ...]
    descripcion: str = ''

    def __len__(self) -> int:
        return len(self.producciones)

    @property
    def no_terminales(self) -> tuple[str, ...]:
        return tuple(sorted({p.izquierda for p in self.producciones}))

    def por_izquierda(self, simbolo: str) -> tuple[Produccion, ...]:
        return tuple(p for p in self.producciones if p.izquierda == simbolo)

    def texto(self) -> str:
        """Gramatica en notacion BNF, agrupada por no terminal."""
        lineas = [f'# Gramatica {self.nombre}  ({len(self)} producciones)']
        if self.descripcion:
            lineas.append(f'# {self.descripcion}')
        for nt in self.no_terminales:
            for produccion in self.por_izquierda(nt):
                lineas.append(str(produccion))
        return '\n'.join(lineas)


# --------------------------------------------------------------------------
# Manejo de simbolos con rasgos:  FN[genero=m,numero=sg]
# --------------------------------------------------------------------------

def simbolo(nombre: str, rasgos: dict[str, str] | None = None) -> str:
    if not rasgos:
        return nombre
    cuerpo = ','.join(f'{k}={v}' for k, v in sorted(rasgos.items()))
    return f'{nombre}[{cuerpo}]'


def partes(simbolo_: str) -> tuple[str, dict[str, str]]:
    """Separa 'FN[genero=m,numero=sg]' en ('FN', {'genero':'m','numero':'sg'})."""
    if '[' not in simbolo_:
        return simbolo_, {}
    nombre, resto = simbolo_.split('[', 1)
    pares = [p for p in resto.rstrip(']').split(',') if p]
    return nombre, dict(par.split('=', 1) for par in pares)


def es_categoria_lexica(simbolo_: str) -> bool:
    return partes(simbolo_)[0] in CATEGORIAS_LEXICAS


def _combinaciones(rasgos: tuple[str, ...]) -> list[dict[str, str]]:
    """Producto cartesiano de los valores de los rasgos activos."""
    activos = tuple(r for r in rasgos if r in VALORES_POR_RASGO)
    if not activos:
        return [{}]
    valores = [VALORES_POR_RASGO[r] for r in activos]
    return [dict(zip(activos, combo)) for combo in product(*valores)]


def _proyectar(combo: dict[str, str], permitidos: tuple[str, ...]) -> dict[str, str]:
    return {k: v for k, v in combo.items() if k in permitidos}


def _lex(categoria: str, combo: dict[str, str]) -> str:
    """Simbolo lexico con solo los rasgos que esa categoria realmente tiene."""
    return simbolo(categoria, _proyectar(combo, RASGOS_POR_CATEGORIA[categoria]))


# --------------------------------------------------------------------------
# v1: sin rasgos, sin concordancia
# --------------------------------------------------------------------------

def construir_v1() -> Gramatica:
    producciones = (
        Produccion('O', ('FN', 'FV')),
        Produccion('FN', ('DET', 'SUST')),
        Produccion('FN', ('DET', 'SUST', 'ADJ')),
        Produccion('FV', ('V_INTR',)),
        Produccion('FV', ('V_TRANS', 'FN')),
    )
    return Gramatica(
        'v1', 'O', producciones,
        'CFG ingenua: categorias sin rasgos. Sobregenera: acepta discordancias.',
    )


# --------------------------------------------------------------------------
# v2: concordancia por particion de no terminales
# --------------------------------------------------------------------------

def construir_v2(rasgos: tuple[str, ...] = RASGOS_POR_DEFECTO) -> Gramatica:
    """Una copia de cada regla nominal por combinacion de rasgos.

    `rasgos` es parametrizable a proposito: pasando ('genero','numero','persona')
    se mide cuanto crece |P| al agregar un rasgo mas. Con persona activa la
    gramatica ya no analiza (el lexico solo tiene 3a persona); sirve para contar.
    """
    producciones: list[Produccion] = []
    combos_nominales = _combinaciones(rasgos)
    combos_verbales = _combinaciones(tuple(r for r in rasgos if r in RASGOS_VERBALES))

    for combo in combos_nominales:
        fn = simbolo('FN', combo)
        fv = simbolo('FV', _proyectar(combo, RASGOS_VERBALES))
        # La concordancia sujeto-verbo se impone aqui: el mismo numero aparece
        # en el no terminal del sujeto y en el del verbo.
        producciones.append(Produccion('O', (fn, fv)))
        producciones.append(Produccion(fn, (_lex('DET', combo), _lex('SUST', combo))))
        producciones.append(Produccion(fn, (_lex('DET', combo), _lex('SUST', combo),
                                            _lex('ADJ', combo))))

    for combo in combos_verbales:
        fv = simbolo('FV', combo)
        producciones.append(Produccion(fv, (_lex('V_INTR', combo),)))
        # El objeto directo no concuerda con el verbo: hay que repetir la regla
        # una vez por cada combinacion posible del objeto.
        for combo_objeto in combos_nominales:
            producciones.append(Produccion(fv, (_lex('V_TRANS', combo),
                                                simbolo('FN', combo_objeto))))

    return Gramatica(
        'v2', 'O', tuple(producciones),
        'Concordancia det-sust-adj y sujeto-verbo por particion de no terminales.',
    )


# --------------------------------------------------------------------------
# v3: v2 + modificadores + subordinada relativa
# --------------------------------------------------------------------------

def construir_v3(rasgos: tuple[str, ...] = RASGOS_POR_DEFECTO) -> Gramatica:
    """Agrega modificadores y una subordinada de relativo.

    Escribo las listas de modificadores con recursion a la DERECHA
    (MODN -> ADJ MODN) y no a la izquierda. No es cosmetico: un analizador
    descendente no termina con recursion izquierda, y quiero conservar el mismo
    estilo de analisis de la fase 1.
    """
    producciones: list[Produccion] = []
    combos_nominales = _combinaciones(rasgos)
    combos_verbales = _combinaciones(tuple(r for r in rasgos if r in RASGOS_VERBALES))

    for combo in combos_nominales:
        combo_v = _proyectar(combo, RASGOS_VERBALES)
        fn = simbolo('FN', combo)
        nuc = simbolo('NUC', combo)
        modn = simbolo('MODN', combo)

        producciones.append(Produccion('O', (fn, simbolo('FV', combo_v))))
        producciones.append(Produccion(fn, (_lex('DET', combo), nuc)))
        producciones.append(Produccion(nuc, (_lex('SUST', combo), modn)))
        producciones.append(Produccion(modn, ()))
        producciones.append(Produccion(modn, (_lex('ADJ', combo), modn)))
        producciones.append(Produccion(modn, ('FPREP', modn)))
        # La subordinada hereda el numero del sustantivo al que modifica:
        # "el gato que duerme" / "los gatos que duermen".
        producciones.append(Produccion(modn, (simbolo('SUBORD', combo_v), modn)))

    for combo in combos_verbales:
        fv = simbolo('FV', combo)
        nucv = simbolo('NUCV', combo)
        producciones.append(Produccion(simbolo('SUBORD', combo),
                                       ('PRON_REL', fv)))
        producciones.append(Produccion(fv, (nucv, 'MODV')))
        producciones.append(Produccion(nucv, (_lex('V_INTR', combo),)))
        for combo_objeto in combos_nominales:
            producciones.append(Produccion(nucv, (_lex('V_TRANS', combo),
                                                  simbolo('FN', combo_objeto))))

    for combo_objeto in combos_nominales:
        producciones.append(Produccion('FPREP', ('PREP', simbolo('FN', combo_objeto))))

    producciones.append(Produccion('MODV', ()))
    producciones.append(Produccion('MODV', ('ADV', 'MODV')))
    producciones.append(Produccion('MODV', ('FPREP', 'MODV')))

    return Gramatica(
        'v3', 'O', tuple(producciones),
        'v2 + adjetivos, adverbios, frases preposicionales y subordinada relativa.',
    )


VERSIONES = {
    'v1': construir_v1,
    'v2': construir_v2,
    'v3': construir_v3,
}


def medir_explosion() -> list[dict[str, object]]:
    """Tamanio de cada gramatica, incluyendo la variante con el rasgo persona.

    Es la evidencia numerica de que la concordancia no es imposible en una CFG,
    sino carisima: |P| crece como el producto de las cardinalidades.
    """
    filas = [
        {'gramatica': 'v1', 'rasgos': 'ninguno',
         'combinaciones': 1, 'producciones': len(construir_v1())},
        {'gramatica': 'v2', 'rasgos': 'genero x numero',
         'combinaciones': 4, 'producciones': len(construir_v2(('genero', 'numero')))},
        {'gramatica': 'v2', 'rasgos': 'genero x numero x persona',
         'combinaciones': 12,
         'producciones': len(construir_v2(('genero', 'numero', 'persona')))},
        {'gramatica': 'v3', 'rasgos': 'genero x numero',
         'combinaciones': 4, 'producciones': len(construir_v3(('genero', 'numero')))},
        {'gramatica': 'v3', 'rasgos': 'genero x numero x persona',
         'combinaciones': 12,
         'producciones': len(construir_v3(('genero', 'numero', 'persona')))},
    ]
    base = filas[0]['producciones']
    for fila in filas:
        fila['factor_vs_v1'] = round(fila['producciones'] / base, 1)
    return filas
