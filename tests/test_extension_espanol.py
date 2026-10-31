"""Pruebas de la extension al espanol.

Las pruebas no solo comprueban que el codigo funciona: cada bloque documenta
una de las limitaciones del catalogo. Varias afirman explicitamente que una
oracion gramatical en espanol es RECHAZADA, porque ese es el hallazgo.
"""
import unittest

from fase1_extension_espanol.analizador import (
    Analizador,
    ErrorLexicoEspanol,
    analizar,
)
from fase1_extension_espanol.gramatica import (
    construir_v1,
    construir_v2,
    construir_v3,
    medir_explosion,
)
from fase1_extension_espanol.lexico import candidatos
from fase1_extension_espanol.limitaciones import CATALOGO, por_codigo
from fase1_extension_espanol.muro_cfg import (
    ORACIONES_DEMO,
    construir_v3_respectivamente,
    producciones_necesarias,
)


class PruebasLexico(unittest.TestCase):
    def test_entrada_con_rasgos(self):
        (gato,) = candidatos('gato')
        self.assertEqual((gato.categoria, gato.genero, gato.numero), ('SUST', 'm', 'sg'))

    def test_tolera_falta_de_tilde(self):
        self.assertTrue(candidatos('jardín'))
        self.assertTrue(candidatos('jardín'))

    def test_ambiguedad_lexica_de_baja(self):
        """Limitacion L4: una palabra puede pertenecer a dos categorias."""
        categorias = {e.categoria for e in candidatos('baja')}
        self.assertEqual(categorias, {'ADJ', 'V_INTR'})

    def test_palabra_fuera_del_lexico(self):
        with self.assertRaises(ErrorLexicoEspanol):
            analizar(construir_v3(), 'el dragon duerme')


class PruebasV1Sobregenera(unittest.TestCase):
    """Limitacion L1: sin rasgos, la CFG acepta cualquier discordancia."""

    def setUp(self):
        self.v1 = construir_v1()

    def test_acepta_oracion_correcta(self):
        self.assertTrue(analizar(self.v1, 'el gato negro duerme').aceptada)

    def test_tambien_acepta_oracion_incorrecta(self):
        self.assertTrue(analizar(self.v1, 'la gato negros duerme').aceptada)

    def test_acepta_discordancia_sujeto_verbo(self):
        self.assertTrue(analizar(self.v1, 'el gato duermen').aceptada)


class PruebasV2Concordancia(unittest.TestCase):
    def setUp(self):
        self.v2 = construir_v2()

    def test_acepta_concordancia_completa(self):
        self.assertTrue(analizar(self.v2, 'el gato negro duerme').aceptada)
        self.assertTrue(analizar(self.v2, 'las gatas negras duermen').aceptada)

    def test_rechaza_genero_determinante_sustantivo(self):
        self.assertFalse(analizar(self.v2, 'la gato duerme').aceptada)

    def test_rechaza_genero_sustantivo_adjetivo(self):
        self.assertFalse(analizar(self.v2, 'el gato negra duerme').aceptada)

    def test_rechaza_numero_determinante_sustantivo(self):
        self.assertFalse(analizar(self.v2, 'los gato duermen').aceptada)

    def test_rechaza_numero_sujeto_verbo(self):
        self.assertFalse(analizar(self.v2, 'el gato duermen').aceptada)
        self.assertFalse(analizar(self.v2, 'los gatos duerme').aceptada)

    def test_objeto_no_concuerda_con_el_verbo(self):
        """El objeto directo lleva sus propios rasgos, independientes del verbo."""
        self.assertTrue(analizar(self.v2, 'el gato ve las gatas').aceptada)


class PruebasV3Modificadores(unittest.TestCase):
    def setUp(self):
        self.v3 = construir_v3()

    def test_adjetivo(self):
        self.assertTrue(analizar(self.v3, 'el gato negro duerme').aceptada)

    def test_varios_adjetivos(self):
        self.assertTrue(analizar(self.v3, 'el gato pequeño negro duerme').aceptada)

    def test_adverbio(self):
        self.assertTrue(analizar(self.v3, 'el gato duerme rápidamente').aceptada)

    def test_frase_preposicional_en_el_nombre(self):
        self.assertTrue(analizar(self.v3, 'el gato de la casa duerme').aceptada)

    def test_frase_preposicional_en_el_verbo(self):
        self.assertTrue(analizar(self.v3, 'el gato duerme en la casa').aceptada)

    def test_concordancia_dentro_del_modificador(self):
        self.assertFalse(analizar(self.v3, 'el gato negra duerme').aceptada)


class PruebasV3Subordinada(unittest.TestCase):
    def setUp(self):
        self.v3 = construir_v3()

    def test_relativa_con_sujeto_singular(self):
        resultado = analizar(self.v3, 'el gato que duerme ve el ratón')
        self.assertTrue(resultado.aceptada)
        self.assertIn('Subordinada relativa', resultado.arboles[0].texto())

    def test_relativa_con_sujeto_plural(self):
        self.assertTrue(analizar(self.v3, 'los gatos que duermen ven los ratones').aceptada)

    def test_relativa_rompe_concordancia(self):
        """Limitacion L5: el rasgo de numero viaja hasta el verbo subordinado."""
        self.assertFalse(analizar(self.v3, 'el gato que duermen ve el ratón').aceptada)
        self.assertFalse(analizar(self.v3, 'los gatos que duerme ven los ratones').aceptada)

    def test_concordancia_a_distancia(self):
        """El sujeto y su verbo quedan separados por la subordinada completa."""
        self.assertTrue(analizar(self.v3, 'el gato que ve los ratones duerme').aceptada)
        self.assertFalse(analizar(self.v3, 'el gato que ve los ratones duermen').aceptada)


class PruebasAmbiguedad(unittest.TestCase):
    """Limitacion L3: la ambiguedad crece segun los numeros de Catalan."""

    def setUp(self):
        self.analizador = Analizador(construir_v3())

    def test_adjuncion_preposicional_es_ambigua(self):
        self.assertEqual(self.analizador.contar('el niño ve el telescopio en la casa'), 2)

    def test_la_ambiguedad_crece(self):
        serie = [
            self.analizador.contar('el niño ve el telescopio'),
            self.analizador.contar('el niño ve el telescopio en la casa'),
            self.analizador.contar('el niño ve el telescopio en la casa con la mujer'),
            self.analizador.contar(
                'el niño ve el telescopio en la casa con la mujer de el jardín'),
        ]
        self.assertEqual(serie, [1, 2, 5, 14])

    def test_se_construyen_los_dos_arboles(self):
        resultado = analizar(construir_v3(), 'el niño ve el telescopio en la casa')
        self.assertEqual(len(resultado.arboles), 2)
        self.assertNotEqual(resultado.arboles[0].texto(), resultado.arboles[1].texto())
        self.assertTrue(resultado.ambigua)


class PruebasExplosion(unittest.TestCase):
    """Limitacion L2: la concordancia es posible pero cuesta producciones."""

    def test_tamanios_conocidos(self):
        self.assertEqual(len(construir_v1()), 5)
        self.assertEqual(len(construir_v2()), 22)
        self.assertEqual(len(construir_v3()), 49)

    def test_agregar_un_rasgo_multiplica_la_gramatica(self):
        sin_persona = len(construir_v3(('genero', 'numero')))
        con_persona = len(construir_v3(('genero', 'numero', 'persona')))
        self.assertGreater(con_persona, sin_persona * 3)

    def test_la_tabla_reporta_el_factor(self):
        filas = medir_explosion()
        self.assertEqual(filas[0]['factor_vs_v1'], 1.0)
        self.assertGreater(filas[-1]['factor_vs_v1'], 30)


class PruebasMuroNoCFG(unittest.TestCase):
    """Limitacion L6: coordinacion distributiva con 'respectivamente'."""

    def test_parche_para_n2_acepta_la_correcta(self):
        g2 = construir_v3_respectivamente(2)
        self.assertTrue(analizar(g2, ORACIONES_DEMO['correcta_n2'], 1).aceptada)

    def test_parche_rechaza_rasgos_cruzados(self):
        g2 = construir_v3_respectivamente(2)
        self.assertFalse(analizar(g2, ORACIONES_DEMO['cruzada_n2'], 1).aceptada)

    def test_el_parche_no_generaliza_a_n3(self):
        """Cada longitud nueva exige reglas nuevas: no hay CFG finita para todo n."""
        g2 = construir_v3_respectivamente(2)
        g3 = construir_v3_respectivamente(3)
        self.assertFalse(analizar(g2, ORACIONES_DEMO['correcta_n3'], 1).aceptada)
        self.assertTrue(analizar(g3, ORACIONES_DEMO['correcta_n3'], 1).aceptada)

    def test_el_costo_es_exponencial(self):
        self.assertEqual(producciones_necesarias(2), 16)
        self.assertEqual(producciones_necesarias(3), 16 + 64)
        self.assertEqual(producciones_necesarias(4), 16 + 64 + 256)

    def test_v3_sola_rechaza_la_construccion(self):
        self.assertFalse(analizar(construir_v3(), ORACIONES_DEMO['correcta_n2'], 1).aceptada)

    def test_requiere_al_menos_dos_coordinados(self):
        with self.assertRaises(ValueError):
            construir_v3_respectivamente(1)


class PruebasCatalogo(unittest.TestCase):
    def test_hay_seis_limitaciones_documentadas(self):
        self.assertEqual(len(CATALOGO), 6)

    def test_solo_una_excede_las_cfg(self):
        fuera = [l.codigo for l in CATALOGO if not l.sigue_siendo_cfg]
        self.assertEqual(fuera, ['L6'])

    def test_cada_limitacion_tiene_nivel_y_evidencia(self):
        for limitacion in CATALOGO:
            self.assertTrue(limitacion.nivel_chomsky)
            self.assertTrue(limitacion.evidencia)
            self.assertTrue(limitacion.regla_que_falla)

    def test_busqueda_por_codigo(self):
        self.assertIn('respectivamente', por_codigo('l6').fenomeno)
        with self.assertRaises(KeyError):
            por_codigo('L99')


class PruebasRecursionIzquierda(unittest.TestCase):
    """Guarda defensiva: si alguien agrega recursion izquierda, falla con mensaje."""

    def test_detecta_recursion_izquierda(self):
        from fase1_extension_espanol.gramatica import Gramatica, Produccion
        mala = Gramatica('mala', 'X', (
            Produccion('X', ('X', 'SUST')),
            Produccion('X', ('SUST',)),
        ))
        with self.assertRaises(RecursionError):
            analizar(mala, 'gato')


if __name__ == '__main__':
    unittest.main()
