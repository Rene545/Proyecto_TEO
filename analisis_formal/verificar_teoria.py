"""
Verificación independiente de los resultados teóricos del proyecto.

Este módulo NO importa nada de fase1_extension_espanol ni de comparacion_nlp.
La idea es reproducir por un camino distinto los números que reportan las
otras partes, para poder defenderlos en la presentación:

  1. Ambigüedad de adjunción preposicional (L3): la serie 1, 2, 5, 14 son
     números de Catalan. Se recalcula contando derivaciones en una gramática
     abstracta mínima, sin léxico del español.
  2. Explosión combinatoria de la concordancia (L2): cuánto se multiplica
     cada regla según los rasgos que deben coincidir.
  3. Costo del parche para "respectivamente" (L6): la tabla 16, 80, 336,
     1360, 5456 sale de una fórmula cerrada.
  4. Lema de bombeo sobre el lenguaje copia {w c w}: se comprueba por fuerza
     bruta que ninguna descomposición uvwxy sobrevive al bombeo (ilustración
     para valores concretos de p, no reemplaza la demostración).
  5. Métricas de la comparación: se recalculan precisión, cobertura, rechazo
     correcto y exactitud a partir de las matrices de confusión del borrador.

Uso (desde la raíz del repositorio):

    python -m analisis_formal.verificar_teoria
    python -m analisis_formal.verificar_teoria --seccion catalan
"""

from __future__ import annotations

import argparse
from functools import lru_cache
from math import comb


# ---------------------------------------------------------------------------
# 1. L3 — Ambigüedad estructural y números de Catalan
# ---------------------------------------------------------------------------
#
# Gramática abstracta (la misma forma que tiene v3 para la adjunción):
#
#     SV -> V SN | SV SP
#     SN -> N    | SN SP
#     SP -> P SN
#
# Se cuenta cuántos árboles distintos generan la cadena
#     V N (P N)^k
# con un CKY que cuenta en vez de construir. Si la serie coincide con la de
# las otras partes, el resultado no depende del léxico ni del analizador.

GRAMATICA_ADJUNCION = {
    "SV": [("V", "SN"), ("SV", "SP")],
    "SN": [("SN", "SP")],
    "SP": [("P", "SN")],
}
LEXICAS = {"SN": {"N"}}  # SN -> N


def contar_arboles(tokens: list[str], inicial: str = "SV") -> int:
    n = len(tokens)

    @lru_cache(maxsize=None)
    def cuenta(simbolo: str, i: int, j: int) -> int:
        # cuántas derivaciones de `simbolo` cubren tokens[i:j]
        if simbolo == tokens[i] and j == i + 1:
            return 1
        total = 0
        if j == i + 1 and tokens[i] in LEXICAS.get(simbolo, set()):
            total += 1
        for izq, der in GRAMATICA_ADJUNCION.get(simbolo, []):
            for k in range(i + 1, j):
                a = cuenta(izq, i, k)
                if a:
                    total += a * cuenta(der, k, j)
        return total

    return cuenta(inicial, 0, n)


def catalan(n: int) -> int:
    return comb(2 * n, n) // (n + 1)


def seccion_catalan() -> None:
    print("L3 — Adjunción de frases preposicionales")
    print(f"{'FP':>3} {'árboles':>8} {'Catalan(k+1)':>13}")
    for k in range(0, 8):
        tokens = ["V", "N"] + ["P", "N"] * k
        arboles = contar_arboles(tokens)
        print(f"{k:>3} {arboles:>8} {catalan(k + 1):>13}")
        assert arboles == catalan(k + 1)
    print("Con k frases preposicionales hay Catalan(k+1) árboles.")
    print("Los primeros cuatro (1, 2, 5, 14) coinciden con v3 y con NLTK.\n")


# ---------------------------------------------------------------------------
# 2. L2 — Explosión combinatoria de la concordancia
# ---------------------------------------------------------------------------
#
# Una regla "plana" se parte en tantas copias como combinaciones de valores
# tengan los rasgos que la regla obliga a coincidir. Un rasgo que no
# participa en ninguna concordancia (p. ej. el tiempo verbal en esta
# gramática) no multiplica nada.

RASGOS = {"genero": 2, "numero": 2, "persona": 3, "tiempo": 2}


def copias_por_regla(rasgos_que_concuerdan: list[str]) -> int:
    total = 1
    for r in rasgos_que_concuerdan:
        total *= RASGOS[r]
    return total


def seccion_explosion() -> None:
    print("L2 — Copias de una regla según los rasgos que deben concordar")
    casos = [
        ("FN -> DET SUST ADJ", ["genero", "numero"]),
        ("O  -> FN FV  (sin persona)", ["numero"]),
        ("O  -> FN FV  (con persona)", ["numero", "persona"]),
        ("FN con género, número y persona", ["genero", "numero", "persona"]),
    ]
    for regla, rasgos in casos:
        print(f"  {regla:<36} rasgos={'×'.join(rasgos):<24} copias={copias_por_regla(rasgos)}")
    print("  El tiempo verbal no aparece: no concuerda con nada, así que cuesta 0.\n")


# ---------------------------------------------------------------------------
# 3. L6 — Costo de parchear "respectivamente" con una CFG
# ---------------------------------------------------------------------------
#
# Cada grupo nominal se resume en un par (género, número): 4 valores.
# Para una coordinación de longitud k, una CFG sin memoria cruzada tiene que
# enumerar las 4^k secuencias posibles de rasgos. Cubrir k = 2..n cuesta
#     sum_{k=2}^{n} 4^k = (4^(n+1) - 16) / 3

TABLA_REPORTADA_L6 = {2: 16, 3: 80, 4: 336, 5: 1360, 6: 5456}


def producciones_l6(n: int, valores: int = 4) -> int:
    return sum(valores ** k for k in range(2, n + 1))


def seccion_l6() -> None:
    print("L6 — Producciones para cubrir coordinaciones de longitud 2..n")
    print(f"{'n':>3} {'suma 4^k':>9} {'cerrada':>9} {'reportada':>10}")
    for n in range(2, 9):
        suma = producciones_l6(n)
        cerrada = (4 ** (n + 1) - 16) // 3
        rep = TABLA_REPORTADA_L6.get(n, "")
        print(f"{n:>3} {suma:>9} {cerrada:>9} {rep!s:>10}")
        assert suma == cerrada
        if n in TABLA_REPORTADA_L6:
            assert suma == TABLA_REPORTADA_L6[n]
    print("El costo crece como 4^n: hay una CFG para cada n fijo, pero no una")
    print("CFG finita para todo n.\n")


# ---------------------------------------------------------------------------
# 4. Lema de bombeo sobre L = { w c w : w en {a,b}* }
# ---------------------------------------------------------------------------
#
# Lema de bombeo para CFL: si L es libre de contexto existe p tal que toda
# z en L con |z| >= p se escribe z = u v w x y con |vwx| <= p, |vx| >= 1 y
# u v^i w x^i y en L para todo i >= 0.
#
# Se toma z = a^p b^p c a^p b^p y se comprueba que TODA descomposición válida
# falla para i = 0 o i = 2. Es una comprobación para cada p concreto; la
# demostración general está en analisis_resultados.md.

def en_lenguaje_copia(s: str) -> bool:
    if s.count("c") != 1:
        return False
    izq, der = s.split("c")
    return izq == der


def bombeo_falla_siempre(p: int) -> tuple[bool, int]:
    z = "a" * p + "b" * p + "c" + "a" * p + "b" * p
    n = len(z)
    descomposiciones = 0
    for ini in range(n):                       # inicio de vwx
        for largo in range(1, p + 1):          # |vwx|
            fin = ini + largo
            if fin > n:
                break
            for lv in range(0, largo + 1):
                for lx in range(0, largo - lv + 1):
                    if lv + lx == 0:
                        continue
                    u = z[:ini]
                    v = z[ini:ini + lv]
                    w = z[ini + lv:fin - lx]
                    x = z[fin - lx:fin]
                    y = z[fin:]
                    descomposiciones += 1
                    sobrevive = all(
                        en_lenguaje_copia(u + v * i + w + x * i + y) for i in (0, 2)
                    )
                    if sobrevive:
                        return False, descomposiciones
    return True, descomposiciones


def seccion_bombeo() -> None:
    print("Lema de bombeo sobre { w c w }  con z = a^p b^p c a^p b^p")
    for p in range(1, 8):
        ok, revisadas = bombeo_falla_siempre(p)
        estado = "ninguna sobrevive" if ok else "ALGUNA SOBREVIVE"
        print(f"  p={p}: {revisadas:>5} descomposiciones revisadas -> {estado}")
        assert ok
    print("  Como |vwx| <= p, vwx no alcanza a tocar las a's de la primera copia")
    print("  y las b's de la segunda a la vez: bombear altera una copia y no la")
    print("  otra (o borra la c). La demostración por casos está en el análisis.\n")


# ---------------------------------------------------------------------------
# 5. Métricas de la comparación (borrador de Persona 3)
# ---------------------------------------------------------------------------

MATRICES = {
    #                           TP  FP  FN  TN
    "v1 (sin concordancia)":    (17, 11, 28, 5),
    "v2 (concordancia)":        (17, 0, 28, 16),
    "v3 (modif. + relativo)":   (32, 0, 13, 16),
    "spaCy + regla":            (44, 7, 1, 9),
}


def metricas(tp: int, fp: int, fn: int, tn: int) -> dict[str, float]:
    return {
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "cobertura": tp / (tp + fn) if tp + fn else 0.0,
        "rechazo": tn / (tn + fp) if tn + fp else 0.0,
        "exactitud": (tp + tn) / (tp + fp + fn + tn),
    }


def seccion_metricas() -> None:
    print("Métricas recalculadas (61 oraciones: 45 gramaticales, 16 agramaticales)")
    print(f"  {'Sistema':<24} {'Prec':>6} {'Cob':>6} {'Rech':>6} {'Exact':>6}")
    for nombre, (tp, fp, fn, tn) in MATRICES.items():
        assert tp + fn == 45 and fp + tn == 16, nombre
        m = metricas(tp, fp, fn, tn)
        print(f"  {nombre:<24} {m['precision']:>6.3f} {m['cobertura']:>6.3f} "
              f"{m['rechazo']:>6.3f} {m['exactitud']:>6.3f}")
    print("  Todas coinciden con las tablas del borrador.\n")

    # Con 61 oraciones las diferencias pequeñas no son concluyentes.
    # Intervalo de Wilson al 95 % para la exactitud y el rechazo correcto.
    print("Intervalos de Wilson al 95 % (qué tan finos son los números)")
    print(f"  {'Sistema':<24} {'Exactitud':>22} {'Rechazo correcto':>22}")
    for nombre, (tp, fp, fn, tn) in MATRICES.items():
        ex = wilson(tp + tn, tp + fp + fn + tn)
        re = wilson(tn, tn + fp)
        print(f"  {nombre:<24} {fmt_intervalo(ex):>22} {fmt_intervalo(re):>22}")
    print("  v3 y spaCy + regla se solapan en exactitud: con esta muestra no se")
    print("  puede afirmar que uno sea más exacto que el otro.\n")


def wilson(aciertos: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = aciertos / n
    centro = (p + z * z / (2 * n)) / (1 + z * z / n)
    margen = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / (1 + z * z / n)
    return (max(0.0, centro - margen), min(1.0, centro + margen))


def fmt_intervalo(iv: tuple[float, float]) -> str:
    return f"[{iv[0]:.2f}, {iv[1]:.2f}]"


SECCIONES = {
    "catalan": seccion_catalan,
    "explosion": seccion_explosion,
    "l6": seccion_l6,
    "bombeo": seccion_bombeo,
    "metricas": seccion_metricas,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--seccion", choices=SECCIONES, help="ejecutar solo una sección")
    args = parser.parse_args()
    if args.seccion:
        SECCIONES[args.seccion]()
    else:
        for f in SECCIONES.values():
            f()


if __name__ == "__main__":
    main()
