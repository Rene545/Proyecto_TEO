# Investigación y análisis formal

Todo se ejecuta **desde la raíz del repositorio** (igual que el resto del proyecto).

Esta carpeta conecta los resultados de las partes de implementación con la
teoría de lenguajes formales: ubica cada punto de falla en la jerarquía de
Chomsky, da la demostración formal del único que sale del tipo 2 y revisa qué
dicen (y qué no dicen) los números de la comparación con NLP.

| Archivo | Para qué sirve |
| :--- | :--- |
| `marco_teorico.md` | Jerarquía de Chomsky, propiedades de las CFG, diferencias entre lenguaje formal y natural, historia del debate y referencias |
| `analisis_resultados.md` | L1–L6 en la jerarquía, serie de Catalan, demostración de L6 (clausura + lema de bombeo), métricas con intervalos de confianza y clasificación de los fallos de spaCy |
| `verificar_teoria.py` | Recalcula los números teóricos por un camino independiente (solo biblioteca estándar) |
| `inspeccionar_spacy.py` | Revisa uno por uno los 7 falsos positivos de spaCy + regla y los clasifica (necesita spaCy) |
| `resultados/` | Salidas ya generadas: `verificacion_teoria.txt` e `inspeccion_spacy.md` |

## Cómo correrlo

```bash
# verificación teórica, sin dependencias
python -m analisis_formal.verificar_teoria
python -m analisis_formal.verificar_teoria --seccion catalan    # o: explosion, l6, bombeo, metricas

# inspección de spaCy (mismas dependencias que comparacion_nlp)
pip install spacy
python -m spacy download es_core_news_sm
python -m analisis_formal.inspeccionar_spacy --guardar

# pruebas
python -m unittest tests.test_analisis_formal -v
```

## Qué se verificó

* **Ambigüedad (L3).** Una gramática abstracta de tres reglas, recursiva por la
  izquierda, da 1, 2, 5, 14, 42, 132, 429. El analizador del equipo (recursivo
  por la derecha) da exactamente lo mismo hasta k = 6: son los números de
  Catalan C(k + 1).
* **El muro (L6).** `muro_cfg.producciones_necesarias(n)` coincide con la
  fórmula cerrada (4ⁿ⁺¹ − 16)/3 para n = 2…8; el homomorfismo de la
  demostración, aplicado al léxico real, lleva las oraciones correctas a
  { w c w } y la cruzada no; y ninguna descomposición de aᵖbᵖcaᵖbᵖ sobrevive
  al bombeo para p = 1…7.
* **Métricas.** Las matrices de confusión que cita el informe salen de correr
  el parser sobre el gold; los intervalos de Wilson muestran qué diferencias
  son robustas con 61 oraciones.
* **spaCy.** De los 7 falsos positivos: 2 por rasgo vacío, 2 por rasgo
  asimilado (spaCy asigna el rasgo que concuerda) y 3 por límite de la regla en
  las relativas.
* Se volvió a correr `comparacion_nlp.comparar` completo con spaCy 3.8 y
  `es_core_news_sm` 3.8.0: las tablas salen idénticas, salvo los tiempos.

## Decisiones que conviene poder defender

1. **`verificar_teoria.py` no importa código del equipo.** Si importara el
   analizador, coincidir con él no probaría nada. Las pruebas son las que cruzan
   ambas implementaciones.
2. **La fuerza bruta del lema de bombeo no es la demostración.** Comprueba casos
   concretos de p; la demostración por casos está en `analisis_resultados.md`.
3. **La clasificación de spaCy usa el léxico del equipo como verdad.** Un rasgo
   se considera "asimilado" solo si el léxico le da a la palabra un valor único
   y spaCy le asigna otro.
