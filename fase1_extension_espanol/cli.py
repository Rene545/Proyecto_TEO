"""Demo ejecutable de la extension al espanol.

Pensado para la presentacion en vivo: cada bandera muestra un hallazgo.

  --oracion "..." [--version v1|v2|v3] [--svg ruta] [--arboles N]
  --lote archivo        corre un archivo de casos y compara con lo esperado
  --gramatica v2        imprime la gramatica en BNF
  --explosion           tabla del crecimiento de |P| al agregar rasgos
  --ambiguedad          crecimiento del numero de analisis (numeros de Catalan)
  --limitaciones        catalogo formal de los puntos de falla
  --muro                demostracion del limite no libre de contexto
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fase1_extension_espanol.analizador import Analizador, ErrorLexicoEspanol, analizar
from fase1_extension_espanol.gramatica import VERSIONES, medir_explosion
from fase1_extension_espanol.limitaciones import CATALOGO
from fase1_extension_espanol.muro_cfg import (
    ARGUMENTO_FORMAL,
    ORACIONES_DEMO,
    construir_v3_respectivamente,
    tabla_costo,
)

ORACIONES_AMBIGUEDAD = [
    'el niño ve el telescopio',
    'el niño ve el telescopio en la casa',
    'el niño ve el telescopio en la casa con la mujer',
    'el niño ve el telescopio en la casa con la mujer de el jardín',
]


def _titulo(texto: str) -> None:
    print()
    print(texto)
    print('-' * len(texto))


def _tabla(filas: list[dict], columnas: list[str]) -> None:
    anchos = {c: max(len(c), *(len(str(f.get(c, ''))) for f in filas)) for c in columnas}
    print('  '.join(c.ljust(anchos[c]) for c in columnas))
    print('  '.join('-' * anchos[c] for c in columnas))
    for fila in filas:
        print('  '.join(str(fila.get(c, '')).ljust(anchos[c]) for c in columnas))


def comando_oracion(args) -> int:
    gramatica = VERSIONES[args.version]()
    resultado = analizar(gramatica, args.oracion, args.arboles)
    print(resultado.resumen())
    if not resultado.aceptada:
        return 1
    for indice, arbol in enumerate(resultado.arboles, start=1):
        _titulo(f'Arbol {indice} de {resultado.derivaciones}')
        print(arbol.texto())
    if resultado.truncado:
        print(f'\n(se muestran {len(resultado.arboles)} de {resultado.derivaciones} analisis)')
    if args.svg:
        resultado.arboles[0].guardar_svg(args.svg)
        print(f'\nArbol SVG generado: {args.svg}')
    return 0


def comando_lote(args) -> int:
    """Formato del archivo:  '+ oracion' se espera aceptada, '- oracion' rechazada."""
    gramatica = VERSIONES[args.version]()
    analizador = Analizador(gramatica)
    aciertos = fallos = 0
    for linea in Path(args.lote).read_text(encoding='utf-8').splitlines():
        linea = linea.strip()
        if not linea or linea.startswith('#'):
            if linea.startswith('#'):
                print(linea)
            continue
        marca, _, oracion = linea.partition(' ')
        esperada = marca == '+'
        try:
            resultado = analizador.analizar(oracion, maximo=1)
            obtenida, detalle = resultado.aceptada, f'{resultado.derivaciones} analisis'
        except ErrorLexicoEspanol as error:
            obtenida, detalle = False, str(error)
        if obtenida == esperada:
            aciertos += 1
            print(f'  ok    {marca} {oracion}  ({detalle})')
        else:
            fallos += 1
            print(f'  FALLA {marca} {oracion}  ({detalle})')
    _titulo(f'Resultado con {gramatica.nombre}')
    print(f'{aciertos} coinciden con lo esperado, {fallos} no')
    return 0 if fallos == 0 else 1


def comando_gramatica(args) -> int:
    print(VERSIONES[args.gramatica]().texto())
    return 0


def comando_explosion() -> int:
    _titulo('Crecimiento del tamanio de la gramatica (limitacion L2)')
    _tabla(medir_explosion(),
           ['gramatica', 'rasgos', 'combinaciones', 'producciones', 'factor_vs_v1'])
    print('\n|P| crece como el producto de las cardinalidades de los rasgos que')
    print('deben concordar. La concordancia es posible en una CFG, pero no es gratis.')
    return 0


def comando_ambiguedad() -> int:
    gramatica = VERSIONES['v3']()
    analizador = Analizador(gramatica)
    filas = []
    for oracion in ORACIONES_AMBIGUEDAD:
        filas.append({
            'frases_preposicionales': oracion.count(' en ') + oracion.count(' con ') + oracion.count(' de '),
            'palabras': len(oracion.split()),
            'analisis': analizador.contar(oracion),
            'oracion': oracion,
        })
    _titulo('Crecimiento de la ambiguedad estructural (limitacion L3)')
    _tabla(filas, ['frases_preposicionales', 'palabras', 'analisis', 'oracion'])
    print('\nLa serie 1, 2, 5, 14 son los numeros de Catalan: la ambiguedad crece')
    print('exponencialmente con el numero de modificadores adjuntables.')
    return 0


def comando_limitaciones() -> int:
    _titulo('Puntos exactos donde falla la extension al espanol')
    for limitacion in CATALOGO:
        print()
        print(limitacion.texto())
    return 0


def comando_muro() -> int:
    g2 = construir_v3_respectivamente(2)
    g3 = construir_v3_respectivamente(3)
    _titulo('Limitacion L6: la coordinacion distributiva no es libre de contexto')
    filas = []
    for clave, oracion in ORACIONES_DEMO.items():
        filas.append({
            'caso': clave,
            'n<=2': 'acepta' if analizar(g2, oracion, 1).aceptada else 'rechaza',
            'n<=3': 'acepta' if analizar(g3, oracion, 1).aceptada else 'rechaza',
            'oracion': oracion,
        })
    _tabla(filas, ['caso', 'n<=2', 'n<=3', 'oracion'])
    print('\nLa gramatica parcheada hasta n=2 acepta la version correcta y rechaza')
    print('la de rasgos cruzados, pero no alcanza para n=3: hay que agregar reglas.')
    _titulo('Costo de cubrir coordinaciones cada vez mas largas')
    _tabla(tabla_costo(7), ['n_max', 'producciones_distributivas', 'total_gramatica'])
    print()
    print(ARGUMENTO_FORMAL)
    return 0


def main() -> int:
    analizador = argparse.ArgumentParser(
        description='Extension de la CFG al espanol y sus limites formales')
    grupo = analizador.add_mutually_exclusive_group(required=True)
    grupo.add_argument('--oracion', help='Oracion en espanol a analizar')
    grupo.add_argument('--lote', help='Archivo de casos de prueba')
    grupo.add_argument('--gramatica', choices=sorted(VERSIONES), help='Imprimir la gramatica en BNF')
    grupo.add_argument('--explosion', action='store_true', help='Tabla de crecimiento de |P|')
    grupo.add_argument('--ambiguedad', action='store_true', help='Crecimiento del numero de analisis')
    grupo.add_argument('--limitaciones', action='store_true', help='Catalogo de puntos de falla')
    grupo.add_argument('--muro', action='store_true', help='Demostracion del limite no-CFG')
    analizador.add_argument('--version', choices=sorted(VERSIONES), default='v3',
                            help='Version de la gramatica (por defecto v3)')
    analizador.add_argument('--arboles', type=int, default=3, help='Maximo de arboles a imprimir')
    analizador.add_argument('--svg', type=Path, help='Guardar el primer arbol como SVG')
    args = analizador.parse_args()

    try:
        if args.oracion:
            return comando_oracion(args)
        if args.lote:
            return comando_lote(args)
        if args.gramatica:
            return comando_gramatica(args)
        if args.explosion:
            return comando_explosion()
        if args.ambiguedad:
            return comando_ambiguedad()
        if args.limitaciones:
            return comando_limitaciones()
        if args.muro:
            return comando_muro()
    except (OSError, ErrorLexicoEspanol, RecursionError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
