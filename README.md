# Proyecto TLP02-2026 — Gramáticas formales y lenguaje natural

Este repositorio es la implementación del proyecto de Teoría de Lenguajes de
Programación. La idea del proyecto es empujar una gramática libre de contexto
(CFG) hasta donde aguante: primero se uso para lo que sirve bien, que es un
subconjunto de un lenguaje de programación, y después intenta estirarla al
español para ver exactamente dónde se rompe y por qué.

El resultado corto, por si alguien solo quiere la conclusión: la CFG **sí**
puede con la concordancia de género y número, pero pagando un precio que crece
como el producto de las cardinalidades de los rasgos. Donde de verdad se queda
corta es en las dependencias cruzadas, y eso sí es una imposibilidad formal,
no una cuestión de esfuerzo.

## Requisitos

Python 3.10 o superior. **Nada más**: no hay dependencias externas, no hace
falta instalar Graphviz ni crear un entorno virtual. Los árboles sintácticos
se exportan a SVG con un renderizador que se escribió a mano en `core/arbol.py`,
precisamente para que la demo en vivo no dependa de que la máquina del aula
tenga algo instalado.

Todos los comandos se ejecutan **desde la raíz del repositorio**, porque los
módulos se importan por paquete (`python -m paquete.modulo`).

La única excepción son las comparaciones con NLP de las partes 3 y 4, que usan
NLTK y spaCy (`pip install nltk spacy` y `python -m spacy download
es_core_news_sm`). Sin ellas, todo lo demás funciona y sus resultados ya
generados están en `comparacion_nlp/resultados/` y `analisis_formal/resultados/`.

## Estructura

```
core/arbol.py                   Árbol genérico + exportación a texto, DOT y SVG
fase1_parser_formal/            Parser del subconjunto de C
  lexer.py                      Tokenizador por expresiones regulares
  parser.py                     Analizador descendente recursivo
  cli.py                        Interfaz de línea de comandos
fase1_extension_espanol/        Extensión de la CFG al español
  lexico.py                     Vocabulario con rasgos morfológicos
  gramatica.py                  Las tres versiones de la gramática (v1, v2, v3)
  analizador.py                 Analizador con retroceso y enumeración
  muro_cfg.py                   El límite que ya no es libre de contexto
  limitaciones.py               Catálogo formal de los puntos de falla
  cli.py                        Demo ejecutable
comparacion_nlp/                Pruebas y comparación con NLTK y spaCy (ver su README)
analisis_formal/                Análisis formal y verificación independiente (ver su README)
  marco_teorico.md              Jerarquía de Chomsky y lenguaje formal vs. natural
  analisis_resultados.md        L1–L6 en la jerarquía, demostración de L6, métricas
  verificar_teoria.py           Recalcula los números teóricos por otro camino
  inspeccionar_spacy.py         Clasifica los falsos positivos de spaCy
informe/informe_tecnico.md      Informe técnico de la Fase 1
presentacion/                   Guion de la presentación, demo y banco de preguntas
tests/                          Pruebas (89 en total)
validacion/                     Programas en C y oraciones en español de prueba
salidas_ejemplo/                Árboles SVG ya generados
```

## Parte 1 — Parser del subconjunto de C

Se implementó un analizador descendente recursivo. El subconjunto que acepta es
una función `main` con declaraciones de enteros, asignaciones, `if`/`else`,
`while`, bloques anidados, `return` y expresiones aritméticas con precedencia.

```bash
python -m fase1_parser_formal.cli --archivo validacion/programa_valido.c
python -m fase1_parser_formal.cli --archivo validacion/programa_invalido.c
python -m fase1_parser_formal.cli --texto "int main(){int x=(1+2)*3;return x;}" --svg arbol.svg
```

El primero imprime el árbol sintáctico; el segundo falla a propósito y reporta
`Se esperaba ';'; apareció 'return' en línea 3, columna 5`.

La precedencia se resolvió con la estratificación clásica
expresión → término → factor, así que `1+2*3` agrupa la multiplicación
primero sin necesidad de reglas de prioridad externas.


- **La condición de un `if` exige un operador relacional.** `if (2)` se
  rechaza, aunque C lo aceptaría. se hizo así para que la gramática del
  subconjunto quede LL(1) y sin ambigüedad en ese punto; es una restricción
  mía, no un error.
- **El `else` colgante se asocia al `if` más cercano.** Esa ambigüedad existe
  en la gramática real de C, y el analizador la resuelve por el orden en que
  intenta las alternativas. se dejó documentado porque es el puente natural
  hacia la ambigüedad del lenguaje natural de la parte 2.

## Parte 2 — Extensión al español

Aquí está el núcleo del trabajo. En vez de escribir una sola gramática del
español y reportar que falla, se escribieron **tres versiones incrementales**, porque
lo que se quería medir era *cuánto* cuesta cada fenómeno, no solo si se puede o no.

| Versión | Qué agrega | Producciones |
| :--- | :--- | ---: |
| v1 | Categorías sin rasgos, sin concordancia | 5 |
| v2 | Concordancia det–sust–adj y sujeto–verbo | 22 |
| v3 | Adjetivos, adverbios, frases preposicionales y subordinada de relativo | 49 |

### Cómo imponer concordancia en una CFG

Una producción solo concatena símbolos; no puede exigir que dos hijos
compartan el valor de un rasgo. La única salida dentro de las CFG es meter el
rasgo **dentro del nombre del no terminal** y partir cada regla en una copia
por combinación. Es decir, pasar de esto:

```
FN -> DET SUST ADJ
```

a esto, cuatro veces (una por cada combinación de género × número):

```
FN[genero=m,numero=sg] -> DET[genero=m,numero=sg] SUST[genero=m,numero=sg] ADJ[genero=m,numero=sg]
FN[genero=f,numero=sg] -> DET[genero=f,numero=sg] SUST[genero=f,numero=sg] ADJ[genero=f,numero=sg]
...
```

Funciona. Y es la razón por la que se generaron las producciones por código en
`gramatica.py` en lugar de escribirlas a mano: con 49 reglas ya es tedioso, y
quería poder **contarlas** variando el conjunto de rasgos.

```bash
python -m fase1_extension_espanol.cli --gramatica v3    # la gramática en BNF
python -m fase1_extension_espanol.cli --explosion       # cuánto crece |P|
```

La tabla de `--explosion` es el dato que interesaba: añadiendo solo el rasgo
`persona` (3 valores), v3 pasa de 49 a **189** producciones, casi 38 veces el
tamaño de v1. Un español realista, con tiempo, modo y aspecto, multiplica eso
por cientos. Vale la pena notar que el **tiempo verbal no cuesta nada** en mi
gramática, porque no participa en ninguna concordancia: el precio lo pagan
únicamente los rasgos que deben coincidir entre dos constituyentes. Eso es
exactamente lo que motivó históricamente las gramáticas de rasgos con
unificación (HPSG, LFG) y las gramáticas de atributos: no amplían el poder
generativo, solo factorizan esta explosión.

### Por qué tuve que cambiar de analizador

El parser de C es descendente recursivo determinista porque ese subconjunto es
LL(1). Para el español no me sirvió, y no por un defecto corregible: **v3 es
ambigua, y una gramática ambigua no es LL(k) para ningún k**, porque hay
cadenas con más de un árbol de derivación y un analizador determinista solo
puede devolver uno. Así que en `analizador.py` se conservó el análisis descendente
pero se agregó retroceso completo y enumeración de todas las derivaciones.

Tiene dos modos. `contar()` cuenta las derivaciones por programación dinámica
sin construir árboles, así que es barato incluso cuando el número de análisis
es enorme; `analizar()` da el conteo exacto más los primeros N árboles
concretos. Dejé además una guarda que detecta recursión izquierda y falla con
un mensaje claro en lugar de colgarse, porque me pasó mientras escribía las
reglas de modificadores.

### Uso

```bash
# analizar una oración y ver sus árboles
python -m fase1_extension_espanol.cli --oracion "el gato que duerme ve el ratón"
python -m fase1_extension_espanol.cli --oracion "las gatas negras duermen" --svg arbol.svg

# comparar versiones sobre la misma oración
python -m fase1_extension_espanol.cli --oracion "la gato negros duerme" --version v1   # la acepta
python -m fase1_extension_espanol.cli --oracion "la gato negros duerme" --version v2   # la rechaza

# correr todo el conjunto de prueba
python -m fase1_extension_espanol.cli --lote validacion/oraciones_espanol.txt

# los hallazgos, uno por bandera
python -m fase1_extension_espanol.cli --ambiguedad
python -m fase1_extension_espanol.cli --limitaciones
python -m fase1_extension_espanol.cli --muro
```

El archivo `validacion/oraciones_espanol.txt` tiene 51 casos en tres niveles de
complejidad, marcados con `+` si la gramática debe aceptarlos y `-` si debe
rechazarlos. Los 51 coinciden con lo esperado. Los últimos tres son oraciones
perfectamente gramaticales en español que v3 rechaza: eso **no es un bug**, es
el resultado que se buscaba documentar.

## Los hallazgos

Se catalogaron seis puntos de falla en `limitaciones.py`, cada uno con la regla
concreta que falla, el diagnóstico formal y el nivel de la jerarquía de Chomsky
que le corresponde. Lo más importante del catálogo es la columna que dice si el
fenómeno **sigue cabiendo o no** en una CFG, porque cinco de los seis sí caben:
son costos, no imposibilidades. Decir "una CFG no puede con la concordancia"
sería simplemente falso.

| | Fenómeno | ¿Sigue siendo CFG? |
| :--- | :--- | :--- |
| L1 | Sobregeneración: sin rasgos no hay concordancia | sí |
| L2 | Explosión combinatoria al codificar la concordancia | sí |
| L3 | Ambigüedad estructural (adjunción de frase preposicional) | sí |
| L4 | Ambigüedad léxica que se propaga a la sintaxis | sí |
| L5 | Concordancia a distancia a través de la subordinada | sí |
| L6 | Coordinación distributiva con "respectivamente" | **no** |

### L3 — la ambigüedad crece exponencialmente

Al medir cuántos análisis produce v3 según el número de frases preposicionales
me salió esta serie:

| Frases preposicionales | 0 | 1 | 2 | 3 |
| :--- | ---: | ---: | ---: | ---: |
| Análisis distintos | 1 | 2 | 5 | 14 |

Son los **números de Catalan**. No se buscaron: es la consecuencia de que cada
frase preposicional nueva puede colgar del nombre o del verbo, y el número de
árboles binarios posibles sobre *n* puntos de adjunción es justamente
C(n); contando frases preposicionales, *k* frases dan C(k + 1) análisis. La
serie sigue 42, 132, 429 (ver `analisis_formal/`). O sea que la ambigüedad crece exponencialmente y la CFG no tiene ningún
mecanismo para preferir un árbol sobre otro: desambiguar "el niño ve el
telescopio en la casa" exige semántica y conocimiento del mundo, que están
fuera de la sintaxis. Como dato adicional, decidir si una CFG arbitraria es
ambigua es un problema **indecidible**.

### L5 — lo que parecía un límite y no lo era

Se esperaba que la concordancia a distancia rompiera la gramática:
"el gato que ve los ratones duerme" tiene el sujeto y su verbo separados por
una subordinada completa. Pero funciona, y al razonarlo tiene sentido: la
dependencia es de distancia ilimitada pero **anidada**, y eso es exactamente lo
que un autómata de pila sabe reconocer. Basta con llevar el rasgo en el no
terminal que domina todo el grupo nominal. se dejó en el catálogo porque es un
resultado negativo útil: el problema real es de ingeniería, ya que cualquier
regla recursiva que olvide propagar el rasgo rompe la concordancia en silencio.

### L6 — el muro de verdad

Aquí sí se sale de las CFG. La construcción es la coordinación distributiva:

> "el niño y la niña son alto y baja respectivamente"

Con *n* sujetos y *n* adjetivos, el adjetivo *i* debe concordar con el sujeto
*i*. La dependencia es **cruzada**, no anidada. Abstrayendo cada grupo nominal
a su par de rasgos, el conjunto de cadenas gramaticales es isomorfo a
*{ w c w }*, que es el ejemplo de libro de lenguaje **no** libre de contexto:
se demuestra con el lema de bombeo: el segmento bombeado mide a lo sumo *p*,
así que o borra la *c*, o altera una sola copia, o (si cruza la *c*) solo toca
el final de la primera copia y el inicio de la segunda y las desbalancea. La
demostración completa, con intersección con un regular y homomorfismo, está en
`analisis_formal/analisis_resultados.md`.

se verificó empíricamente. Parcheé v3 enumerando las secuencias de rasgos para
coordinaciones de longitud fija, y el comportamiento es el predicho: con el
parche para n ≤ 2 la versión correcta se acepta y la de rasgos cruzados
("son alta y bajo") se rechaza, pero una coordinación de tres elementos se
rechaza hasta que agrego reglas nuevas. El costo de cada longitud adicional:

| n máximo | 2 | 3 | 4 | 5 | 6 |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Producciones necesarias | 16 | 80 | 336 | 1 360 | 5 456 |

Para cada *n* fijo existe una CFG. Lo que no existe es una CFG **finita** que
cubra todo *n*. El lenguaje sí es dependiente del contexto (tipo 1): lo
reconoce un autómata lineal acotado comparando las dos mitades. El salto es
exactamente tipo 2 → tipo 1, y es el mismo argumento de las dependencias
cruzadas que se usó contra las CFG como modelo del alemán suizo y del holandés.

Dejo anotado el contraargumento honesto, porque me parece parte del hallazgo:
el argumento formal exige *n* no acotado, y en el uso real nadie coordina
veinte sujetos, así que para el español efectivamente producible una CFG
gigantesca alcanzaría. La distinción es la clásica entre competencia y
actuación. La limitación es de competencia, y es la que importa al clasificar
el lenguaje dentro de la jerarquía.

## Parte 3 — Pruebas y comparación con NLP

La carpeta `comparacion_nlp/` agrega un corpus de 33 programas de C (válidos,
inválidos y fuera del subconjunto), un gold de 61 oraciones en español con dos
etiquetas (`esperado_v3` y `gramatical_real`) y la comparación del parser propio
con NLTK (verificación cruzada, misma gramática v3) y con spaCy. El detalle y
los comandos están en `comparacion_nlp/README.md`.

```bash
python -m comparacion_nlp.ejecutar_pruebas_c
python -m comparacion_nlp.comparar               # o --sin-spacy --sin-nltk
```

## Parte 4 — Análisis formal

La carpeta `analisis_formal/` ubica cada punto de falla en la jerarquía de
Chomsky y verifica los números del proyecto por un camino independiente.

```bash
python -m analisis_formal.verificar_teoria       # sin dependencias
python -m analisis_formal.inspeccionar_spacy     # necesita spaCy
```

Lo principal: la serie de L3 se reproduce con una gramática abstracta distinta
(y continúa 42, 132, 429); la tabla de L6 sale de la fórmula cerrada
(4ⁿ⁺¹ − 16)/3; la demostración de L6 se completa con intersección con un
regular, homomorfismo a { w c w } y lema de bombeo por casos; y de los 7 falsos
positivos de spaCy, 2 son rasgos que spaCy "corrige" en silencio (etiqueta
"negra" como masculino en "el gato negra duerme"). El informe técnico está en
`informe/informe_tecnico.md` y el guion de la presentación en
`presentacion/guion_presentacion.md`.

## Pruebas

```bash
python -m unittest tests.test_fase1 tests.test_extension_espanol tests.test_corpus_c tests.test_comparacion_nlp tests.test_analisis_formal -v
```

89 pruebas: 14 del parser de C, 40 de la extensión al español, 23 del corpus de
C y la comparación con NLP, y 12 del análisis formal. Ninguna necesita NLTK ni
spaCy. Varias de las 40 afirman explícitamente que una oración **gramatical** en español es
rechazada, con el código de la limitación que lo explica en el docstring; otras
fijan los números que reporto arriba (las 5/22/49 producciones, la serie
1-2-5-14) para que no se me muevan sin darme cuenta.

Las pruebas se corren con `python -m unittest tests.test_...` y no con
descubrimiento automático (`discover`), porque no puse `__init__.py` en
`tests/` y el descubrimiento necesita que el directorio sea importable.

## Alcance que dejé fuera a propósito

Para que el experimento sea legible acoté el subconjunto del español. Estas son
restricciones conscientes, no cosas que se me olvidaron:

- **Solo tercera persona.** El léxico no tiene 1ª ni 2ª persona. El rasgo
  `persona` está implementado y es parametrizable, pero lo uso únicamente para
  medir el crecimiento de la gramática, no para analizar.
- **Sin contracciones.** Se escribe "de el jardín" y no "del", para no mezclar
  fenómenos morfofonológicos con los sintácticos que se estan midiendo.
- **Sin la preposición "a" de objeto directo.** "ve el ratón", no "ve al
  ratón", por la misma razón.
- **El orden de los modificadores es más laxo que el del español real.** La
  regla `MODN -> ADJ MODN` permite "el gato en la casa negro", que suena mal.
  Restringirlo exigía más particiones de no terminales y habría inflado la
  gramática sin aportar al argumento.
- **Sin coordinación general.** "el gato duerme y el perro ladra" se rechaza.
  La única coordinación que se implementó es la distributiva de L6, porque esa es
  la que demuestra el límite formal.

El léxico tolera entradas sin tildes (escribir "nino" o "jardin" funciona),
pero las formas canónicas están acentuadas correctamente, porque el mismo
conjunto de oraciones se va a pasar por spaCy más adelante y no se quiere que la
comparación se contamine con problemas de ortografía.
