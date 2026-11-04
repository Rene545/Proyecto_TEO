# Gramáticas formales y lenguaje natural: experimentando los límites de la jerarquía de Chomsky

**Proyecto TLP02-2026 — Fase 1**
Teoría de Lenguajes de Programación — Universidad Centroamericana José Simeón Cañas

**Integrantes:** _(completar)_
**Repositorio:** https://github.com/Rene545/Proyecto_TEO
**Fecha:** noviembre de 2026

---

## Resumen

Se implementó un analizador descendente recursivo para un subconjunto de C y se
intentó extender su gramática libre de contexto (CFG) al español en tres
versiones incrementales (v1, v2 y v3). El objetivo no fue solo observar que la
gramática falla, sino medir cuánto cuesta cada fenómeno y en qué punto exacto se
sale del tipo 2 de la jerarquía de Chomsky. Los resultados muestran que la
concordancia de género y número sí cabe en una CFG, a un costo que crece como el
producto de las cardinalidades de los rasgos; que la ambigüedad de adjunción
preposicional crece según los números de Catalan; y que la coordinación
distributiva con "respectivamente" introduce dependencias cruzadas que ninguna
CFG finita puede capturar. De las 13 oraciones gramaticales que v3 rechaza, solo
una corresponde a esa imposibilidad formal; las demás son decisiones de alcance.
Finalmente, se comparó el parser con NLTK (que confirma el número de derivaciones
en 61 de 61 oraciones) y con spaCy, cuya naturaleza estadística le da cobertura
casi total pero ninguna noción de agramaticalidad.

## 1. Marco teórico

### 1.1 La jerarquía de Chomsky

| Tipo | Gramática | Producciones | Reconocedor | Ejemplo |
| :--- | :--- | :--- | :--- | :--- |
| 0 | Irrestricta | α → β | Máquina de Turing | Recursivamente enumerables |
| 1 | Dependiente del contexto | αAβ → αγβ | Autómata linealmente acotado | { aⁿbⁿcⁿ }, { w c w } |
| 2 | Libre de contexto | A → γ | Autómata de pila | { aⁿbⁿ }, { w c wᴿ } |
| 3 | Regular | A → aB, A → a | Autómata finito | a*b*, identificadores |

Las inclusiones son estrictas y cada una se demuestra con un lenguaje testigo y
el lema de bombeo correspondiente (Hopcroft et al., 2007; Sipser, 2013). Una
producción A → γ reescribe A igual sin importar su entorno; por eso el
reconocedor equivalente, el autómata de pila, solo compara contra el último
símbolo guardado. Reconoce dependencias **anidadas** (a₁ a₂ b₂ b₁) pero no
**cruzadas** (a₁ a₂ b₁ b₂).

Tres propiedades de las CFG sostienen el análisis: (1) el **lema de bombeo**
(Bar-Hillel et al., 1961); (2) la **clausura** bajo intersección con lenguajes
regulares y bajo homomorfismo, que permite reducir un fragmento del español a un
lenguaje de libro; y (3) que toda gramática LL(k) es no ambigua, mientras que
decidir si una CFG arbitraria es ambigua es **indecidible** (Cantor, 1962).

Entre el tipo 2 y el tipo 1 está la clase de los lenguajes **ligeramente
dependientes del contexto** (Joshi, 1985), generados por TAG y CCG: agregan
dependencias cruzadas acotadas y conservan análisis polinomial. Es la clase en
la que hoy se ubica al lenguaje natural.

### 1.2 Lenguaje formal frente a lenguaje natural

| Dimensión | Subconjunto de C | Español |
| :--- | :--- | :--- |
| Origen | Diseñado; la gramática *es* el lenguaje | Evoluciona; la gramática lo describe aproximadamente |
| Estructura | Explícita (llaves, `;`, palabras reservadas) | Implícita; orden flexible, sujeto tácito |
| Ambigüedad | Eliminada o resuelta por convención (`else` colgante) | Estructural y léxica; requiere semántica |
| Recursividad | Bloques y expresiones anidados | Subordinadas, frases preposicionales, relativas |
| Dependencias de contexto | Delegadas al análisis semántico (tabla de símbolos) | Concordancia, correferencia, dependencias cruzadas |
| Concordancia | No existe en la sintaxis | Obligatoria: género, número, persona |
| Vocabulario | Cerrado | Abierto |

Incluso C tiene restricciones que no son libres de contexto, como declarar una
variable antes de usarla, que es esencialmente el lenguaje { w c w }. Los
compiladores no las resuelven en la gramática sino en el análisis semántico
(Aho et al., 2006). La concordancia del español se parece más a esa verificación
de tipos que a la sintaxis pura.

### 1.3 ¿Es el lenguaje natural libre de contexto?

Pullum y Gazdar (1982) refutaron los primeros argumentos en contra, incluido el
de *respectively* del inglés, por basarse en dependencias semánticas. Bresnan et
al. (1982) mostraron dependencias cruzadas en holandés, pero solo afectan la
capacidad generativa fuerte. Shieber (1985) dio la prueba aceptada con el alemán
suizo: la marca de caso hace visible la dependencia cruzada en la cadena y,
mediante intersección con un regular y homomorfismo, el lenguaje se reduce a uno
que no es libre de contexto. El hallazgo L6 de este proyecto aplica esa misma
técnica al español.

## 2. Parser formal del subconjunto de C

El subconjunto acepta una función `main` con declaraciones de enteros,
asignaciones, `if`/`else`, `while`, bloques anidados, `return` y expresiones
aritméticas. El analizador léxico (`lexer.py`) es una sola expresión regular
con grupos nombrados, es decir, un reconocedor de tipo 3: distingue números,
identificadores, operadores, símbolos y comentarios, y separa las palabras
reservadas de los identificadores. El analizador sintáctico (`parser.py`) es
descendente recursivo, con un método por no terminal. Su gramática, en EBNF:

```
programa    -> 'int' 'main' '(' ')' bloque EOF
bloque      -> '{' sentencia* '}'
sentencia   -> declaracion | asignacion | retorno | si | mientras | bloque
declaracion -> 'int' ID ( '=' expresion )? ';'
asignacion  -> ID '=' expresion ';'
retorno     -> 'return' expresion ';'
si          -> 'if' '(' condicion ')' sentencia ( 'else' sentencia )?
mientras    -> 'while' '(' condicion ')' sentencia
condicion   -> expresion OPREL expresion        OPREL: == != < <= > >=
expresion   -> termino ( ( '+' | '-' ) termino )*
termino     -> factor ( ( '*' | '/' ) factor )*
factor      -> NUM | ID | '(' expresion ')' | '-' factor
```

La gramática es LL(1): `sentencia` elige su alternativa con un solo token
(`int`, identificador, `return`, `if`, `while` o `{`), y esos conjuntos
PRIMERO son disjuntos. La precedencia se resuelve con la estratificación
expresión → término → factor, de modo que `1+2*3` agrupa la multiplicación
primero; las repeticiones `( … )*` se implementan como ciclos que construyen el
árbol hacia la izquierda, lo que da asociatividad izquierda a `-` y `/`.

Dos decisiones de diseño merecen mención. La condición del `if` exige un
operador relacional (`if (2)` se rechaza aunque C lo acepte), lo que simplifica
la gramática. Y el `else` opcional produce el único conflicto LL(1) de la
gramática: `else` está a la vez en PRIMERO de `( 'else' sentencia )?` y en
SIGUIENTE de `sentencia`. El analizador lo resuelve consumiendo el `else` en
cuanto lo ve, lo que lo asocia al `if` más cercano. Es la ambigüedad clásica
del `else` colgante de C, resuelta por convención, y sirve de puente hacia la
ambigüedad del español, donde no existe una convención así.

Los errores se reportan con línea y columna (por ejemplo,
`Se esperaba ';'; apareció 'return' en línea 3, columna 5`), y los árboles se
exportan a texto, DOT y SVG con un renderizador propio sin dependencias externas.

**Pruebas.** Se definió un corpus de 33 programas: 12 válidos, 14 inválidos
también en C real y 7 válidos en C pero fuera del subconjunto (`if (2)`,
`float`, `main` con parámetros). La tercera categoría separa las decisiones de
alcance de los errores del parser. Los 33 se comportan como se declaró, y se
verifica estructuralmente la precedencia y la asociación del `else`. El corpus
está en `validacion/c_corpus/` y se ejecuta con
`python -m comparacion_nlp.ejecutar_pruebas_c`.

## 3. Extensión de la gramática al español

Se escribieron tres versiones incrementales para medir el costo de cada
fenómeno:

| Versión | Agrega | Producciones |
| :--- | :--- | ---: |
| v1 | Categorías sin rasgos | 5 |
| v2 | Concordancia det–sust–adj y sujeto–verbo | 22 |
| v3 | Adjetivos, adverbios, frases preposicionales y relativa | 49 |

Una producción de CFG no puede exigir que dos hijos compartan un rasgo. La única
forma de imponer la concordancia es incluir el rasgo en el nombre del no
terminal y crear una copia de la regla por combinación:

```
FN -> DET SUST ADJ
   ⇒  FN[m,sg] -> DET[m,sg] SUST[m,sg] ADJ[m,sg]
      FN[f,sg] -> DET[f,sg] SUST[f,sg] ADJ[f,sg]
      FN[m,pl] -> ...        FN[f,pl] -> ...
```

Por eso las producciones se generan por código y se pueden contar al variar los
rasgos: agregando solo `persona` (3 valores), v3 pasa de 49 a 189 producciones.
El tiempo verbal no aumenta el tamaño porque no participa en ninguna
concordancia.

El parser de C es determinista porque su gramática es LL(1). v3, en cambio, es
**ambigua**, y una gramática ambigua no es LL(k) para ningún k. Por eso el
analizador del español conserva el análisis descendente pero agrega retroceso y
enumeración de derivaciones: `contar()` cuenta por programación dinámica sin
construir árboles y `analizar()` devuelve además los primeros N árboles. Una
guarda detecta recursión izquierda y falla con un mensaje claro.

Las 51 oraciones de validación del equipo (tres niveles, positivas y negativas)
se comportan como se esperaba, incluidas tres oraciones gramaticales que v3
rechaza a propósito.

**Pruebas del repositorio.** La suite completa tiene 89 pruebas y pasan todas:
14 del parser de C, 40 de la extensión al español, 23 del corpus de C y de la
comparación con NLP, y 12 del análisis formal, que cruzan los números de este
informe con dos implementaciones independientes.

```bash
python -m unittest tests.test_fase1 tests.test_extension_espanol tests.test_corpus_c tests.test_comparacion_nlp tests.test_analisis_formal
```

## 4. Análisis formal de los puntos de falla

| | Fenómeno | Regla donde falla | Clase de dependencia | ¿Sigue siendo CFG? | Nivel |
| :--- | :--- | :--- | :--- | :--- | :--- |
| L1 | Sobregeneración sin rasgos | `FN -> DET SUST ADJ` (v1) | Concordancia local | Sí | Tipo 2 |
| L2 | Explosión al codificar rasgos | Toda regla nominal de v2 y v3 | Concordancia local finita | Sí | Tipo 2 |
| L3 | Ambigüedad de adjunción preposicional | `MODN -> FPREP MODN` frente a `MODV -> FPREP MODV` | Estructural | Sí (gramática ambigua) | Tipo 2 |
| L4 | Ambigüedad léxica | "baja" es Adj [f,sg] y V.intr [sg] | Léxica | Sí | Tipo 2 |
| L5 | Concordancia a través de la relativa | `MODN -> SUBORD MODN`, `SUBORD -> PRON_REL FV` | Ilimitada pero anidada | Sí | Tipo 2 |
| L6 | Coordinación con "respectivamente" | Ninguna regla finita (`muro_cfg`) | **Cruzada** | **No** | **Tipo 1** |

**L1 y L2 — costo, no imposibilidad.** Si F es el conjunto de rasgos que una
regla obliga a coincidir, la regla se parte en Π_{r∈F} |Vᵣ| copias: 4 para
género × número, 12 si se agrega persona. Medido sobre las gramáticas del
proyecto, pasar de 4 a 12 combinaciones lleva v2 de 22 a 114 producciones y v3
de 49 a 189. Como los rasgos son finitos, el resultado sigue siendo una CFG
finita. Las gramáticas de atributos (Knuth, 1968) y de unificación (LFG, HPSG)
surgieron para factorizar esta explosión, sin aumentar el poder generativo.

**L3 — ambigüedad exponencial.** Con k frases preposicionales tras el objeto, v3
produce 1, 2, 5 y 14 árboles, y extendiendo la prueba hasta k = 6 el mismo
analizador sigue con 42, 132 y 429. La serie se reprodujo además con una
gramática abstracta de tres reglas, recursiva por la izquierda
(`SV → V SN | SV SP`, `SN → N | SN SP`, `SP → P SN`), mientras que v3 es
recursiva por la derecha: dos gramáticas distintas dan exactamente los números
de Catalan C(k + 1), que crecen como 4ⁿ / (n^{3/2}√π) (Church y Patil, 1982). La
CFG genera todos los árboles pero no tiene criterio para preferir uno; "el niño
ve el telescopio en la casa" se desambigua con semántica o conocimiento del
mundo. Contar los árboles, en cambio, es polinomial, porque comparten
subárboles; por eso `contar()` es barato aunque el número sea exponencial.

**L5 — distancia no es cruce.** En "el gato que ve los ratones duerme" el sujeto y
su verbo están separados por una subordinada completa, pero la dependencia es
anidada, con la forma de { w c wᴿ }. El autómata de pila apila el número del
sujeto, procesa la relativa y lo encuentra en el tope al llegar al verbo. Basta
con propagar el rasgo en el no terminal que domina el grupo nominal.

**L6 — la salida del tipo 2.** En "el niño y la niña son alto y baja
respectivamente" el adjetivo i concuerda con el sujeto i, de modo que las
dependencias se cruzan. Suponiendo que el fragmento E fuera libre de contexto:

1. Se interseca con el regular R = (DET SUST y)⁺ DET SUST son ADJ (y ADJ)⁺
   respectivamente. E ∩ R seguiría siendo libre de contexto.
2. Se aplica un homomorfismo h que lleva cada sustantivo y adjetivo al símbolo de
   su par (género, número), `son` a c, y borra lo demás. Se obtiene
   h(E ∩ R) = { w c w : |w| ≥ 2 }.
3. Con z = aᵖbᵖcaᵖbᵖ, toda descomposición uvwxy con |vwx| ≤ p o borra la c, o
   altera una sola de las mitades, o (si cruza la c) quita b's de la primera y
   a's de la segunda en distinta posición. En todos los casos uv⁰wx⁰y ∉ L.

Esto contradice el lema de bombeo; por lo tanto E no es libre de contexto. El
lenguaje copia sí es tipo 1 (lo reconoce un autómata linealmente acotado
comparando las mitades) y además ligeramente dependiente del contexto.

Para cada longitud máxima n sí existe una CFG que enumera las 4ᵏ secuencias de
rasgos, con un costo de Σ_{k=2}^{n} 4ᵏ = (4ⁿ⁺¹ − 16)/3 producciones:

| n máximo | 2 | 3 | 4 | 5 | 6 |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Producciones | 16 | 80 | 336 | 1 360 | 5 456 |

La fórmula coincide con lo medido al parchear v3 (`muro_cfg`) para n = 2…8, y
aplicando h al léxico real las oraciones correctas de n = 2 y n = 3 caen en
{ w c w } mientras que la cruzada no. Lo que no existe es una CFG finita para
todo n.

Dos objeciones se reconocen explícitamente. Primero, el argumento exige n no
acotado, cosa que no ocurre en el uso real; la jerarquía clasifica la
competencia, no la actuación. Segundo, Pullum y Gazdar descartaron el argumento
de *respectively* en inglés porque allí la dependencia es semántica; en español
la discordancia es morfológica ("son alta y bajo"), lo que fortalece el
argumento, aunque depende del juicio de que esa discordancia es agramatical y no
solo extraña.

## 5. Comparación con NLTK y spaCy

Se usaron las 51 oraciones del equipo y 10 oraciones de español natural fuera de
alcance (61 en total: 45 gramaticales y 16 agramaticales).

| Sistema | TP | FP | FN | TN | Precisión | Cobertura | Rechazo correcto | Exactitud |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v1 | 17 | 11 | 28 | 5 | 0.607 | 0.378 | 0.312 | 0.361 |
| v2 | 17 | 0 | 28 | 16 | 1.000 | 0.378 | 1.000 | 0.541 |
| v3 | 32 | 0 | 13 | 16 | 1.000 | 0.711 | 1.000 | 0.787 |
| spaCy + regla | 44 | 7 | 1 | 9 | 0.863 | 0.978 | 0.562 | 0.869 |

La comparación completa se volvió a ejecutar en una máquina limpia (NLTK y
spaCy 3.8 con `es_core_news_sm` 3.8.0) y todas las tablas salieron idénticas;
solo cambian los tiempos.

**NLTK como verificación cruzada.** La gramática v3 exportada a
`EarleyChartParser` coincide con el parser propio en el número de derivaciones en
61/61 oraciones, incluida la serie 1-2-5-14 de L3.

**spaCy.** Es un analizador de dependencias estadístico: produjo árbol para
61/61 oraciones y no rechaza ninguna. Para medir su detección de discordancia se
aplicó una regla de concordancia sobre sus rasgos morfológicos. Se revisaron uno
por uno sus 7 falsos positivos, comparando los rasgos que asigna spaCy con los
del léxico (`analisis_formal/inspeccionar_spacy.py`):

| Mecanismo | Oraciones | Qué pasa |
| :--- | :--- | :--- |
| Rasgo vacío | "los gato duermen", "el gato duermen" | spaCy no asigna género ni número a "gato"; la regla no tiene con qué comparar |
| Rasgo asimilado | "el gato ve los ratón", "el gato negra duerme" | spaCy marca "ratón" como plural y "negra" como masculino: asigna el rasgo que concuerda con la palabra vecina |
| Límite de la regla | las 3 relativas con verbo discordante | "que" no tiene número y la regla no sigue la relación `acl` hasta el antecedente |

El segundo mecanismo es el más revelador: el etiquetador morfológico predice
los rasgos a partir del contexto y, ante una discordancia, la **corrige en
silencio** antes de que cualquier regla pueda verla. Solo los tres fallos de la
relativa se arreglarían mejorando la regla. Su único falso negativo ("Yo quiero
que tú vengas") se debe a que el modelo etiquetó `vengas` como adjetivo plural.

**Interpretación.**

- **v1 → v2** elimina los 11 falsos positivos (L1) y **v2 → v3** recupera 15
  oraciones sin introducir ninguno (costo de L2).
- De los 13 falsos negativos de v3, **1** es el límite formal (L6), 2 son
  coordinación general no implementada, 7 son vocabulario y 3 son construcciones
  no cubiertas. Doce de trece se corrigen sin salir de las CFG.
- Con 61 oraciones, los intervalos de Wilson al 95 % de la exactitud se solapan
  (v3: [0.67, 0.87]; spaCy + regla: [0.76, 0.93]): no se puede afirmar que uno
  sea más exacto. En rechazo correcto no se solapan (v3: [0.81, 1.00]; spaCy +
  regla: [0.33, 0.77]), aunque la ventaja de v3 está inflada por haberse diseñado
  con esas oraciones a la vista.
- En las oraciones con adjunción preposicional, v3 enumera 2 análisis y spaCy
  devuelve 1 sin indicar la ambigüedad.
- Tiempo medio por oración: 0.13 ms (propio), 1.21 ms (NLTK), 3.19 ms (spaCy). La
  diferencia refleja el tamaño del léxico, no escalabilidad.

## 6. Conclusiones

1. Las CFG son la herramienta adecuada para lenguajes de programación porque
   estos se diseñan para ser libres de contexto y deterministas; lo que no lo es
   se delega al análisis semántico.
2. La concordancia de género y número **sí** cabe en una CFG. Su costo crece como
   el producto de las cardinalidades de los rasgos que concuerdan, y eso motivó
   históricamente las gramáticas de rasgos con unificación.
3. La distancia no es el problema: las dependencias anidadas, por largas que
   sean, son tipo 2.
4. La ambigüedad estructural crece según los números de Catalan y obliga a usar
   un analizador no determinista; la CFG la genera pero no la resuelve.
5. El único punto donde se sale del tipo 2 es la dependencia cruzada de la
   coordinación distributiva, demostrado con clausura y lema de bombeo sobre
   { w c w }. Es el mismo tipo de argumento que Shieber usó para el alemán suizo.
6. La comparación muestra dos enfoques complementarios: la CFG da veredictos
   formales y explicables sobre un fragmento pequeño; spaCy da cobertura amplia
   sin noción de agramaticalidad. La CFG **verifica** la concordancia; spaCy la
   **predice**, y en parte de los casos la corrige sin avisar.

Todos los resultados se reproducen desde el repositorio; las series teóricas se
recalculan de forma independiente con `python -m analisis_formal.verificar_teoria`.

## Referencias

- Aho, A. V., Lam, M. S., Sethi, R. y Ullman, J. D. (2006). *Compilers: Principles, Techniques, and Tools* (2.ª ed.). Addison-Wesley.
- Bar-Hillel, Y., Perles, M. y Shamir, E. (1961). On formal properties of simple phrase structure grammars. *Zeitschrift für Phonetik, Sprachwissenschaft und Kommunikationsforschung*, 14, 143–172.
- Bird, S., Klein, E. y Loper, E. (2009). *Natural Language Processing with Python*. O'Reilly.
- Bresnan, J., Kaplan, R. M., Peters, S. y Zaenen, A. (1982). Cross-serial dependencies in Dutch. *Linguistic Inquiry*, 13(4), 613–635.
- Cantor, D. G. (1962). On the ambiguity problem of Backus systems. *Journal of the ACM*, 9(4), 477–479.
- Chomsky, N. (1956). Three models for the description of language. *IRE Transactions on Information Theory*, 2(3), 113–124.
- Church, K. y Patil, R. (1982). Coping with syntactic ambiguity or how to put the block in the box on the table. *American Journal of Computational Linguistics*, 8(3–4), 139–149.
- Hopcroft, J. E., Motwani, R. y Ullman, J. D. (2007). *Introduction to Automata Theory, Languages, and Computation* (3.ª ed.). Pearson.
- Joshi, A. K. (1985). Tree adjoining grammars: How much context-sensitivity is required to provide reasonable structural descriptions? En *Natural Language Parsing*. Cambridge University Press.
- Knuth, D. E. (1968). Semantics of context-free languages. *Mathematical Systems Theory*, 2(2), 127–145.
- Pullum, G. K. y Gazdar, G. (1982). Natural languages and context-free languages. *Linguistics and Philosophy*, 4(4), 471–504.
- Shieber, S. M. (1985). Evidence against the context-freeness of natural language. *Linguistics and Philosophy*, 8(3), 333–343.
- Sipser, M. (2013). *Introduction to the Theory of Computation* (3.ª ed.). Cengage Learning.
