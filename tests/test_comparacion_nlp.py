"""Pruebas del gold y de la comparacion.  python -m unittest tests.test_comparacion_nlp -v

Todo lo que no necesita NLTK ni spaCy se prueba aqui. La parte que si los usa se
valida corriendo `python -m comparacion_nlp.comparar` en una maquina que los tenga.
"""
import unittest
from types import SimpleNamespace as NS

from fase1_extension_espanol.analizador import Analizador
from fase1_extension_espanol.gramatica import es_categoria_lexica, partes, VERSIONES
from fase1_extension_espanol.lexico import tokenizar
from comparacion_nlp.comparar import detectar_discordancias, evaluar_propio, exportar_cfg, metricas
from comparacion_nlp.oro import cargar


class Oro(unittest.TestCase):
    def test_tamanos(self):
        casos = cargar()
        self.assertEqual(sum(c.origen == 'equipo' for c in casos), 51)
        self.assertEqual(sum(c.origen == 'extra' for c in casos), 10)

    def test_v3_cumple_lo_esperado_en_las_51_del_equipo(self):
        casos = [c for c in cargar() if c.origen == 'equipo']
        for caso, fila in zip(casos, evaluar_propio('v3', casos)):
            with self.subTest(oracion=caso.oracion):
                self.assertEqual(fila.acepta, caso.esperado_v3)

    def test_las_tres_que_exceden_son_gramaticales_aunque_v3_las_rechace(self):
        raras = [c for c in cargar() if c.origen == 'equipo' and c.esperado_v3 != c.gramatical_real]
        self.assertEqual(len(raras), 3)
        self.assertTrue(all(c.gramatical_real and not c.esperado_v3 for c in raras))

    def test_los_extras_son_todos_gramaticales_y_v3_no_acepta_ninguno(self):
        extras = [c for c in cargar() if c.origen == 'extra']
        self.assertTrue(all(c.gramatical_real for c in extras))
        self.assertFalse(any(f.acepta for f in evaluar_propio('v3', extras)))

    def test_hay_extras_dentro_y_fuera_del_lexico(self):
        extras = [c for c in cargar() if c.origen == 'extra']
        self.assertTrue(any(c.en_lexico for c in extras))
        self.assertTrue(any(not c.en_lexico for c in extras))

    def test_v1_sobregenera_y_v2_no(self):
        negativas = [c for c in cargar() if c.origen == 'equipo' and not c.gramatical_real]
        self.assertTrue(any(f.acepta for f in evaluar_propio('v1', negativas)))
        self.assertFalse(any(f.acepta for f in evaluar_propio('v2', negativas)))


class Metricas(unittest.TestCase):
    def test_matriz_y_razones(self):
        m = metricas([True, True, False, False, True], [True, False, True, False, True])
        self.assertEqual((m['TP'], m['FP'], m['FN'], m['TN']), (2, 1, 1, 1))
        self.assertEqual(m['precision'], round(2 / 3, 3))
        self.assertEqual(m['cobertura'], round(2 / 3, 3))
        self.assertEqual(m['rechazo_correcto'], 0.5)
        self.assertEqual(m['exactitud'], 0.6)

    def test_division_por_cero_devuelve_none(self):
        self.assertIsNone(metricas([False], [True])['precision'])


def _tok(i, texto, dep, cabeza_i, morph, pos='X'):
    t = NS(i=i, text=texto, dep_=dep, pos_=pos, head=None,
           morph=NS(get=lambda k, m=morph: [m[k]] if k in m else []))
    t._cabeza_i = cabeza_i
    return t


def _doc(*toks):
    for t in toks:
        t.head = toks[t._cabeza_i]
    return list(toks)


class ReglaDeConcordanciaSobreSpacy(unittest.TestCase):
    def test_oracion_concordante_no_se_marca(self):
        doc = _doc(_tok(0, 'el', 'det', 1, {'Gender': 'Masc', 'Number': 'Sing'}),
                   _tok(1, 'gato', 'nsubj', 2, {'Gender': 'Masc', 'Number': 'Sing'}),
                   _tok(2, 'duerme', 'ROOT', 2, {'Number': 'Sing'}))
        self.assertEqual(detectar_discordancias(doc), [])

    def test_genero_distinto_entre_determinante_y_nombre(self):
        doc = _doc(_tok(0, 'la', 'det', 1, {'Gender': 'Fem', 'Number': 'Sing'}),
                   _tok(1, 'gato', 'nsubj', 2, {'Gender': 'Masc', 'Number': 'Sing'}),
                   _tok(2, 'duerme', 'ROOT', 2, {'Number': 'Sing'}))
        self.assertEqual(len(detectar_discordancias(doc)), 1)

    def test_numero_distinto_entre_sujeto_y_verbo(self):
        doc = _doc(_tok(0, 'el', 'det', 1, {'Gender': 'Masc', 'Number': 'Sing'}),
                   _tok(1, 'gato', 'nsubj', 2, {'Gender': 'Masc', 'Number': 'Sing'}),
                   _tok(2, 'duermen', 'ROOT', 2, {'Number': 'Plur'}))
        self.assertIn('Number', detectar_discordancias(doc)[0])

    def test_sin_rasgos_no_se_inventa_discordancia(self):
        doc = _doc(_tok(0, 'que', 'nsubj', 1, {}), _tok(1, 'duerme', 'ROOT', 1, {'Number': 'Sing'}))
        self.assertEqual(detectar_discordancias(doc), [])


def _contar_sobre_exportacion(inicial, prods, palabras):
    """Cuenta derivaciones usando SOLO los datos exportados (sin tocar lexico.py)."""
    por_lhs = {}
    for lhs, rhs, terminal in prods:
        por_lhs.setdefault(lhs, []).append((rhs, terminal))
    memo, activos = {}, set()

    def simbolo(s, pos):
        clave = (s, pos)
        if clave in memo:
            return memo[clave]
        assert clave not in activos, 'recursion izquierda'
        activos.add(clave)
        total = {}
        for rhs, terminal in por_lhs.get(s, ()):
            if terminal:
                if pos < len(palabras) and palabras[pos] == rhs[0]:
                    total[pos + 1] = total.get(pos + 1, 0) + 1
            else:
                for fin, n in secuencia(rhs, pos).items():
                    total[fin] = total.get(fin, 0) + n
        activos.discard(clave)
        memo[clave] = total
        return total

    def secuencia(rhs, pos):
        actual = {pos: 1}
        for s in rhs:
            nuevo = {}
            for p, n in actual.items():
                for fin, m in simbolo(s, p).items():
                    nuevo[fin] = nuevo.get(fin, 0) + n * m
            actual = nuevo
        return actual

    return simbolo(inicial, 0).get(len(palabras), 0)


class ExportacionANLTK(unittest.TestCase):
    ORACIONES = [
        'el gato duerme', 'las gatas negras duermen', 'la gato duerme',
        'el niño ve el telescopio en la casa',
        'el niño ve el telescopio en la casa con la mujer de el jardín',   # 14 analisis
        'el gato que ve los ratones duerme',
    ]

    def test_la_exportacion_reproduce_el_conteo_del_analizador(self):
        gram = VERSIONES['v3']()
        analizador = Analizador(gram)
        for oracion in self.ORACIONES:
            with self.subTest(oracion=oracion):
                palabras = tokenizar(oracion)
                inicial, prods = exportar_cfg(gram, palabras)
                self.assertEqual(_contar_sobre_exportacion(inicial, prods, palabras),
                                 analizador.contar(oracion))

    def test_el_caso_de_catalan_da_14(self):
        gram = VERSIONES['v3']()
        palabras = tokenizar(self.ORACIONES[4])
        inicial, prods = exportar_cfg(gram, palabras)
        self.assertEqual(_contar_sobre_exportacion(inicial, prods, palabras), 14)

    def test_producciones_lexicas_solo_para_palabras_de_la_oracion(self):
        gram = VERSIONES['v3']()
        palabras = tokenizar('el gato duerme')
        _, prods = exportar_cfg(gram, palabras)
        terminales = {rhs[0] for _, rhs, t in prods if t}
        self.assertEqual(terminales, set(palabras))

    def test_los_simbolos_de_las_reglas_originales_no_son_terminales(self):
        gram = VERSIONES['v3']()
        _, prods = exportar_cfg(gram, tokenizar('el gato duerme'))
        for lhs, rhs, terminal in prods:
            if not terminal:
                self.assertTrue(all(isinstance(s, str) for s in rhs))
            else:
                self.assertTrue(es_categoria_lexica(lhs))


if __name__ == '__main__':
    unittest.main()
