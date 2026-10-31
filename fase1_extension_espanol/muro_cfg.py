"""El punto donde el espanol deja de ser libre de contexto.

Todo lo de gramatica.py sigue siendo de tipo 2 (libre de contexto): la
concordancia local es caras pero posible. Este modulo documenta la
construccion que SI queda por encima de las CFG.

La construccion: coordinacion distributiva con "respectivamente".

    "el niño y la niña son alto y baja respectivamente"

Con n sujetos coordinados y n adjetivos coordinados, el adjetivo i-esimo debe
concordar con el sujeto i-esimo. Si escribo la secuencia de rasgos de los
sujetos como w y la de los adjetivos como w', la oracion es gramatical solo
cuando w = w'. O sea: el lenguaje de las cadenas de rasgos aceptables es

    L = { w c w  |  w en {m_sg, m_pl, f_sg, f_pl}* }

donde c es el separador ("son"). Y { w c w } es el ejemplo de libro de
lenguaje NO libre de contexto: se demuestra con el lema de bombeo para CFL.
Es un lenguaje de tipo 1 (dependiente del contexto), reconocible por un
automata lineal acotado, pero no por un automata de pila.

Demostracion de que no hay CFG finita: para cada n FIJO si puedo escribir una
CFG, enumerando una produccion por cada secuencia de rasgos posible. Lo que no
puedo es cubrir todo n, porque haria falta un numero infinito de producciones.
La funcion producciones_necesarias() muestra que el costo ya es exponencial
antes de volverse infinito.

Esto es lo mismo que en la literatura se llama dependencia cruzada
(cross-serial dependency), el argumento clasico contra las CFG como modelo del
aleman suizo y del holandes.
"""
from __future__ import annotations

from itertools import product

from fase1_extension_espanol.gramatica import (
    Gramatica,
    Produccion,
    RASGOS_POR_DEFECTO,
    _combinaciones,
    _lex,
    construir_v3,
    simbolo,
)


def producciones_necesarias(n_max: int, rasgos: tuple[str, ...] = RASGOS_POR_DEFECTO) -> int:
    """Cuantas producciones hacen falta para cubrir coordinaciones de 2..n_max.

    Es la suma de |combinaciones|^k para k = 2..n_max: exponencial en n.
    """
    base = len(_combinaciones(rasgos))
    return sum(base ** k for k in range(2, n_max + 1))


def construir_v3_respectivamente(
        n_max: int = 2,
        rasgos: tuple[str, ...] = RASGOS_POR_DEFECTO) -> Gramatica:
    """v3 parcheada para cubrir coordinaciones distributivas de hasta n_max.

    Cada produccion fija la secuencia completa de rasgos de los sujetos y la
    repite en los adjetivos. Es la unica forma de forzar w = w' con reglas
    libres de contexto: enumerar.
    """
    if n_max < 2:
        raise ValueError('La coordinacion distributiva necesita al menos 2 elementos')
    base = construir_v3(rasgos)
    producciones = list(base.producciones)
    combos = _combinaciones(rasgos)

    for k in range(2, n_max + 1):
        for secuencia in product(combos, repeat=k):
            lado_sujetos: list[str] = []
            for indice, combo in enumerate(secuencia):
                if indice:
                    lado_sujetos.append('CONJ')
                lado_sujetos.append(simbolo('FN', combo))
            lado_adjetivos: list[str] = []
            for indice, combo in enumerate(secuencia):
                if indice:
                    lado_adjetivos.append('CONJ')
                lado_adjetivos.append(_lex('ADJ', combo))
            derecha = (*lado_sujetos,
                       _lex('COP', {'numero': 'pl', 'persona': '3'}),
                       *lado_adjetivos,
                       'RESP')
            producciones.append(Produccion('O', derecha))

    return Gramatica(
        f'v3+resp(n<={n_max})', 'O', tuple(producciones),
        f'v3 mas coordinacion distributiva enumerada hasta n={n_max}.',
    )


def tabla_costo(hasta: int = 7, rasgos: tuple[str, ...] = RASGOS_POR_DEFECTO) -> list[dict[str, int]]:
    """Costo en producciones de cubrir coordinaciones cada vez mas largas."""
    filas = []
    for n_max in range(2, hasta + 1):
        filas.append({
            'n_max': n_max,
            'producciones_distributivas': producciones_necesarias(n_max, rasgos),
            'total_gramatica': len(construir_v3_respectivamente(n_max, rasgos)),
        })
    return filas


ORACIONES_DEMO = {
    'correcta_n2': 'el niño y la niña son alto y baja respectivamente',
    'cruzada_n2': 'el niño y la niña son alta y bajo respectivamente',
    'correcta_n3': 'el niño y la niña y los gatos son alto y baja y negros respectivamente',
}

ARGUMENTO_FORMAL = """\
Por que esto no es libre de contexto
------------------------------------
1. En "A1 y A2 y ... y An son J1 y J2 y ... y Jn respectivamente" el adjetivo
   Ji debe concordar con el sujeto Ai. La dependencia es cruzada, no anidada.
2. Abstrayendo cada grupo nominal a su par de rasgos, el conjunto de cadenas
   gramaticales es isomorfo a  L = { w c w | w en Sigma* }, con |Sigma| = 4.
3. { w c w } no es libre de contexto. Prueba por el lema de bombeo: para
   cualquier constante de bombeo p, la cadena  z = a^p b^p c a^p b^p  esta en L
   y |z| >= p; en cualquier descomposicion z = uvwxy con |vwx| <= p y |vx| >= 1,
   el segmento vwx no puede tocar las dos copias de w a la vez (estan separadas
   por mas de p simbolos), asi que bombear altera una copia y no la otra, y
   uv^2wx^2y deja de pertenecer a L. Contradiccion.
4. L si es dependiente del contexto (tipo 1): lo reconoce un automata lineal
   acotado que compara las dos mitades. El salto es exactamente tipo 2 -> tipo 1.
5. Consecuencia practica: para cada n fijo existe una CFG (enumerando las 4^n
   secuencias de rasgos), pero no existe una CFG finita que cubra todo n.

Contraargumento honesto
-----------------------
El argumento formal exige n no acotado. En el uso real nadie coordina veinte
sujetos, asi que para el espanol efectivamente producible una CFG gigantesca
alcanzaria. La distincion es la clasica de Chomsky entre competencia (el
sistema, donde n no esta acotado) y actuacion (lo que de hecho se dice). La
limitacion es de competencia, y es la que importa al clasificar el lenguaje
dentro de la jerarquia.
"""
