# Marco teórico — Jerarquía de Chomsky y lenguaje natural

Este documento reúne la investigación teórica que sostiene el proyecto. Su
objetivo es que cada resultado de las partes de implementación (parser de C,
extensión al español y comparación con NLP) se pueda ubicar en un nivel concreto
de la jerarquía y explicar con un argumento formal, no solo con la observación
de que "el parser falla".

## 1. La jerarquía de Chomsky

Chomsky (1956, 1959) clasificó las gramáticas formales según la forma que pueden
tener sus producciones. Cada nivel restringe más las reglas, y a cambio gana
propiedades computacionales: reconocedores más simples y más problemas
decidibles.

| Tipo | Gramática | Forma de las producciones | Reconocedor | Ejemplo canónico |
| :--- | :--- | :--- | :--- | :--- |
| 0 | Irrestricta | α → β | Máquina de Turing | Lenguajes recursivamente enumerables |
| 1 | Dependiente del contexto (CSG) | αAβ → αγβ, con γ ≠ ε | Autómata linealmente acotado | { aⁿbⁿcⁿ }, { w c w } |
| 2 | Libre de contexto (CFG) | A → γ | Autómata de pila (PDA) | { aⁿbⁿ }, { w c wᴿ }, paréntesis balanceados |
| 3 | Regular | A → aB o A → a | Autómata finito | identificadores, números, a*b* |

Las inclusiones son estrictas: Regular ⊂ CFL ⊂ CSL ⊂ RE. Cada inclusión tiene
un lenguaje testigo que está en un nivel y no en el anterior, y la herramienta
para demostrarlo es el **lema de bombeo** correspondiente.

### 1.1 Qué significa "libre de contexto"

En una producción A → γ el no terminal A se reescribe igual sin importar qué
símbolos lo rodean. Esa es la propiedad que hace eficientes a las CFG y, al
mismo tiempo, la que les impide expresar que dos partes alejadas de la cadena
"se pongan de acuerdo" si ese acuerdo no está **anidado**.

La intuición correcta viene del reconocedor: un autómata de pila solo puede
comparar el último símbolo que guardó. Por eso reconoce dependencias del tipo
a₁ a₂ a₃ … b₃ b₂ b₁ (anidadas, como paréntesis), pero no del tipo
a₁ a₂ a₃ … b₁ b₂ b₃ (cruzadas), donde habría que comparar contra el fondo de la
pila.

```
Anidada  (CFG sí):   el gato  [que ve los ratones]  duerme
                     ^-------------------------------^
                                  ^---------^

Cruzada  (CFG no):   el niño  y  la niña   son   alto  y  baja   respectivamente
                     ^--------------------------------^
                                 ^--------------------------^
```

### 1.2 Propiedades de las CFG que se usan en el proyecto

- **Lema de bombeo para CFL** (Bar-Hillel, Perles y Shamir, 1961). Si L es libre
  de contexto, existe p tal que toda z ∈ L con |z| ≥ p se puede escribir
  z = uvwxy con |vwx| ≤ p, |vx| ≥ 1 y uvⁱwxⁱy ∈ L para todo i ≥ 0. Se usa en
  sentido contrario: si para alguna z ninguna descomposición sobrevive al
  bombeo, L no es libre de contexto.
- **Propiedades de clausura.** Las CFL son cerradas bajo unión, concatenación,
  estrella, homomorfismo e **intersección con un lenguaje regular**, pero *no*
  bajo intersección entre CFL ni bajo complemento. La intersección con regulares
  y el homomorfismo son las dos operaciones que permiten aislar un fragmento del
  español y reducirlo a un lenguaje de libro.
- **Ambigüedad.** Una CFG es ambigua si alguna cadena tiene dos árboles de
  derivación distintos. Decidir si una CFG arbitraria es ambigua es
  **indecidible** (Cantor, 1962; Floyd, 1962). Además existen lenguajes
  *inherentemente* ambiguos, para los que ninguna CFG es no ambigua.
- **LL(k) y ambigüedad.** Toda gramática LL(k) es no ambigua, porque el
  analizador elige una sola producción con k símbolos de anticipación. La
  contrapositiva explica un hallazgo de la Parte 2: una gramática ambigua no es
  LL(k) para ningún k.
- **Complejidad del análisis.** Cualquier CFG se puede analizar en O(n³) (CYK,
  Earley). El número de *árboles* puede ser exponencial, pero se representan de
  forma compartida en un bosque de tamaño polinomial; por eso contar
  derivaciones con programación dinámica es barato aunque enumerarlas no lo sea.

### 1.3 Más allá de las CFG: lenguajes ligeramente dependientes del contexto

Pasar de tipo 2 a tipo 1 completo tiene un precio alto: el problema de
pertenencia para CSG es PSPACE-completo. Por eso la lingüística computacional
no adoptó las CSG, sino una clase intermedia propuesta por Joshi (1985): los
**lenguajes ligeramente dependientes del contexto** (*mildly context-sensitive*).
Agregan justo lo necesario para dependencias cruzadas acotadas, conservan
análisis en tiempo polinomial y tienen la propiedad de crecimiento constante.
Los formalismos de esta clase son las gramáticas de adjunción de árboles (TAG),
las gramáticas categoriales combinatorias (CCG) y las gramáticas lineales
indexadas, que resultaron ser débilmente equivalentes entre sí.

```
Regular  ⊂  Libre de contexto  ⊂  Ligeramente dependiente del contexto  ⊂  Dependiente del contexto
 (tipo 3)       (tipo 2)              (TAG, CCG; análisis O(n⁶))               (tipo 1)
                  ^                              ^
       lenguajes de programación      donde se ubica el lenguaje natural
```

## 2. Por qué las CFG bastan para los lenguajes de programación

Los lenguajes de programación se **diseñan** para que su sintaxis sea libre de
contexto y, casi siempre, determinista (LL(1) o LR(1)). Eso permite generar
analizadores automáticamente y garantizar un solo árbol por programa. Las
ambigüedades conocidas, como el `else` colgante, se resuelven con una
convención fija (asociar al `if` más cercano), algo que el parser de la Parte 1
implementa por el orden de las alternativas.

Pero incluso en C hay restricciones que no son libres de contexto: que una
variable esté declarada antes de usarse, que los tipos coincidan en una
asignación o que el número de argumentos de una llamada coincida con la
declaración. El lenguaje {w c w} modela exactamente "declarar w y luego usar w".
Los compiladores no lo resuelven en la gramática, sino en el **análisis
semántico**, con una tabla de símbolos (Aho et al., 2006). Esta división de
trabajo es importante para el proyecto: la concordancia del español se parece
mucho más a la verificación de tipos que a la sintaxis pura, y por eso las
soluciones históricas (gramáticas de atributos, unificación de rasgos) son las
mismas en los dos mundos.

## 3. Diferencias entre lenguaje formal y lenguaje natural

| Dimensión | Lenguaje formal (subconjunto de C) | Lenguaje natural (español) | Dónde se ve en el proyecto |
| :--- | :--- | :--- | :--- |
| Origen | Diseñado; la gramática es la definición del lenguaje | Evoluciona; la gramática es una descripción aproximada | La gramática de C es completa por construcción; la del español siempre deja oraciones fuera (13 falsos negativos) |
| Estructura | Fijada y explícita (llaves, `;`, palabras reservadas) | Implícita; el orden de palabras es flexible (SVO, VSO, sujeto tácito) | v3 rechaza el orden verbo-sujeto |
| Ambigüedad | Eliminada por diseño o resuelta por convención | Estructural y léxica, persistente; se resuelve con semántica y contexto | L3 (Catalan) y L4 |
| Recursividad | Anidamiento de bloques y expresiones | Subordinadas, frases preposicionales encadenadas, relativas | L5 funciona porque la recursión es anidada |
| Dependencias de contexto | Delegadas al análisis semántico (tabla de símbolos) | Concordancia, correferencia, dependencias cruzadas | L1, L2, L5, L6 |
| Concordancia | Inexistente en la sintaxis | Morfológica y obligatoria: género, número, persona | Explosión de v1 → v2 → v3 |
| Vocabulario | Cerrado y pequeño | Abierto y en cambio constante | 7 de los 13 falsos negativos son palabras fuera del léxico |
| Error | Binario: el programa compila o no | Gradual: hay oraciones dudosas, aceptables en un dialecto y no en otro | spaCy nunca rechaza; la CFG siempre decide |

### 3.1 Ambigüedad

En C, `a - b - c` tiene un solo árbol porque la gramática fija la asociatividad.
En español, "el niño ve el telescopio en la casa" tiene dos lecturas legítimas
(la casa como lugar donde está el telescopio o donde ocurre la acción), y ambas
son gramaticales. Church y Patil (1982) mostraron que el número de análisis de
una secuencia de frases preposicionales sigue los **números de Catalan**, que
crecen como 4ⁿ / (n^{3/2}√π). La sintaxis sola no tiene criterio para elegir: la
decisión requiere semántica, conocimiento del mundo o estadística.

### 3.2 Recursividad

Ambos tipos de lenguaje son recursivos, y esa es la razón por la que ninguno es
regular. Chomsky (1957) argumentó que el inglés no es de estados finitos a
partir de construcciones anidadas del tipo *if … then*, *either … or*. Lo
importante para el proyecto es que la recursión **anidada** cabe en una CFG; la
cruzada no.

### 3.3 Dependencias de contexto y concordancia

La concordancia exige que dos constituyentes compartan rasgos. Una producción
de CFG no puede expresar "el rasgo de este hijo es igual al de aquel"; solo
puede **enumerar** las combinaciones permitidas metiendo el rasgo en el nombre
del no terminal. Mientras los rasgos sean finitos esto sigue siendo una CFG
(GPSG, de Gazdar et al., 1985, se apoya justamente en eso), pero el número de
producciones crece como el producto de las cardinalidades de los rasgos que
concuerdan. Las gramáticas de atributos (Knuth, 1968) y las de unificación
(LFG, Kaplan y Bresnan, 1982; HPSG, Pollard y Sag, 1994) factorizan esa
explosión: escriben la regla una vez con variables de rasgo y dejan la
coincidencia a un mecanismo de unificación.

## 4. ¿Es el lenguaje natural libre de contexto?

Fue un debate abierto durante casi treinta años, y vale la pena conocer su
historia porque el proyecto reproduce sus argumentos.

1. **Primeros argumentos (1960–1980).** Se propusieron pruebas basadas en
   *respectively* del inglés, en la comparación y en otros fenómenos. Pullum y
   Gazdar (1982) las revisaron una por una y mostraron que todas eran
   defectuosas: o los datos eran discutibles o la dependencia era semántica y
   no sintáctica.
2. **Holandés (Bresnan, Kaplan, Peters y Zaenen, 1982).** Las subordinadas
   holandesas tienen dependencias cruzadas entre verbos y sus objetos. Sin
   embargo, como el holandés no marca caso, el conjunto de *cadenas* sí es libre
   de contexto; el argumento solo afecta la capacidad generativa **fuerte**
   (las estructuras), no la débil.
3. **Alemán suizo (Shieber, 1985).** El dialecto de Zúrich marca caso dativo y
   acusativo en los objetos, y cada verbo exige un caso específico. Eso
   convierte la dependencia cruzada en un hecho morfológico visible en la
   cadena. Shieber intersecó el lenguaje con un regular, aplicó un homomorfismo
   y obtuvo { w aᵐ bⁿ x cᵐ dⁿ y : m, n ≥ 1 }, que no es libre de contexto
(los dativos aᵐ deben coincidir con los verbos cᵐ y los acusativos bⁿ con dⁿ,
en orden cruzado). Es la
   prueba aceptada de que al menos una lengua natural no es CFL, incluso en
   capacidad débil. Culy (1985) dio un argumento similar para el bambara.

**Relación con el proyecto.** El hallazgo L6 usa la misma técnica que Shieber
aplicada al español: la coordinación distributiva con "respectivamente" crea una
dependencia cruzada y, a diferencia del inglés, el español la hace visible con
concordancia de género y número en los adjetivos. Por eso el argumento es más
fuerte que el de *respectively* del inglés que Pullum y Gazdar refutaron, aunque
hereda una objeción posible que se discute en `analisis_resultados.md`.

## 5. Enfoques estadísticos y por qué no compiten en el mismo terreno

Las herramientas modernas no intentan decidir pertenencia a un lenguaje:

- **PCFG** (gramáticas probabilísticas). Asignan probabilidad a cada
  producción y eligen el árbol más probable. Atacan la ambigüedad, no la
  capacidad generativa: una PCFG sigue siendo una CFG.
- **Análisis de dependencias basado en transiciones** (spaCy). Un modelo
  neuronal decide paso a paso cómo unir palabras y devuelve **siempre un único
  árbol**, aunque la entrada sea agramatical. No hay noción de "rechazo".
- **Modelos de lenguaje grandes.** Asignan probabilidad a secuencias y
  capturan concordancia y dependencias largas de forma implícita, sin
  garantías formales ni árboles explícitos (tema de la Fase 2).

Esto define cómo se debe leer la comparación: la CFG da un **veredicto formal y
explicable** sobre un fragmento pequeño; spaCy da **cobertura amplia y
robusta** sin veredicto. Medir a spaCy en "rechazo correcto" exige construir una
regla encima de sus rasgos, y esa medición evalúa la regla tanto como el
modelo.

## Referencias

- Aho, A. V., Lam, M. S., Sethi, R. y Ullman, J. D. (2006). *Compilers: Principles, Techniques, and Tools* (2.ª ed.). Addison-Wesley.
- Bar-Hillel, Y., Perles, M. y Shamir, E. (1961). On formal properties of simple phrase structure grammars. *Zeitschrift für Phonetik, Sprachwissenschaft und Kommunikationsforschung*, 14, 143–172.
- Bird, S., Klein, E. y Loper, E. (2009). *Natural Language Processing with Python*. O'Reilly.
- Bresnan, J., Kaplan, R. M., Peters, S. y Zaenen, A. (1982). Cross-serial dependencies in Dutch. *Linguistic Inquiry*, 13(4), 613–635.
- Cantor, D. G. (1962). On the ambiguity problem of Backus systems. *Journal of the ACM*, 9(4), 477–479.
- Chomsky, N. (1956). Three models for the description of language. *IRE Transactions on Information Theory*, 2(3), 113–124.
- Chomsky, N. (1957). *Syntactic Structures*. Mouton.
- Chomsky, N. (1959). On certain formal properties of grammars. *Information and Control*, 2(2), 137–167.
- Church, K. y Patil, R. (1982). Coping with syntactic ambiguity or how to put the block in the box on the table. *American Journal of Computational Linguistics*, 8(3–4), 139–149.
- Culy, C. (1985). The complexity of the vocabulary of Bambara. *Linguistics and Philosophy*, 8(3), 345–351.
- Floyd, R. W. (1962). On ambiguity in phrase structure languages. *Communications of the ACM*, 5(10), 526.
- Gazdar, G., Klein, E., Pullum, G. y Sag, I. (1985). *Generalized Phrase Structure Grammar*. Blackwell.
- Hopcroft, J. E., Motwani, R. y Ullman, J. D. (2007). *Introduction to Automata Theory, Languages, and Computation* (3.ª ed.). Pearson.
- Joshi, A. K. (1985). Tree adjoining grammars: How much context-sensitivity is required to provide reasonable structural descriptions? En Dowty, Karttunen y Zwicky (eds.), *Natural Language Parsing*. Cambridge University Press.
- Jurafsky, D. y Martin, J. H. (2024). *Speech and Language Processing* (3.ª ed., borrador). Stanford University.
- Kaplan, R. M. y Bresnan, J. (1982). Lexical-Functional Grammar: A formal system for grammatical representation. En Bresnan (ed.), *The Mental Representation of Grammatical Relations*. MIT Press.
- Knuth, D. E. (1968). Semantics of context-free languages. *Mathematical Systems Theory*, 2(2), 127–145.
- Pollard, C. y Sag, I. A. (1994). *Head-Driven Phrase Structure Grammar*. University of Chicago Press.
- Pullum, G. K. y Gazdar, G. (1982). Natural languages and context-free languages. *Linguistics and Philosophy*, 4(4), 471–504.
- Shieber, S. M. (1985). Evidence against the context-freeness of natural language. *Linguistics and Philosophy*, 8(3), 333–343.
- Sipser, M. (2013). *Introduction to the Theory of Computation* (3.ª ed.). Cengage Learning.
