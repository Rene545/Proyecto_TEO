# Resultados de la comparación (generado por `comparacion_nlp.comparar`)

Oraciones: 61 (51 del equipo + 10 extra fuera de alcance). Positivo = "la oración es gramatical/aceptable".

## 1. Todas las oraciones

| Sistema | TP | FP | FN | TN | Precisión | Cobertura | Rechazo correcto | Exactitud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Parser propio v1 | 17 | 11 | 28 | 5 | 0.607 | 0.378 | 0.312 | 0.361 |
| Parser propio v2 | 17 | 0 | 28 | 16 | 1.0 | 0.378 | 1.0 | 0.541 |
| Parser propio v3 | 32 | 0 | 13 | 16 | 1.0 | 0.711 | 1.0 | 0.787 |
| spaCy + regla de concordancia (es_core_news_sm) | 44 | 7 | 1 | 9 | 0.863 | 0.978 | 0.562 | 0.869 |

## 2. Por nivel de complejidad

**Nivel 1** (20 oraciones)

| Sistema | TP | FP | FN | TN | Precisión | Cobertura | Rechazo correcto | Exactitud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Parser propio v1 | 12 | 8 | 0 | 0 | 0.6 | 1.0 | 0.0 | 0.6 |
| Parser propio v2 | 12 | 0 | 0 | 8 | 1.0 | 1.0 | 1.0 | 1.0 |
| Parser propio v3 | 12 | 0 | 0 | 8 | 1.0 | 1.0 | 1.0 | 1.0 |
| spaCy + concordancia | 12 | 3 | 0 | 5 | 0.8 | 1.0 | 0.625 | 0.85 |

**Nivel 2** (18 oraciones)

| Sistema | TP | FP | FN | TN | Precisión | Cobertura | Rechazo correcto | Exactitud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Parser propio v1 | 5 | 3 | 8 | 2 | 0.625 | 0.385 | 0.4 | 0.389 |
| Parser propio v2 | 5 | 0 | 8 | 5 | 1.0 | 0.385 | 1.0 | 0.556 |
| Parser propio v3 | 13 | 0 | 0 | 5 | 1.0 | 1.0 | 1.0 | 1.0 |
| spaCy + concordancia | 13 | 1 | 0 | 4 | 0.929 | 1.0 | 0.8 | 0.944 |

**Nivel 3** (13 oraciones)

| Sistema | TP | FP | FN | TN | Precisión | Cobertura | Rechazo correcto | Exactitud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Parser propio v1 | 0 | 0 | 10 | 3 |  | 0.0 | 1.0 | 0.231 |
| Parser propio v2 | 0 | 0 | 10 | 3 |  | 0.0 | 1.0 | 0.231 |
| Parser propio v3 | 7 | 0 | 3 | 3 | 1.0 | 0.7 | 1.0 | 0.769 |
| spaCy + concordancia | 10 | 3 | 0 | 0 | 0.769 | 1.0 | 0.0 | 0.769 |

**Extra fuera de alcance** (10 oraciones)

| Sistema | TP | FP | FN | TN | Precisión | Cobertura | Rechazo correcto | Exactitud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Parser propio v1 | 0 | 0 | 10 | 0 |  | 0.0 |  | 0.0 |
| Parser propio v2 | 0 | 0 | 10 | 0 |  | 0.0 |  | 0.0 |
| Parser propio v3 | 0 | 0 | 10 | 0 |  | 0.0 |  | 0.0 |
| spaCy + concordancia | 9 | 0 | 1 | 0 | 1.0 | 0.9 |  | 0.9 |

## 3. Errores del parser propio v3

**Falsos negativos** (gramaticales que rechaza): 13

| Oración | Motivo | Fenómeno |
| --- | --- | --- |
| el niño y la niña son alto y baja respectivamente | rechazada | fenomenos que exceden la gramatica (ver limitaciones L6) |
| el niño y la niña duermen | rechazada | fenomenos que exceden la gramatica (ver limitaciones L6) |
| el gato duerme y el perro ladra | rechazada | fenomenos que exceden la gramatica (ver limitaciones L6) |
| El gato come pescado. | fuera_de_lexico | vocabulario fuera del lexico |
| Los niños juegan en el parque. | fuera_de_lexico | vocabulario fuera del lexico |
| Yo quiero que tú vengas. | fuera_de_lexico | primera/segunda persona y subjuntivo |
| María ve a su madre. | fuera_de_lexico | nombre propio, "a" personal, posesivo |
| No me gusta el café. | fuera_de_lexico | negacion y pronombre clitico |
| Ayer el perro persiguió al gato. | fuera_de_lexico | contraccion "al" (de + el) |
| La niña dijo que el gato duerme. | fuera_de_lexico | subordinada completiva |
| El libro que compró la niña es viejo. | rechazada | relativo de objeto con sujeto pospuesto, todo en el lexico |
| La casa de los niños es pequeña. | rechazada | oracion copulativa con adjetivo, todo en el lexico |
| Duerme el gato. | rechazada | orden verbo-sujeto, todo en el lexico |

**Falsos positivos** (agramaticales que acepta): 0

## 4. Ambigüedad: análisis por oración (v3)

spaCy devuelve siempre UN árbol por oración; la CFG enumera todos.

| Oración | Análisis v3 | Árboles spaCy |
| --- | --- | --- |
| el niño ve el telescopio en la casa | 2 | 1 |
| el hombre alto ve la mujer en el jardín | 2 | 1 |
| el gato que duerme en la casa ve el ratón | 2 | 1 |
| los niños que compraron unos libros viejos duermen | 2 | 1 |

## 5. Verificación cruzada con NLTK (misma gramática v3, EarleyChartParser)

Coinciden en el número de derivaciones en 61/61 oraciones.

Tiempo medio por oración: propio 0.13 ms, NLTK 1.21 ms.

## 6. spaCy (es_core_news_sm)

Produjo árbol para 61/61 oraciones (el parser propio v3 aceptó 32).

Tiempo medio por oración: 3.19 ms.
