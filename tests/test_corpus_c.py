"""Pruebas del corpus de C.  python -m unittest tests.test_corpus_c -v"""
import unittest

from fase1_parser_formal.parser import analizar_codigo
from comparacion_nlp.casos_c import CASOS, por_categoria
from comparacion_nlp.ejecutar_pruebas_c import veredicto


def _buscar(nodo, etiqueta):
    if nodo.etiqueta == etiqueta:
        yield nodo
    for hijo in nodo.hijos:
        yield from _buscar(hijo, etiqueta)


class CorpusC(unittest.TestCase):
    def test_tamano_del_corpus(self):
        self.assertEqual(len(por_categoria('valido')), 12)
        self.assertEqual(len(por_categoria('invalido_c')), 14)
        self.assertEqual(len(por_categoria('fuera_subconjunto')), 7)

    def test_ids_unicos(self):
        ids = [c.id for c in CASOS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_cada_caso_se_comporta_como_se_declaro(self):
        for caso in CASOS:
            with self.subTest(caso=caso.id, nota=caso.nota):
                ok, detalle = veredicto(caso)
                self.assertTrue(ok, detalle)

    def test_todos_los_validos_producen_arbol(self):
        for caso in por_categoria('valido'):
            with self.subTest(caso=caso.id):
                self.assertEqual(analizar_codigo(caso.codigo).etiqueta, 'Programa C')

    def test_else_colgante_se_asocia_al_if_mas_cercano(self):
        arbol = analizar_codigo(next(c for c in CASOS if c.id == 'V09').codigo)
        externo, interno = list(_buscar(arbol, 'Condicional if'))[:2]
        self.assertEqual(len(list(_buscar(interno, 'Si no'))), 1)
        self.assertEqual(len(list(_buscar(externo, 'Si no'))), 1)  # el del interno, anidado
        # el 'Si no' del externo seria hijo directo suyo: no debe existir
        self.assertNotIn('Si no', [h.etiqueta for h in externo.hijos])

    def test_precedencia_multiplicacion_dentro_de_suma(self):
        arbol = analizar_codigo('int main(){int a=1+2*3;return 0;}')
        suma = next(_buscar(arbol, 'Expresión +'))
        self.assertTrue(list(_buscar(suma, 'Término *')))

    def test_posicion_de_error_multilinea(self):
        with self.assertRaises(ValueError) as ctx:
            analizar_codigo('int main() {\n    int edad = 18\n    return 0;\n}\n')
        self.assertIn('línea 3, columna 5', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
