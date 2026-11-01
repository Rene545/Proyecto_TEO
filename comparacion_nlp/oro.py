"""Conjunto de oraciones con DOS etiquetas, para no mezclar dos preguntas distintas.

  esperado_v3      lo que la gramatica v3 DEBE hacer (acepta / rechaza). Viene del
                   archivo del equipo validacion/oraciones_espanol.txt ('+' / '-').
  gramatical_real  si la oracion es gramatical en espanol de verdad.

Coinciden casi siempre. Divergen exactamente en las oraciones que excedieron la
CFG ('el gato duerme y el perro ladra'): v3 las rechaza y son gramaticales. Medir
contra 'gramatical_real' es lo que permite hablar de falsos negativos.

Se agregan ademas oraciones EXTRA de espanol natural fuera del alcance, para ver
que pasa cuando el vocabulario o la construccion no estan cubiertos.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from fase1_extension_espanol.lexico import candidatos, tokenizar

ARCHIVO_EQUIPO = Path('validacion/oraciones_espanol.txt')
_CABECERA = re.compile(r'^#\s*---\s*Nivel\s+(\d)\s*(\(negativos\))?\s*:\s*(.*?)\s*---\s*$')


@dataclass(frozen=True)
class CasoEs:
    oracion: str
    nivel: str            # '1', '2', '3' (del equipo) o 'X' (extra fuera de alcance)
    esperado_v3: bool
    gramatical_real: bool
    fenomeno: str
    origen: str           # 'equipo' | 'extra'
    en_lexico: bool       # todas sus palabras estan en el lexico declarado


# (oracion, fenomeno). Todas son gramaticales en espanol.
EXTRAS: tuple[tuple[str, str], ...] = (
    ('El gato come pescado.', 'vocabulario fuera del lexico'),
    ('Los niños juegan en el parque.', 'vocabulario fuera del lexico'),
    ('Yo quiero que tú vengas.', 'primera/segunda persona y subjuntivo'),
    ('María ve a su madre.', 'nombre propio, "a" personal, posesivo'),
    ('No me gusta el café.', 'negacion y pronombre clitico'),
    ('Ayer el perro persiguió al gato.', 'contraccion "al" (de + el)'),
    ('La niña dijo que el gato duerme.', 'subordinada completiva'),
    ('El libro que compró la niña es viejo.', 'relativo de objeto con sujeto pospuesto, todo en el lexico'),
    ('La casa de los niños es pequeña.', 'oracion copulativa con adjetivo, todo en el lexico'),
    ('Duerme el gato.', 'orden verbo-sujeto, todo en el lexico'),
)


def _en_lexico(oracion: str) -> bool:
    return all(candidatos(p) for p in tokenizar(oracion))


def cargar(ruta: Path = ARCHIVO_EQUIPO, incluir_extras: bool = True) -> list[CasoEs]:
    casos: list[CasoEs] = []
    nivel, fenomeno, excede = '1', '', False
    for linea in Path(ruta).read_text(encoding='utf-8').splitlines():
        linea = linea.strip()
        if not linea:
            continue
        if linea.startswith('#'):
            m = _CABECERA.match(linea)
            if m:
                nivel, fenomeno = m.group(1), m.group(3)
                excede = 'exceden' in fenomeno
            continue
        marca, _, oracion = linea.partition(' ')
        esperado = marca == '+'
        casos.append(CasoEs(oracion, nivel, esperado, esperado or excede, fenomeno,
                            'equipo', _en_lexico(oracion)))
    if incluir_extras:
        for oracion, fen in EXTRAS:
            casos.append(CasoEs(oracion, 'X', False, True, fen, 'extra', _en_lexico(oracion)))
    return casos
