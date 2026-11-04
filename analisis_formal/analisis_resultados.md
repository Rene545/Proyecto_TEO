# Análisis formal de los resultados

Este documento toma los resultados de las tres partes de implementación y los
ubica en la jerarquía de Chomsky. Todos los números que aparecen aquí se pueden
reproducir con:

```bash
python -m analisis_formal.verificar_teoria          # series teóricas (sin dependencias)
python -m analisis_formal.inspeccionar_spacy        # los 7 falsos positivos de spaCy (necesita spaCy)
python -m unittest tests.test_analisis_formal -v    # 12 pruebas que cruzan ambas implementaciones
```

`verificar_teoria` no importa nada del parser ni de la comparación con NLP:
recalcula las series por un camino independiente (una gramática abstracta
mínima, fórmulas cerradas y fuerza bruta). Las pruebas de
`tests/test_analisis_formal.py` comparan esos números con los que producen
`fase1_extension_espanol` y `comparacion_nlp`; si coinciden es porque los
resultados no dependen de un detalle de implementación. Las salidas ya
generadas están en `analisis_formal/resultados/`.

Además se volvió a correr `python -m comparacion_nlp.comparar` completo (NLTK y
spaCy 3.8 con `es_core_news_sm` 3.8.0): todas las tablas de
`comparacion_nlp/resultados/resultados.md` salen idénticas, salvo los tiempos.

## 1. Resumen

Los resultados del proyecto caen en tres clases distintas, y la conclusión más
importante es no mezclarlas:

| Clase | Qué significa | Casos | ¿Sale de tipo 2? |
| :--- | :--- | :--- | :--- |
| **Costo** | La CFG puede, pero el tamaño de la gramática crece rápido | L1, L2, L5 | No |
| **Ambigüedad** | La CFG genera bien, pero no puede elegir entre árboles | L3, L4 | No |
| **Imposibilidad** | No existe CFG finita que genere el lenguaje | L6 | **Sí: tipo 2 → tipo 1** |

Y en la evaluación empírica, de las 13 oraciones gramaticales que v3 rechaza,
**solo 1** corresponde a la imposibilidad formal; las otras 12 son decisiones de
alcance (léxico cerrado, construcciones no implementadas).

## 2. Mapa de cada limitación a la jerarquía

| | Fenómeno | Regla donde se manifiesta | Clase de dependencia | Nivel mínimo | Evidencia |
| :--- | :--- | :--- | :--- | :--- | :--- |
| L1 | Sobregeneración sin rasgos | `FN -> DET SUST ADJ` (v1) | Concordancia local | Tipo 2 alcanza | v1 acepta "la gato negros duerme"; 11 falsos positivos |
| L2 | Explosión al codificar rasgos | Toda regla nominal de `construir_v2` / `construir_v3` | Concordancia local finita | Tipo 2 alcanza | v1 = 5, v2 = 22, v3 = 49; con persona: v2 = 114, v3 = 189 |
| L3 | Ambigüedad de adjunción de FP | `MODN -> FPREP MODN` compite con `MODV -> FPREP MODV` | Estructural | Tipo 2 (gramática ambigua) | 1, 2, 5, 14 en v3 y NLTK; el analizador sigue con 42, 132, 429 |
| L4 | Ambigüedad léxica | Emparejamiento léxico en `analizador._generar` | Léxica que se propaga | Tipo 2 | "baja" es Adj [f,sg] y V.intr [sg] ("la niña baja") |
| L5 | Concordancia a distancia | `MODN -> SUBORD MODN` con `SUBORD -> PRON_REL FV` | Ilimitada pero **anidada** | Tipo 2 alcanza | "el gato que ve los ratones duerme" se acepta y su versión discordante se rechaza |
| L6 | Coordinación distributiva | `muro_cfg.construir_v3_respectivamente` | **Cruzada** | **Tipo 1** | Parche: 16, 80, 336, 1360, 5456 producciones |

## 3. L1 y L2 — La concordancia sí cabe en una CFG, pero cuesta

**Argumento.** Sea F el conjunto de rasgos que una regla obliga a coincidir y
Vᵣ el conjunto de valores del rasgo r. Una CFG no puede compartir variables entre
hijos, así que la única forma de imponer la coincidencia es crear una copia de la
regla por cada combinación de valores:

    copias por regla = Π_{r ∈ F} |Vᵣ|

| Regla (forma conceptual) | Rasgos que concuerdan | Copias |
| :--- | :--- | ---: |
| FN → DET SUST ADJ | género × número | 2 × 2 = 4 |
| sujeto–verbo | número | 2 |
| sujeto–verbo, con persona | número × persona | 2 × 3 = 6 |
| FN con género, número y persona | género × número × persona | 12 |

En v3 las reglas reales son `FN -> DET NUC`, `NUC -> SUST MODN` y las de `MODN`,
cada una con una copia por combinación. Lo que mide `cli.py --explosion`
confirma el patrón: pasar de 4 a 12 combinaciones lleva v2 de 22 a 114
producciones y v3 de 49 a 189. No es exactamente ×3 porque las reglas sin
concordancia (`MODV`, `FPREP`) no se multiplican.

Como los rasgos tienen un número **finito** de valores, el resultado sigue siendo
una CFG finita: L1 y L2 no son límites de la jerarquía, son límites prácticos.
Esto explica también la observación de la Parte 2 de que el tiempo verbal "no
cuesta nada": un rasgo que no participa en ninguna concordancia no aparece en F
y no multiplica nada.

**Lectura.** Es el mismo problema que llevó a GPSG a introducir metarreglas y a
LFG/HPSG a usar unificación. Ninguno de esos formalismos (con rasgos finitos)
aumenta el poder generativo: solo describen la misma CFG de forma compacta. Es
análogo a que un compilador no meta la tabla de tipos dentro de la gramática.

## 4. L3 — Ambigüedad estructural y números de Catalan

**Resultado empírico.** Con k frases preposicionales encadenadas después del
objeto, v3 y NLTK enumeran 1, 2, 5 y 14 árboles. Se extendió la prueba con el
analizador del equipo hasta k = 6 ("… en la casa con el hombre de la niña") y
la serie continúa 42, 132, 429.

**Explicación.** `verificar_teoria` reproduce la serie con una gramática
abstracta de tres reglas, sin léxico del español:

```
SV -> V SN | SV SP
SN -> N    | SN SP
SP -> P SN
```

Esta gramática es recursiva por la izquierda y la de v3 es recursiva por la
derecha (`MODN -> FPREP MODN`, `MODV -> FPREP MODV`), porque el analizador
descendente no admite recursión izquierda. Que dos gramáticas con forma distinta
den exactamente la misma serie confirma que el número de análisis es una
propiedad del fenómeno y no de cómo se escribieron las reglas.

| Frases preposicionales (k) | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Gramática abstracta | 1 | 2 | 5 | 14 | 42 | 132 | 429 |
| Analizador v3 del equipo | 1 | 2 | 5 | 14 | 42 | 132 | 429 |
| Catalan(k + 1) | 1 | 2 | 5 | 14 | 42 | 132 | 429 |

Cada FP puede adjuntarse a cualquier constituyente "abierto" a su izquierda (el
verbo o alguno de los nombres anteriores) sin que las ramas se crucen. Contar las
formas de hacerlo sin cruces es contar árboles binarios, y eso da los números de
Catalan (Church y Patil, 1982). Con la indexación habitual, k frases dan
**C(k + 1)** análisis, donde C(n) = (2n)! / ((n + 1)! n!) y crece como
4ⁿ / (n^{3/2}√π): crecimiento exponencial.

**Consecuencias formales.**

1. v3 es **ambigua**, por lo tanto no es LL(k) para ningún k. Es la razón formal
   de que la Parte 2 haya tenido que abandonar el análisis determinista.
2. La CFG no tiene ningún mecanismo para preferir un árbol. Desambiguar exige
   semántica o probabilidades (PCFG, modelos neuronales).
3. Aunque el número de árboles crece exponencialmente, contarlos es polinomial
   (programación dinámica sobre un bosque compartido, igual que CYK o Earley).
   Eso explica por qué `contar()` es barato y `analizar()` no.
4. No hay una prueba general de que la ambigüedad desaparezca reescribiendo la
   gramática: decidir si una CFG es ambigua es indecidible.

**Sobre la notación.** El README decía "árboles sobre n puntos de adjunción es
C(n)". Es correcto si n cuenta los puntos de adjunción (k + 1); contando frases
preposicionales es C(k + 1). Se aclaró en el README.

## 5. L5 — Dependencia ilimitada no es lo mismo que dependencia cruzada

**Resultado.** "el gato que ve los ratones duerme" se acepta y la versión con el
verbo principal en plural se rechaza, aunque entre el sujeto y su verbo cabe una
subordinada completa.

**Explicación.** La dependencia es de distancia **no acotada** pero **anidada**:

```
el gato  [ que ve los ratones ]  duerme
  sg  ───────────────────────────── sg
             [ ve ─── ratones ]
```

Abstrayendo, tiene la forma de { w c wᴿ } o de paréntesis balanceados, que son
libres de contexto. El autómata de pila apila el número del sujeto, procesa la
subordinada (que apila y desapila lo suyo) y al llegar al verbo principal el
número del sujeto vuelve a estar en el tope. En la gramática esto corresponde a
llevar el rasgo en el no terminal que domina todo el grupo nominal.

**Lectura.** Es un resultado negativo útil: refuta la creencia de que "distancia
larga" implica "no libre de contexto". El riesgo real es de ingeniería: cualquier
regla recursiva que no propague el rasgo rompe la concordancia en silencio, y la
gramática sigue pareciendo correcta.

## 6. L6 — La dependencia cruzada y la salida de tipo 2

### 6.1 El fenómeno

```
el niño   y   la niña    son    alto   y   baja    respectivamente
 m,sg  ───────────────────────── m,sg
               f,sg  ─────────────────────── f,sg
```

El adjetivo i concuerda con el sujeto i. Las dependencias se **cruzan**.

### 6.2 Demostración de que no es libre de contexto

Sea E el conjunto de oraciones gramaticales del fragmento. Se supone, por
contradicción, que E es libre de contexto.

**Paso 1 — Intersección con un regular.** Sea R el lenguaje regular

    R = (DET SUST y)⁺ DET SUST son ADJ (y ADJ)⁺ respectivamente

escrito sobre las palabras del léxico. Como las CFL son cerradas bajo
intersección con regulares, E ∩ R sería libre de contexto. E ∩ R contiene
exactamente las coordinaciones distributivas bien formadas de cualquier
longitud n ≥ 2.

**Paso 2 — Homomorfismo.** Sea Σ = {a, b, d, e} un símbolo por cada par
(género, número): a = (m, sg), b = (f, sg), d = (m, pl), e = (f, pl). Se define h
sobre las palabras:

- cada sustantivo y cada adjetivo → el símbolo de su par de rasgos;
- `son` → c;
- determinantes, `y` y `respectivamente` → ε.

Las CFL son cerradas bajo homomorfismo, así que h(E ∩ R) sería libre de
contexto. Pero por la condición de concordancia distributiva:

    h(E ∩ R) = { w c w : w ∈ Σ*, |w| ≥ 2 }

**Paso 3 — Lema de bombeo.** Se demuestra que L = { w c w } no es libre de
contexto (basta con el subalfabeto {a, b}). Sea p la constante del lema y

    z = aᵖ bᵖ c aᵖ bᵖ ∈ L

Toda descomposición z = uvwxy con |vwx| ≤ p y |vx| ≥ 1 cae en uno de estos
casos:

1. **v o x contiene la c.** Con i = 0 la cadena no tiene c, así que no está en L.
2. **vwx está completamente antes de la c.** Con i = 0 la primera copia pierde
   símbolos y la segunda no; las mitades tienen longitud distinta.
3. **vwx está completamente después de la c.** Simétrico al caso 2.
4. **vwx cruza la c sin contenerla en v ni en x.** Entonces v está dentro de bᵖ
   (final de la primera copia) y x dentro de aᵖ (inicio de la segunda), porque
   |vwx| ≤ p no alcanza para llegar a las a de la primera copia ni a las b de la
   segunda. Con i = 0 la primera mitad queda aᵖ bᵖ⁻ʳ y la segunda aᵖ⁻ˢ bᵖ con
   r + s ≥ 1; si r ≥ 1 la primera mitad termina con menos b, y si s ≥ 1 la segunda
   empieza con menos a, así que las mitades son distintas.

En todos los casos uvⁱwxⁱy ∉ L para algún i, lo que contradice el lema. Por lo
tanto L no es libre de contexto, h(E ∩ R) tampoco, y entonces **E no es libre de
contexto**. ∎

El script lo comprueba por fuerza bruta para p = 1, …, 7: revisa todas las
descomposiciones (hasta 2 758 para p = 7) y ninguna sobrevive al bombeo. Eso no
reemplaza la demostración, pero sirve para mostrarla en vivo. La prueba
`test_homomorfismo_lleva_la_oracion_correcta_a_wcw` aplica h al léxico real del
equipo: las oraciones correctas de `muro_cfg` (n = 2 y n = 3) caen en { w c w }
y la cruzada no.

**Sobre el texto de `muro_cfg.py`.** El argumento que imprime `cli.py --muro`
dice que vwx "no puede tocar las dos copias de w a la vez (están separadas por
más de p símbolos)". Eso no es exacto: el final de la primera copia y el inicio
de la segunda están separados solo por la c, así que vwx sí puede tocar ambas
(caso 4). La conclusión se mantiene, porque en ese caso bombear quita b de una
mitad y a de la otra, pero si el docente lo nota conviene tener el caso 4 a mano.
Se propone reemplazar ese paso del texto por los cuatro casos de 6.2.

### 6.3 En qué nivel sí cae

{ w c w } es dependiente del contexto (tipo 1): un autómata linealmente acotado
lo reconoce marcando un símbolo de la primera mitad, buscando su pareja en la
segunda y repitiendo, sin salir de la cinta de entrada. El salto es exactamente
**tipo 2 → tipo 1**. Más aún, el lenguaje copia está en la clase ligeramente
dependiente del contexto (lo genera una TAG), que es donde la literatura ubica
al lenguaje natural.

### 6.4 El costo de forzarlo con una CFG

Para cada longitud máxima n sí existe una CFG: basta enumerar las 4ᵏ secuencias
de rasgos para cada k ≤ n.

    |P|(n) = Σ_{k=2}^{n} 4ᵏ = (4ⁿ⁺¹ − 16) / 3

| n máximo | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Producciones | 16 | 80 | 336 | 1 360 | 5 456 | 21 840 | 87 376 |

La fórmula reproduce exactamente la tabla de la Parte 2 y coincide con
`muro_cfg.producciones_necesarias` para n = 2…8 (prueba
`test_formula_cerrada_coincide_con_muro_cfg`). El crecimiento es
exponencial en n, y para "todo n" haría falta una gramática infinita. Esa es la
diferencia entre L2 (crece, pero termina) y L6 (no termina).

### 6.5 Objeciones que conviene tener preparadas

1. **Competencia frente a actuación.** El argumento exige n no acotado; nadie
   coordina veinte sujetos. Para el español que realmente se produce, una CFG
   enorme alcanzaría. La respuesta es que la jerarquía clasifica la
   *competencia* (el conjunto de oraciones que la gramática del idioma
   permite), igual que se dice que C no es regular aunque nadie anide mil
   paréntesis.
2. **¿La concordancia con "respectivamente" es sintáctica o semántica?** Es la
   objeción con la que Pullum y Gazdar (1982) descartaron el argumento de
   *respectively* en inglés: allí "John and Mary are a man and a woman
   respectively" falla por significado, no por forma. En español la
   discordancia es **morfológica** ("son alta y bajo" para "el niño y la niña"),
   lo que acerca el argumento al de Shieber. Aun así, se puede sostener que el
   género del adjetivo se elige por referencia semántica. Lo honesto es
   presentarlo como un argumento fuerte pero dependiente de ese juicio de
   gramaticalidad, y señalar que el alemán suizo es el caso que la comunidad
   acepta sin discusión.
3. **"Entonces el español no es libre de contexto".** Lo que se demostró es que
   el fragmento modelado no lo es, bajo el juicio anterior. Eso basta para
   concluir que **ninguna CFG puede describir el español completo**, porque si
   el español fuera CFL, su intersección con R también lo sería.

## 7. Interpretación de la evaluación empírica

### 7.1 Qué dicen los números

| Sistema | Precisión | Cobertura | Rechazo correcto | Exactitud |
| :--- | ---: | ---: | ---: | ---: |
| v1 | 0.607 | 0.378 | 0.312 | 0.361 |
| v2 | 1.000 | 0.378 | 1.000 | 0.541 |
| v3 | 1.000 | 0.711 | 1.000 | 0.787 |
| spaCy + regla | 0.863 | 0.978 | 0.562 | 0.869 |

Las cuatro filas se recalcularon a partir de las matrices de confusión y
coinciden; para v1, v2 y v3 una prueba verifica además que esas matrices salen
de correr el parser sobre el gold (`test_matrices_del_analisis_coinciden_con_el_gold`).

- **v1 → v2** muestra L1 en datos: agregar rasgos elimina los 11 falsos
  positivos sin perder cobertura. La concordancia es un filtro, no una fuente de
  cobertura.
- **v2 → v3** muestra el precio de L2 compensado: más reglas recuperan 15
  oraciones gramaticales sin introducir falsos positivos.
- **v3 frente a spaCy** no es una carrera entre dos analizadores del mismo
  tipo. La CFG maximiza precisión y rechazo (decide pertenencia); spaCy maximiza
  cobertura (siempre produce un árbol). Ni siquiera la mayor exactitud de spaCy
  dice mucho, por lo que se ve en 7.2.

### 7.2 Qué tan finos son esos números

Con 61 oraciones, cada métrica tiene un margen amplio. Intervalos de Wilson al
95 %:

| Sistema | Exactitud | Rechazo correcto |
| :--- | :--- | :--- |
| v3 | [0.67, 0.87] | [0.81, 1.00] |
| spaCy + regla | [0.76, 0.93] | [0.33, 0.77] |

- En **exactitud** los intervalos se solapan: con esta muestra no se puede
  afirmar que spaCy + regla sea más exacto que v3.
- En **rechazo correcto** los intervalos no se solapan: la ventaja de la CFG
  para detectar oraciones agramaticales sí es robusta, aunque está inflada
  porque esas 16 oraciones se conocían al diseñar la gramática.

### 7.3 Clasificación de los 13 falsos negativos de v3

| Causa | Oraciones | Tipo de límite |
| :--- | :--- | :--- |
| Coordinación distributiva (L6) | "el niño y la niña son alto y baja respectivamente" | **Formal**: tipo 2 → tipo 1 |
| Coordinación general con "y" (2) | "el niño y la niña duermen", "el gato duerme y el perro ladra" | Alcance: es libre de contexto, no se implementó |
| Vocabulario fuera del léxico (7) | las 7 extra con palabras fuera del léxico ("pescado", "parque", "yo", "María", "café", "al", "dijo"…) | Alcance: ampliar el léxico |
| Construcciones no cubiertas (3) | "El libro que compró la niña es viejo", "La casa de los niños es pequeña", "Duerme el gato" | Alcance: relativo de objeto, copulativa y orden V-S; todas sus palabras están en el léxico |

En `comparacion_nlp` las dos coordinaciones generales aparecen etiquetadas
"ver limitaciones L6" porque están en el mismo bloque del archivo de
oraciones, pero no son dependencias cruzadas: "el niño y la niña duermen" solo
exige que un sujeto coordinado concuerde en plural con el verbo, lo cual es
una regla libre de contexto más.

Doce de trece fallos se corrigen sin salir de las CFG. Atribuir los 13 a "las
CFG no pueden" sería falso. Y en la medida fuera de muestra (las 10 oraciones
extra), v3 acepta 0 de 10, lo que dice más sobre el léxico cerrado que sobre la
jerarquía.

### 7.4 Amenazas a la validez

- **Sesgo de diseño.** La gramática se construyó viendo las 51 oraciones del
  equipo; el 0.941 sobre ese conjunto mide diseño, no generalización.
- **Muestra pequeña.** 61 oraciones, 16 agramaticales; ver 7.2.
- **La regla sobre spaCy.** La "detección de discordancia" de spaCy es una
  heurística del equipo; sus resultados evalúan la regla tanto como el modelo
  (ver 7.5).
- **Versión del modelo.** spaCy es estadístico y sus etiquetas pueden cambiar
  entre versiones. Los resultados se reprodujeron con spaCy 3.8 y
  `es_core_news_sm` 3.8.0.

### 7.5 Por qué spaCy + regla deja pasar 7 oraciones agramaticales

El borrador revisó a mano 3 de los 7 falsos positivos y presumía que los otros 4
eran del mismo tipo. Con `inspeccionar_spacy.py` se revisaron los 7 comparando
los rasgos que asigna spaCy con los rasgos reales del léxico del equipo. La
presunción era **correcta para las relativas pero no para la concordancia
simple**: aparece un tercer mecanismo que no se había visto.

| Oración agramatical | Mecanismo | Evidencia |
| :--- | :--- | :--- |
| los gato duermen | Rasgo vacío | spaCy no asigna género ni número a "gato" |
| el gato duermen | Rasgo vacío | ídem |
| el gato ve los ratón | **Rasgo asimilado** | spaCy marca "ratón" como **plural**, copiando al determinante |
| el gato negra duerme | **Rasgo asimilado** | spaCy marca "negra" como **masculino**, copiando al sustantivo |
| el gato que duermen ve el ratón | Regla: relativa | "que" no tiene número; la discordancia gato ~ duermen pasa por `acl`, que la regla no revisa (además "que" sale como `obj`) |
| los gatos que duerme ven los ratones | Regla: relativa | ídem, con "que" como `nsubj` |
| la niña que compran un libro duerme | Regla: relativa | ídem |

- **Rasgo vacío (2):** el modelo no da información; la regla no puede comparar.
- **Rasgo asimilado (2):** es el hallazgo nuevo. El etiquetador morfológico de
  spaCy predice los rasgos a partir del contexto, y ante una discordancia le
  asigna a una de las palabras el valor que concuerda con su vecina. En la
  práctica **corrige la oración en silencio**: la discordancia desaparece de la
  representación antes de que cualquier regla pueda verla. Esto refuerza la
  conclusión del borrador ("spaCy no tiene noción de agramaticalidad") con un
  mecanismo concreto: un modelo entrenado solo con español correcto tiende a
  leer cualquier entrada como español correcto.
- **Regla (3):** limitación de la heurística del equipo, no del modelo. Se
  corregiría siguiendo `acl` hasta el antecedente cuando el sujeto es un
  relativo.

Visto desde la jerarquía: la CFG rechaza esas 7 porque **verifica** la
concordancia; spaCy no la verifica, la **predice**, y por eso solo tres de los
siete fallos (los de la relativa) se arreglarían mejorando la regla.

## 8. Conclusiones

1. La CFG modela correctamente el subconjunto de C, porque ese lenguaje se
   diseñó para ser LL(1); las restricciones no libres de contexto de C se
   delegan al análisis semántico.
2. La concordancia de género y número **sí** cabe en una CFG; su costo crece como
   el producto de las cardinalidades de los rasgos que concuerdan (L1, L2).
3. La distancia no es el problema: las dependencias anidadas, por largas que
   sean, siguen siendo tipo 2 (L5).
4. La ambigüedad estructural crece según los números de Catalan; la CFG la
   genera pero no la resuelve, y por eso el español exige un analizador no
   determinista (L3).
5. La dependencia cruzada de "respectivamente" es el único punto donde se sale
   de tipo 2. Se demostró con intersección con un regular, homomorfismo y lema
   de bombeo sobre { w c w }, y se cuantificó: el parche cuesta (4ⁿ⁺¹ − 16) / 3
   producciones (L6).
6. Empíricamente, 1 de 13 fallos es formal y 12 son de alcance. Los sistemas
   estadísticos no compiten en el mismo terreno: spaCy cubre todo pero no
   rechaza nada; la CFG rechaza con garantías pero cubre poco.
7. spaCy no solo deja de detectar discordancias: en 2 de sus 7 falsos positivos
   asigna a la palabra discordante el rasgo que concuerda, es decir, corrige la
   oración en silencio. La CFG verifica la concordancia; el modelo la predice.
