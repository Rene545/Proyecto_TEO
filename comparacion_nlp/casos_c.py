"""Corpus de pruebas del parser de C.

Cada caso declara de antemano que se espera. Hay tres categorias, y la
diferencia importa para el informe:

  valido             C valido y dentro del subconjunto: el parser DEBE aceptarlo.
  invalido_c         Invalido tambien en C real: el parser DEBE rechazarlo.
  fuera_subconjunto  C valido en la realidad pero fuera del subconjunto que
                     definio la gramatica: el parser lo rechaza A PROPOSITO.
                     No es un error del parser, es el alcance acotado.

Para los rechazos se fija ademas la clase de error (lexico o sintactico) y,
cuando se verifico a mano, la posicion exacta que se reporta.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CasoC:
    id: str
    categoria: str            # valido | invalido_c | fuera_subconjunto
    codigo: str
    nota: str
    error: str | None = None  # 'lexico' | 'sintactico' (solo si se rechaza)
    donde: str | None = None  # fragmento esperado en el mensaje, p. ej. 'línea 1, columna 20'
    contiene: str | None = None  # fragmento esperado del mensaje


V, I, F = 'valido', 'invalido_c', 'fuera_subconjunto'

CASOS: tuple[CasoC, ...] = (
    # ---------------- validos ----------------
    CasoC('V01', V, 'int main() {}', 'cuerpo vacio'),
    CasoC('V02', V, 'int main(){int x; return 0;}', 'declaracion sin inicializar'),
    CasoC('V03', V, 'int main(){int a=1+2*3-4/2; return a;}', 'precedencia y asociatividad'),
    CasoC('V04', V, 'int main(){int a=((1+2)*(3-1)); return a;}', 'parentesis anidados'),
    CasoC('V05', V, 'int main(){int x=1; if (x<2) { if (x>0) { x=2; } else { x=3; } } else { x=4; } return x;}',
          'if/else anidados con bloques'),
    CasoC('V06', V, 'int main(){int i=0; while (i<10) { i=i+1; } return i;}', 'while con bloque'),
    CasoC('V07', V, 'int main(){int i=0; while (i<3) i=i+1; return i;}', 'while con sentencia simple'),
    CasoC('V08', V, 'int main(){ // linea\n int x=1; /* bloque\n multilinea */ return x;}',
          'comentarios de linea y de bloque'),
    CasoC('V09', V, 'int main(){int a=1; if (a<2) if (a>0) a=5; else a=6; return a;}',
          'else colgante: debe asociarse al if mas cercano'),
    CasoC('V10', V, 'int main(){int a=1; if (a==1) a=2; if (a!=1) a=3; if (a<=1) a=4; if (a>=1) a=5; return a;}',
          'los seis operadores relacionales'),
    CasoC('V11', V, 'int main(){int a=-5; return -a;}', 'signo negativo unario'),
    CasoC('V12', V, 'int main(){int _x1=1; int Abc_2=2; return _x1+Abc_2;}', 'identificadores con _ y digitos'),
    # ---------------- invalidos en C ----------------
    CasoC('I01', I, 'int main(){int x=3 return 0;}', 'falta ;', 'sintactico', 'línea 1, columna 20', "Se esperaba ';'"),
    CasoC('I02', I, 'int main(){int x=(1+2; return 0;}', 'falta )', 'sintactico', 'línea 1, columna 22', "Se esperaba ')'"),
    CasoC('I03', I, 'int main(){int x=3; return 0;', 'falta } final', 'sintactico', 'columna 30', "Se esperaba '}'"),
    CasoC('I04', I, 'int main(){int x=3@; return 0;}', "caracter ilegal '@'", 'lexico', 'línea 1, columna 19'),
    CasoC('I05', I, 'int main(){else return 1;}', 'else sin if', 'sintactico', None, 'Inicio de sentencia'),
    CasoC('I06', I, 'int main(){return 0}', 'return sin ;', 'sintactico', None, "Se esperaba ';'"),
    CasoC('I07', I, 'int main(){int 3x=1; return 0;}', 'identificador que empieza con digito', 'sintactico'),
    CasoC('I08', I, 'int main(){int x=; return 0;}', 'expresion vacia', 'sintactico', 'línea 1, columna 18'),
    CasoC('I09', I, 'int main(){int x=1+2); return 0;}', ') sobrante', 'sintactico', None, "Se esperaba ';'"),
    CasoC('I10', I, 'int main(){int x=0; while x<3 x=x+1; return x;}', 'while sin parentesis', 'sintactico', None, "Se esperaba '('"),
    CasoC('I11', I, 'int main(){int x=1 * / 2; return x;}', 'dos operadores seguidos', 'sintactico'),
    CasoC('I12', I, 'int main(){int while=1; return 0;}', 'palabra reservada como nombre', 'sintactico'),
    CasoC('I13', I, 'int main(){int x==1; return 0;}', '== en una declaracion', 'sintactico'),
    CasoC('I14', I, 'main(){return 0;}', 'sin tipo de retorno (invalido en C moderno)', 'sintactico', None, "Se esperaba 'int'"),
    # ---------------- fuera del subconjunto (valido en C real) ----------------
    CasoC('F01', F, 'int main(){if (2) return 1; return 0;}', 'if sin operador relacional: C lo acepta, la gramatica LL(1) no',
          'sintactico', None, 'operador relacional'),
    CasoC('F02', F, 'int main(){float x=1.5; return 0;}', 'tipo float y literal decimal', 'lexico'),
    CasoC('F03', F, 'int main(){int x="hola"; return 0;}', 'literal de cadena', 'lexico'),
    CasoC('F04', F, 'int main(int a){return 0;}', 'main con parametros', 'sintactico', None, "Se esperaba ')'"),
    CasoC('F05', F, 'int foo(){return 0;}', 'funcion distinta de main', 'sintactico', None, "Se esperaba 'main'"),
    CasoC('F06', F, 'int main(){return 0;} int y;', 'declaracion global tras main', 'sintactico', None, 'después de la función main'),
    CasoC('F07', F, '', 'archivo vacio', 'sintactico'),
)


def por_categoria(categoria: str) -> tuple[CasoC, ...]:
    return tuple(c for c in CASOS if c.categoria == categoria)
