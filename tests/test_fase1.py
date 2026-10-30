import unittest
from fase1_parser_formal.parser import analizar_codigo, ErrorSintactico
from fase1_parser_formal.lexer import ErrorLexico


class PruebasParserC(unittest.TestCase):
    def test_declaracion_valida(self):
        self.assertIn('Declaración int', analizar_codigo('int main(){int x=3; return 0;}').texto())

    def test_asignacion_valida(self):
        self.assertIn('Asignación', analizar_codigo('int main(){int x; x=4+2*3;return 0;}').texto())

    def test_if_else(self):
        self.assertIn('Condicional if', analizar_codigo('int main(){if (1<2) {return 1;} else {return 0;}}').texto())

    def test_while(self):
        self.assertIn('Bucle while', analizar_codigo('int main(){int x=0;while (x<3) x=x+1;return x;}').texto())

    def test_precedencia(self):
        arbol = analizar_codigo('int main(){int a=1+2*3;return 0;}').texto()
        self.assertIn('Expresión +', arbol)
        self.assertIn('Término *', arbol)

    def test_parentesis(self):
        self.assertIn('Paréntesis', analizar_codigo('int main(){int a=(1+2)*3;return a;}').texto())

    def test_retorno(self):
        self.assertIn('Return', analizar_codigo('int main(){return -1;}').texto())

    def test_cuerpo_vacio_valido(self):
        self.assertIn('Programa C', analizar_codigo('int main() {}').texto())

    def test_punto_y_coma_faltante(self):
        with self.assertRaises(ErrorSintactico):
            analizar_codigo('int main(){int x=3 return 0;}')

    def test_parentesis_incompleto(self):
        with self.assertRaises(ErrorSintactico):
            analizar_codigo('int main( {return 0;}')

    def test_if_sin_comparacion(self):
        with self.assertRaises(ErrorSintactico):
            analizar_codigo('int main(){if (2) return 0;}')

    def test_caracter_no_valido(self):
        with self.assertRaises(ErrorLexico):
            analizar_codigo('int main(){int x=@;return 0;}')

    def test_codigo_tras_main(self):
        with self.assertRaises(ErrorSintactico):
            analizar_codigo('int main(){} int x=1;')

    def test_dos_sentencias_mal_escritas(self):
        with self.assertRaises(ErrorSintactico):
            analizar_codigo('int main(){int = 4; return 0;}')


if __name__ == '__main__':
    unittest.main()
