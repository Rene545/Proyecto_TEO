"""Ejecuta el corpus de C contra el parser y muestra una tabla.

  python -m comparacion_nlp.ejecutar_pruebas_c                # tabla en pantalla
  python -m comparacion_nlp.ejecutar_pruebas_c --exportar     # escribe validacion/c_corpus/*.c
"""
from __future__ import annotations

import argparse
from pathlib import Path

from fase1_parser_formal.lexer import ErrorLexico
from fase1_parser_formal.parser import ErrorSintactico, analizar_codigo
from comparacion_nlp.casos_c import CASOS, CasoC


def ejecutar(caso: CasoC) -> tuple[bool, str, str | None]:
    """Devuelve (aceptado, clase_de_error, mensaje)."""
    try:
        analizar_codigo(caso.codigo)
        return True, '', None
    except ErrorLexico as e:
        return False, 'lexico', str(e)
    except ErrorSintactico as e:
        return False, 'sintactico', str(e)


def veredicto(caso: CasoC) -> tuple[bool, str]:
    """True si el parser se comporta como el caso declara."""
    aceptado, clase, mensaje = ejecutar(caso)
    if caso.categoria == 'valido':
        return aceptado, 'aceptado' if aceptado else f'RECHAZADO: {mensaje}'
    if aceptado:
        return False, 'ACEPTADO (se esperaba rechazo)'
    if caso.error and clase != caso.error:
        return False, f'error {clase}, se esperaba {caso.error}'
    for fragmento in (caso.donde, caso.contiene):
        if fragmento and fragmento not in (mensaje or ''):
            return False, f'mensaje sin {fragmento!r}: {mensaje}'
    return True, mensaje or ''


def exportar(destino: Path) -> int:
    destino.mkdir(parents=True, exist_ok=True)
    for caso in CASOS:
        prefijo = {'valido': 'valido', 'invalido_c': 'invalido', 'fuera_subconjunto': 'fuera'}[caso.categoria]
        (destino / f'{prefijo}_{caso.id[1:]}.c').write_text(caso.codigo + '\n', encoding='utf-8')
    return len(CASOS)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exportar', action='store_true', help='escribe cada caso como .c en validacion/c_corpus/')
    args = ap.parse_args()
    if args.exportar:
        print(f'{exportar(Path("validacion/c_corpus"))} archivos escritos en validacion/c_corpus/')
        return 0
    fallos = 0
    for caso in CASOS:
        ok, detalle = veredicto(caso)
        fallos += not ok
        print(f'{"OK " if ok else "MAL"} {caso.id} [{caso.categoria:17s}] {caso.nota}')
        print(f'      -> {detalle}')
    print(f'\n{len(CASOS) - fallos}/{len(CASOS)} casos se comportan como se declaro')
    return 1 if fallos else 0


if __name__ == '__main__':
    raise SystemExit(main())
