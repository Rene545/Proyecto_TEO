"""Pruebas del análisis formal.  python -m unittest tests.test_analisis_formal -v

Fijan que los resultados teóricos que se citan en el informe coinciden entre
dos implementaciones distintas: la del equipo (analizador, muro_cfg,
comparar) y la verificación independiente de analisis_formal. Ninguna prueba
necesita NLTK ni spaCy; la clasificación de los falsos positivos de spaCy se
prueba con objetos simulados, igual que en test_comparacion_nlp.
"""
import unittest
from types import SimpleNamespace as NS

from analisis_formal import verificar_teoria as vt
from analisis_formal.inspeccionar_spacy import clasificar
from comparacion_nlp.comparar import evaluar_propio, metricas
from comparacion_nlp.oro import cargar
from fase1_extension_espanol.analizador import Analizador
from fase1_extension_espanol.gramatica import construir_v3
from fase1_extension_espanol.lexico import candidatos, tokenizar
from fase1_extension_espanol.muro_cfg import ORACIONES_DEMO, producciones_necesarias

FRASES_PREP = ['en la casa', 'con la mujer', 'de el jardín', 'en la casa', 'con el hombre', 'de la niña']


class AmbiguedadCatalan(unittest.TestCase):
    """L3: la serie de análisis son números de Catalan, por dos caminos."""

    def test_gramatica_abstracta_da_catalan(self):
        for k in range(8):
            with self.subTest(k=k):
                self.assertEqual(vt.contar_arboles(['V', 'N'] + ['P', 'N'] * k), vt.catalan(k + 1))

    def test_analizador_del_equipo_continua_la_serie(self):
        """El equipo fijó 1, 2, 5, 14; aquí se comprueba que sigue 42, 132, 429."""
        analizador = Analizador(construir_v3())
        for k in range(7):
            oracion = ' '.join(['el niño ve el telescopio', *FRASES_PREP[:k]])
            with self.subTest(k=k):
                self.assertEqual(analizador.contar(oracion), vt.catalan(k + 1))


class MuroL6(unittest.TestCase):
    def test_formula_cerrada_coincide_con_muro_cfg(self):
        for n in range(2, 9):
            with self.subTest(n=n):
                self.assertEqual(producciones_necesarias(n), (4 ** (n + 1) - 16) // 3)
                self.assertEqual(producciones_necesarias(n), vt.producciones_l6(n))

    def test_homomorfismo_lleva_la_oracion_correcta_a_wcw(self):
        """Paso 2 de la demostración: h(oración) está en {w c w} solo si concuerda."""
        self.assertTrue(vt.en_lenguaje_copia(homomorfismo(ORACIONES_DEMO['correcta_n2'])))
        self.assertTrue(vt.en_lenguaje_copia(homomorfismo(ORACIONES_DEMO['correcta_n3'])))
        self.assertFalse(vt.en_lenguaje_copia(homomorfismo(ORACIONES_DEMO['cruzada_n2'])))

    def test_lema_de_bombeo_sobre_el_lenguaje_copia(self):
        for p in range(1, 6):
            with self.subTest(p=p):
                ok, revisadas = vt.bombeo_falla_siempre(p)
                self.assertTrue(ok)
                self.assertGreater(revisadas, 0)

    def test_lenguaje_copia(self):
        self.assertTrue(vt.en_lenguaje_copia('abcab'))
        self.assertFalse(vt.en_lenguaje_copia('abcba'))   # eso es w c w^R, que sí es CFL
        self.assertFalse(vt.en_lenguaje_copia('abab'))


class Metricas(unittest.TestCase):
    def test_matrices_del_analisis_coinciden_con_el_gold(self):
        """Las matrices citadas en el informe salen de correr el parser, no se copiaron a mano."""
        casos = cargar()
        real = [c.gramatical_real for c in casos]
        for version, clave in (('v1', 'v1 (sin concordancia)'),
                               ('v2', 'v2 (concordancia)'),
                               ('v3', 'v3 (modif. + relativo)')):
            pred = [f.acepta for f in evaluar_propio(version, casos)]
            m = metricas(pred, real)
            with self.subTest(version=version):
                self.assertEqual((m['TP'], m['FP'], m['FN'], m['TN']), vt.MATRICES[clave])

    def test_intervalo_de_wilson(self):
        bajo, alto = vt.wilson(48, 61)
        self.assertAlmostEqual(bajo, 0.67, places=2)
        self.assertAlmostEqual(alto, 0.87, places=2)
        self.assertEqual(vt.wilson(16, 16)[1], 1.0)

    def test_solo_un_falso_negativo_de_v3_es_limite_formal(self):
        casos = cargar()
        filas = evaluar_propio('v3', casos)
        fn = [c.oracion for c, f in zip(casos, filas) if c.gramatical_real and not f.acepta]
        self.assertEqual(len(fn), 13)
        self.assertEqual([o for o in fn if 'respectivamente' in o],
                         ['el niño y la niña son alto y baja respectivamente'])


class ClasificacionSpacy(unittest.TestCase):
    """Los tres tipos de falso positivo, con tokens simulados."""

    def test_rasgo_vacio(self):
        doc = doc_simulado([('el', 'det', 1, 'Gender=Masc|Number=Sing'),
                            ('gato', 'nsubj', 2, ''),
                            ('duermen', 'ROOT', 2, 'Number=Plur')])
        self.assertEqual(clasificar(doc)[0], 'rasgo_vacio')

    def test_rasgo_asimilado(self):
        doc = doc_simulado([('el', 'det', 1, 'Gender=Masc|Number=Sing'),
                            ('gato', 'nsubj', 3, 'Gender=Masc|Number=Sing'),
                            ('negra', 'amod', 1, 'Gender=Masc|Number=Sing'),
                            ('duerme', 'ROOT', 3, 'Number=Sing')])
        self.assertEqual(clasificar(doc)[0], 'rasgo_asimilado')

    def test_regla_relativa(self):
        doc = doc_simulado([('los', 'det', 1, 'Gender=Masc|Number=Plur'),
                            ('gatos', 'nsubj', 4, 'Gender=Masc|Number=Plur'),
                            ('que', 'nsubj', 3, ''),
                            ('duerme', 'acl', 1, 'Number=Sing'),
                            ('ven', 'ROOT', 4, 'Number=Plur')])
        self.assertEqual(clasificar(doc)[0], 'regla_relativa')


# ---------------------------------------------------------------- auxiliares
SIMBOLO = {('m', 'sg'): 'a', ('f', 'sg'): 'b', ('m', 'pl'): 'd', ('f', 'pl'): 'e'}


def homomorfismo(oracion: str) -> str:
    """h de la demostración: sustantivos y adjetivos -> su par de rasgos; 'son' -> c; lo demás -> ε."""
    salida = []
    for palabra in tokenizar(oracion):
        if palabra == 'son':
            salida.append('c')
            continue
        for e in candidatos(palabra):
            if e.categoria in ('SUST', 'ADJ'):
                salida.append(SIMBOLO[(e.genero, e.numero)])
                break
    return ''.join(salida)


class _Morph:
    def __init__(self, texto: str):
        self.d = dict(par.split('=') for par in texto.split('|') if par)

    def get(self, clave):
        return [self.d[clave]] if clave in self.d else []

    def __str__(self):
        return '|'.join(f'{k}={v}' for k, v in self.d.items())


def doc_simulado(filas):
    """filas: (texto, dep, índice de la cabeza, rasgos UD)."""
    toks = [NS(text=t, dep_=d, i=i, morph=_Morph(m), pos_='') for i, (t, d, _, m) in enumerate(filas)]
    for tok, (_, _, cabeza, _) in zip(toks, filas):
        tok.head = toks[cabeza]
    for tok in toks:
        tok.children = [h for h in toks if h.head is tok and h is not tok]
    return toks


if __name__ == '__main__':
    unittest.main()
