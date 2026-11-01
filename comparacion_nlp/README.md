# Pruebas y comparación con NLP (NLTK y spaCy)

Todo se ejecuta **desde la raíz del repositorio** (igual que el resto del proyecto).

| Archivo | Para qué sirve |
| :--- | :--- |
| `casos_c.py` | 33 casos de C: 12 válidos, 14 inválidos, 7 "fuera del subconjunto" (válidos en C real, rechazados a propósito) |
| `ejecutar_pruebas_c.py` | Corre el corpus y muestra una tabla; `--exportar` escribe cada caso como `.c` en `validacion/c_corpus/` |
| `oro.py` | Las 51 oraciones del equipo + 10 extra, con dos etiquetas: `esperado_v3` y `gramatical_real` |
| `comparar.py` | Parser propio v1/v2/v3 vs NLTK vs spaCy, con métricas, tablas y CSV |
| `resultados/` | Salida generada (`resultados.md`, `resultados.csv`, y `arboles_spacy.txt` si corrió spaCy) |

## Cómo correrlo

```bash
# pruebas automáticas (54 del equipo + 23 nuevas)
python -m unittest tests.test_fase1 tests.test_extension_espanol tests.test_corpus_c tests.test_comparacion_nlp -v

# corpus de C, con tabla
python -m comparacion_nlp.ejecutar_pruebas_c

# comparación: solo parser propio (no necesita nada instalado)
python -m comparacion_nlp.comparar --sin-spacy --sin-nltk

# comparación completa
pip install nltk spacy
python -m spacy download es_core_news_sm
python -m comparacion_nlp.comparar
```

## Qué se verificó y qué no

* **Verificado (corre sin dependencias):** el corpus de C, el gold, las métricas del parser propio, la regla de
  concordancia sobre la salida de spaCy (con objetos simulados) y que la exportación de la gramática a formato NLTK
  reproduce exactamente el conteo de derivaciones del analizador, incluido el caso de 14 análisis.
* **Sin ejecutar todavía:** las llamadas reales a NLTK (`EarleyChartParser`) y a spaCy (`spacy.load`). Se escribieron
  contra la API documentada, pero hay que correrlas en una máquina que las tenga y revisar la salida antes de citar
  números en el informe.

## Decisiones de diseño que conviene poder defender

1. **Dos etiquetas por oración.** `esperado_v3` mide si el parser hace lo que se diseñó; `gramatical_real` mide si la
   oración es español correcto. Mezclarlas escondería los falsos negativos.
2. **spaCy no rechaza oraciones.** Siempre devuelve un árbol. Para compararlo se le aplica una regla de
   concordancia sobre sus rasgos morfológicos (`detectar_discordancias`). Es una heurística nuestra, no una función de
   spaCy, y el informe debe decirlo.
3. **NLTK recibe la misma gramática v3.** No se usa como "otro analizador del español" (NLTK no trae uno), sino como
   verificación cruzada: un analizador estándar debe contar las mismas derivaciones que el nuestro.
4. **Las 51 oraciones del equipo no son una prueba independiente.** La gramática se diseñó mirando esas oraciones, así
   que v3 las pasa por construcción. Las 10 oraciones extra son la única medida fuera de muestra.
5. **Criterio sobre "a" personal.** Oraciones como "el hombre alto ve la mujer en el jardín" omiten la "a" personal,
   algo que el README del equipo declara fuera de alcance. El gold las trata como gramaticales; de lo contrario se
   penalizaría una decisión de alcance y no un error.
