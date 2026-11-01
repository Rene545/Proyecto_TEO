"""Verifica con NLTK el crecimiento de la ambigüedad (números de Catalan).

  python -m comparacion_nlp.verificar_ambiguedad

Toma las 4 oraciones de la demo --ambiguedad del equipo (0, 1, 2 y 3 frases
preposicionales) y compara cuántos análisis cuenta el parser propio con
cuántos encuentra NLTK usando la misma gramática v3. Esperado: 1, 2, 5, 14.
"""
from __future__ import annotations

from comparacion_nlp.comparar import evaluar_nltk, evaluar_propio
from comparacion_nlp.oro import CasoEs
from fase1_extension_espanol.cli import ORACIONES_AMBIGUEDAD


def main() -> int:
    casos = [CasoEs(o, 'X', True, True, 'ambiguedad', 'extra', True) for o in ORACIONES_AMBIGUEDAD]
    propios = evaluar_propio('v3', casos)
    try:
        nltk_f = evaluar_nltk(casos)
    except ImportError:
        nltk_f = None
        print('[aviso] NLTK no esta instalado: pip install nltk')
    print('| Oración | Propio | NLTK |')
    print('| --- | ---: | ---: |')
    for i, caso in enumerate(casos):
        print(f'| {caso.oracion} | {propios[i].derivaciones} | {nltk_f[i].derivaciones if nltk_f else "n/d"} |')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
