# Guion de la presentación — Fase 1 (15–20 minutos)

La presentación sigue el mismo hilo que el informe: primero la CFG funcionando
donde debe, luego estirándola al español hasta encontrar el punto exacto donde se
rompe. Cada integrante presenta su parte; Persona 4 abre, enlaza y cierra.

Todos los comandos se ejecutan desde la raíz del repositorio con Python ≥ 3.10.
Los bloques 1, 2, 3 y 5 no necesitan nada instalado; el bloque 4 usa NLTK y
spaCy, y si la máquina del aula no los tiene se muestran los archivos ya
generados en `comparacion_nlp/resultados/` y `analisis_formal/resultados/`.

## Distribución del tiempo

| Min | Bloque | Quién | Qué se muestra |
| ---: | :--- | :--- | :--- |
| 0–3 | Marco teórico | Persona 4 | Jerarquía de Chomsky, anidado frente a cruzado, pregunta guía |
| 3–7 | Parser de C | Persona 1 | Programa válido, inválido con línea y columna, árbol SVG |
| 7–12 | Extensión al español | Persona 2 | v1 → v2 → v3, explosión, ambigüedad, el muro |
| 12–15 | Pruebas y NLP | Persona 3 | Corpus de C, tabla de métricas, NLTK 61/61 |
| 15–18 | Análisis formal y cierre | Persona 4 | L1–L6 en la jerarquía, demostración de L6, spaCy, 1 de 13 |
| 18–20 | Preguntas | Todos | Ver banco de preguntas abajo |

## Bloque 1 — Marco teórico (Persona 4, 3 min)

1. **Pregunta guía:** "¿Por qué la misma herramienta que analiza C sin problemas
   no alcanza para el español, y en qué punto exacto deja de alcanzar?"
2. Tabla de la jerarquía (tipos 0–3 y el reconocedor de cada uno).
3. La idea clave en una diapositiva:
   - Anidado (a₁ a₂ b₂ b₁): un autómata de pila lo maneja → tipo 2.
   - Cruzado (a₁ a₂ b₁ b₂): habría que comparar contra el fondo de la pila → tipo 1.
4. Adelanto de la conclusión: "la concordancia cabe, la distancia cabe, el cruce
   no cabe".

## Bloque 2 — Parser de C (Persona 1, 4 min)

```bash
python -m fase1_parser_formal.cli --archivo validacion/programa_valido.c
python -m fase1_parser_formal.cli --archivo validacion/programa_invalido.c
python -m fase1_parser_formal.cli --texto "int main(){int x=(1+2)*3;return x;}" --svg arbol.svg
```

Puntos a mencionar: el léxico es una expresión regular (tipo 3); precedencia por
estratificación expresión → término → factor; `if (2)` rechazado por decisión de
alcance; el `else` colgante es el único conflicto LL(1) y se resuelve
consumiendo el `else` (se asocia al `if` más cercano).

## Bloque 3 — Extensión al español (Persona 2, 5 min)

```bash
python -m fase1_extension_espanol.cli --oracion "la gato negros duerme" --version v1   # acepta
python -m fase1_extension_espanol.cli --oracion "la gato negros duerme" --version v2   # rechaza
python -m fase1_extension_espanol.cli --explosion
python -m fase1_extension_espanol.cli --oracion "el gato que ve los ratones duerme"
python -m fase1_extension_espanol.cli --ambiguedad
python -m fase1_extension_espanol.cli --muro
```

## Bloque 4 — Pruebas y comparación (Persona 3, 3 min)

```bash
python -m comparacion_nlp.ejecutar_pruebas_c                 # 33 casos de C
python -m comparacion_nlp.comparar --sin-spacy --sin-nltk    # métricas del parser propio, sin dependencias
python -m comparacion_nlp.verificar_ambiguedad               # 1, 2, 5, 14 propio vs NLTK (necesita nltk)
```

Mostrar la tabla v1 / v2 / v3 / spaCy de `comparacion_nlp/resultados/resultados.md`
y que NLTK coincide en 61/61.

## Bloque 5 — Análisis formal y cierre (Persona 4, 3 min)

1. **Clasificación de L1–L6:** cinco son costo o ambigüedad (tipo 2), uno es
   imposibilidad (tipo 1).
2. **Demostración de L6 en tres pasos** (una diapositiva):
   intersección con un regular → homomorfismo a { w c w } → lema de bombeo.
3. **Demo de respaldo** (20 segundos, sin dependencias):
   ```bash
   python -m analisis_formal.verificar_teoria --seccion catalan
   python -m analisis_formal.verificar_teoria --seccion bombeo
   ```
   Una gramática distinta de la del equipo da la misma serie de Catalan, y
   ninguna descomposición sobrevive al bombeo.
4. **spaCy no verifica, predice:** de sus 7 falsos positivos, 2 son rasgos
   vacíos, 3 son límites de la regla y 2 son rasgos "corregidos" en silencio
   ("el gato negra duerme" → spaCy etiqueta "negra" como masculino). Tabla en
   `analisis_formal/resultados/inspeccion_spacy.md`.
5. **El dato que más importa:** de los 13 fallos de v3, solo 1 es formal.
6. **Cierre:** "La CFG no falla con el español por falta de esfuerzo en 12 de 13
   casos. Falla por la jerarquía en exactamente uno, y ese uno es el mismo tipo de
   construcción que usó Shieber para demostrar que el alemán suizo no es libre de
   contexto."

## Banco de preguntas probables

| Pregunta | Respuesta corta |
| :--- | :--- |
| ¿Por qué no usaron LL(1) para el español? | v3 es ambigua y ninguna gramática ambigua es LL(k). Hay cadenas con varios árboles y un analizador determinista solo devuelve uno. |
| ¿La gramática de C es realmente LL(1)? | Sí, salvo el `else` opcional (`else` está en PRIMERO y en SIGUIENTE). Se resuelve consumiéndolo siempre, como hacen los compiladores reales. |
| Si la concordancia cabe, ¿por qué se dice que las CFG no sirven para el español? | Porque el costo crece como el producto de los rasgos (L2) y porque hay construcciones cruzadas (L6). Son dos argumentos distintos: uno práctico, otro formal. |
| ¿Por qué la relativa (L5) no rompe la CFG si la distancia es ilimitada? | Porque es anidada. El autómata de pila tiene el rasgo del sujeto en el tope cuando llega al verbo principal. |
| ¿Por qué 1, 2, 5, 14? | Son números de Catalan: formas de adjuntar k frases preposicionales sin que las ramas se crucen. Con k frases hay C(k + 1) árboles; el analizador sigue con 42, 132, 429. |
| ¿Si el número de árboles es exponencial, cómo los cuentan rápido? | Los árboles comparten subárboles; `contar()` usa programación dinámica, igual que CYK o Earley, en tiempo polinomial. |
| ¿No es suficiente una CFG enorme para el español real? | Para un n acotado sí (actuación). La jerarquía clasifica la competencia; por el mismo motivo se dice que C no es regular aunque nadie anide mil paréntesis. |
| ¿"Respectivamente" no es un argumento semántico, como en inglés? | En inglés sí (Pullum y Gazdar). En español la discordancia es morfológica ("son alta y bajo"), lo que lo acerca al argumento de Shieber, aunque depende de ese juicio de gramaticalidad. |
| En `--muro`, ¿vwx no puede cruzar la c? | Sí puede, y es el caso 4 de la demostración: con \|vwx\| ≤ p solo toca las b de la primera copia y las a de la segunda, y bombear las desbalancea. |
| ¿Dónde cae entonces el español? | En los lenguajes ligeramente dependientes del contexto (TAG, CCG), entre tipo 2 y tipo 1, con análisis polinomial. |
| ¿spaCy es mejor que su parser? | No compiten en lo mismo: spaCy nunca rechaza. En exactitud los intervalos de confianza se solapan; en rechazo correcto la CFG gana, aunque con sesgo de diseño. |
| ¿Por qué spaCy no detecta "el gato negra duerme"? | Porque etiqueta "negra" como masculino: predice el rasgo que concuerda. No verifica, predice. |
| ¿Cómo saben que el número de derivaciones es correcto? | NLTK (Earley) coincide en 61/61, y la serie de Catalan se reproduce con una gramática abstracta independiente. |
| ¿Decidir si una gramática es ambigua se puede automatizar? | No: es indecidible para CFG arbitrarias. |
| ¿C es realmente libre de contexto? | Su sintaxis sí; restricciones como "declarar antes de usar" no, y se resuelven en el análisis semántico. |

## Checklist antes de presentar

- [ ] Probar todos los comandos de la demo en la máquina del aula (Python ≥ 3.10).
- [ ] Correr la suite completa: deben pasar las 89 pruebas.
- [ ] Tener abiertos los SVG de `salidas_ejemplo/` y los `resultados/` por si falla la demo.
- [ ] Persona 2: decidir si se aplica la corrección del texto del lema de bombeo en `muro_cfg.py`.
- [ ] Completar los nombres de los integrantes en el informe.
- [ ] Confirmar que asiste al menos el 50 % + 1 del grupo (requisito del curso).
- [ ] Cada integrante puede explicar su código línea por línea.
