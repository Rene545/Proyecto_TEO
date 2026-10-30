import argparse
from pathlib import Path
import sys
from fase1_parser_formal.lexer import ErrorLexico
from fase1_parser_formal.parser import ErrorSintactico, analizar_codigo


def main() -> int:
    argumento = argparse.ArgumentParser(description='Parser descendente recursivo de un subconjunto de C')
    grupo = argumento.add_mutually_exclusive_group(required=True)
    grupo.add_argument('--archivo', type=Path, help='Ruta a un archivo C')
    grupo.add_argument('--texto', help='Programa C escrito directamente entre comillas')
    argumento.add_argument('--svg', type=Path, help='Exportar árbol visual como SVG')
    argumento.add_argument('--dot', type=Path, help='Exportar árbol como DOT (Graphviz)')
    args = argumento.parse_args()
    try:
        codigo = args.archivo.read_text(encoding='utf-8') if args.archivo else args.texto
        arbol = analizar_codigo(codigo)
        print('ACEPTADO: la entrada pertenece al subconjunto de C definido.')
        print('\nÁRBOL SINTÁCTICO:\n' + arbol.texto())
        if args.svg:
            arbol.guardar_svg(args.svg)
            print(f'\nÁrbol SVG generado: {args.svg}')
        if args.dot:
            arbol.guardar_dot(args.dot)
            print(f'Archivo DOT generado: {args.dot}')
        return 0
    except (OSError, ErrorLexico, ErrorSintactico) as e:
        print(f'RECHAZADO: {e}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
