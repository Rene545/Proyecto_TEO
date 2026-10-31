"""Catalogo de los puntos exactos donde la extension al espanol falla.

Cada entrada dice: que fenomeno linguistico la rompe, cual es la regla
concreta que falla, el diagnostico formal, y si el fenomeno sigue cabiendo o no
en una gramatica libre de contexto. Esa ultima columna es la importante: la
mayoria de las fallas NO son imposibilidades formales sino costos que crecen
hasta volver la gramatica inmanejable. Solo una (L6) es un salto real de nivel
en la jerarquia de Chomsky.

Separar esas dos cosas es el punto del ejercicio. Decir "la CFG no puede con la
concordancia" seria falso; lo correcto es "puede, pero multiplicando sus reglas
por el producto de las cardinalidades de los rasgos".
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Limitacion:
    codigo: str
    fenomeno: str
    ejemplo: str
    regla_que_falla: str
    diagnostico: str
    nivel_chomsky: str
    sigue_siendo_cfg: bool
    evidencia: str

    def texto(self) -> str:
        veredicto = ('sigue siendo tipo 2 (costo, no imposibilidad)'
                     if self.sigue_siendo_cfg else
                     'EXCEDE el tipo 2 (imposibilidad formal)')
        return '\n'.join([
            f'[{self.codigo}] {self.fenomeno}',
            f'  Ejemplo            : {self.ejemplo}',
            f'  Regla que falla    : {self.regla_que_falla}',
            f'  Diagnostico formal : {self.diagnostico}',
            f'  Jerarquia          : {self.nivel_chomsky}',
            f'  Veredicto          : {veredicto}',
            f'  Como reproducirlo  : {self.evidencia}',
        ])


CATALOGO: tuple[Limitacion, ...] = (
    Limitacion(
        codigo='L1',
        fenomeno='Sobregeneracion: sin rasgos no hay concordancia',
        ejemplo='*"la gato negros duerme" (aceptada por v1)',
        regla_que_falla='FN -> DET SUST ADJ  en gramatica.construir_v1',
        diagnostico=(
            'Una produccion solo concatena categorias; no puede exigir que dos '
            'hijos compartan un valor de rasgo. Sin rasgos en los no terminales, '
            'el lenguaje generado es el producto cartesiano de las categorias y '
            'contiene todas las discordancias.'),
        nivel_chomsky='Tipo 2. La gramatica es correcta como CFG; es el lenguaje el que esta mal elegido.',
        sigue_siendo_cfg=True,
        evidencia='cli.py --version v1 --oracion "la gato negros duerme"',
    ),
    Limitacion(
        codigo='L2',
        fenomeno='Explosion combinatoria al codificar la concordancia',
        ejemplo='v1 = 5 producciones -> v2 = 22 -> v3 = 49; v3 con persona = 189',
        regla_que_falla=(
            'Toda regla nominal de construir_v2/_v3: cada una se duplica una vez '
            'por combinacion de rasgos'),
        diagnostico=(
            'La concordancia local SI es expresable en una CFG, particionando cada '
            'no terminal en una copia por combinacion de rasgos. El costo es que '
            '|P| crece como el producto de las cardinalidades de los rasgos. Con '
            'genero(2) x numero(2) son 4 copias; agregando persona(3) son 12. Un '
            'espanol realista (tiempo, modo, aspecto, caso) multiplica cientos de '
            'veces. Nota: el tiempo verbal NO cuesta nada aqui, porque no participa '
            'en ninguna concordancia; el costo lo pagan solo los rasgos que deben '
            'coincidir entre dos constituyentes.'),
        nivel_chomsky=(
            'Tipo 2. Esto es lo que motiva las gramaticas de rasgos con unificacion '
            '(GPSG, HPSG, LFG) y las gramaticas de atributos: no amplian el poder '
            'generativo, solo factorizan la explosion.'),
        sigue_siendo_cfg=True,
        evidencia='cli.py --explosion',
    ),
    Limitacion(
        codigo='L3',
        fenomeno='Ambiguedad estructural: adjuncion de frase preposicional',
        ejemplo='"el niño ve el telescopio en la casa" -> 2 arboles',
        regla_que_falla=(
            'MODN -> FPREP MODN  compite con  MODV -> FPREP MODV: la misma frase '
            'preposicional puede colgar del nombre o del verbo'),
        diagnostico=(
            'La CFG genera los dos arboles y no tiene ningun mecanismo para '
            'preferir uno: desambiguar exige semantica y conocimiento del mundo, '
            'que estan fuera de la sintaxis. Y el numero de analisis crece con el '
            'numero de frases preposicionales segun los numeros de Catalan '
            '(1, 2, 5, 14, 42, ...), es decir exponencialmente. Consecuencia '
            'directa para el parser: una gramatica ambigua no es LL(k) para ningun '
            'k, asi que el analizador determinista de la fase 1 deja de servir y '
            'hubo que pasar a retroceso con enumeracion.'),
        nivel_chomsky=(
            'Tipo 2. La ambiguedad es una propiedad de la gramatica, no una salida '
            'de la clase. De hecho decidir si una CFG arbitraria es ambigua es un '
            'problema indecidible.'),
        sigue_siendo_cfg=True,
        evidencia='cli.py --ambiguedad',
    ),
    Limitacion(
        codigo='L4',
        fenomeno='Ambiguedad lexica que se propaga a la sintaxis',
        ejemplo='"baja" es Adj [f,sg] y V.intr [sg] a la vez',
        regla_que_falla=(
            'El emparejamiento de categorias lexicas en analizador._generar: una '
            'palabra puede satisfacer dos simbolos distintos'),
        diagnostico=(
            'El lexico es una relacion, no una funcion, asi que una misma cadena '
            'multiplica los analisis. En una CFG esto se maneja, pero multiplica el '
            'espacio de busqueda; en un lenguaje de programacion el analizador '
            'lexico lo evita por diseno reservando palabras clave.'),
        nivel_chomsky='Tipo 2. Es la diferencia practica clave entre un lexico disenado y uno natural.',
        sigue_siendo_cfg=True,
        evidencia='cli.py --version v3 --oracion "la niña baja" (y comparar con el lexico)',
    ),
    Limitacion(
        codigo='L5',
        fenomeno='Concordancia a distancia a traves de la subordinada',
        ejemplo='"el gato que ve los ratones duerme" (sujeto y verbo separados por la subordinada)',
        regla_que_falla=(
            'MODN -> SUBORD MODN  junto con  SUBORD -> PRON_REL FV: el rasgo de '
            'numero debe viajar por cada regla recursiva intermedia'),
        diagnostico=(
            'La dependencia es de distancia ilimitada, pero sigue siendo ANIDADA, y '
            'eso una CFG lo soporta: basta llevar el rasgo en el no terminal que '
            'domina todo el grupo nominal. El problema es de ingenieria, no de '
            'poder expresivo: cualquier regla recursiva que olvide propagar el '
            'rasgo rompe la concordancia en silencio, sin error visible.'),
        nivel_chomsky=(
            'Tipo 2. Las dependencias anidadas de profundidad arbitraria son '
            'precisamente lo que un automata de pila sabe reconocer.'),
        sigue_siendo_cfg=True,
        evidencia='cli.py --version v3 --oracion "el gato que ve los ratones duerme"',
    ),
    Limitacion(
        codigo='L6',
        fenomeno='EL MURO: coordinacion distributiva con "respectivamente"',
        ejemplo='"el niño y la niña son alto y baja respectivamente"',
        regla_que_falla=(
            'Ninguna regla finita sirve: muro_cfg.construir_v3_respectivamente '
            'necesita 4^n producciones para cubrir coordinaciones de longitud n'),
        diagnostico=(
            'El adjetivo i-esimo concuerda con el sujeto i-esimo: la dependencia es '
            'CRUZADA, no anidada. El conjunto de cadenas de rasgos gramaticales es '
            'isomorfo a { w c w }, que no es libre de contexto (lema de bombeo). '
            'Para cada n fijo existe una CFG, enumerando las 4^n secuencias, pero '
            'no existe ninguna CFG finita que cubra todo n.'),
        nivel_chomsky=(
            'Tipo 1 (dependiente del contexto). Lo reconoce un automata lineal '
            'acotado, no uno de pila. Es el mismo argumento de las dependencias '
            'cruzadas usado contra las CFG para el aleman suizo y el holandes.'),
        sigue_siendo_cfg=False,
        evidencia='cli.py --muro',
    ),
)


def por_codigo(codigo: str) -> Limitacion:
    for limitacion in CATALOGO:
        if limitacion.codigo == codigo.upper():
            return limitacion
    raise KeyError(f'No existe la limitacion {codigo}')


def tabla_resumen() -> list[dict[str, str]]:
    return [{
        'codigo': l.codigo,
        'fenomeno': l.fenomeno,
        'sigue_siendo_cfg': 'si' if l.sigue_siendo_cfg else 'NO',
        'nivel': l.nivel_chomsky.split('.')[0],
    } for l in CATALOGO]
