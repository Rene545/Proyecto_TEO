"""Comparacion del parser propio con NLTK y spaCy sobre las MISMAS oraciones.

  python -m comparacion_nlp.comparar                    # todo lo que este instalado
  python -m comparacion_nlp.comparar --sin-spacy        # solo parser propio (+ NLTK)
  python -m comparacion_nlp.comparar --modelo es_core_news_md

Dependencias opcionales (el parser propio no necesita ninguna):
  pip install nltk spacy
  python -m spacy download es_core_news_sm

Que se compara y por que:
  * Parser propio v1/v2/v3: acepta o rechaza. Se mide contra 'gramatical_real'.
  * NLTK: se le pasa LA MISMA gramatica v3 (EarleyChartParser). No es "otro
    analizador del espanol": es una verificacion cruzada de que nuestro
    analizador cuenta las mismas derivaciones que uno estandar.
  * spaCy: modelo estadistico. NO rechaza oraciones: siempre devuelve un arbol.
    Para poder compararlo se le aplica una regla de concordancia sobre sus rasgos
    morfologicos (genero/numero de det, adj y verbo respecto de su nucleo); si hay
    discrepancia se cuenta como "oracion marcada". Es una heuristica nuestra, no
    una funcion de spaCy, y el informe debe decirlo asi.
"""
from __future__ import annotations

import argparse
import csv
import time
from dataclasses import dataclass, field
from pathlib import Path

from fase1_extension_espanol.analizador import Analizador, ErrorLexicoEspanol
from fase1_extension_espanol.gramatica import VERSIONES, Gramatica, es_categoria_lexica, partes
from fase1_extension_espanol.lexico import candidatos, tokenizar
from comparacion_nlp.oro import CasoEs, cargar


# ------------------------------------------------------------------ metricas
def metricas(pred: list[bool], real: list[bool]) -> dict[str, float | int | None]:
    """Positivo = 'la oracion es aceptable'. pred/real son listas paralelas."""
    tp = sum(p and r for p, r in zip(pred, real))
    fp = sum(p and not r for p, r in zip(pred, real))
    fn = sum(not p and r for p, r in zip(pred, real))
    tn = sum(not p and not r for p, r in zip(pred, real))
    div = lambda a, b: round(a / b, 3) if b else None
    return {'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn,
            'precision': div(tp, tp + fp),
            'cobertura': div(tp, tp + fn),
            'rechazo_correcto': div(tn, tn + fp),
            'exactitud': div(tp + tn, len(real))}


# ------------------------------------------------------------- parser propio
@dataclass
class FilaPropia:
    estado: str            # aceptada | rechazada | fuera_de_lexico
    derivaciones: int
    ms: float

    @property
    def acepta(self) -> bool:
        return self.estado == 'aceptada'


def evaluar_propio(version: str, casos: list[CasoEs]) -> list[FilaPropia]:
    analizador = Analizador(VERSIONES[version]())
    filas = []
    for caso in casos:
        t0 = time.perf_counter()
        try:
            n = analizador.contar(caso.oracion)
            estado = 'aceptada' if n else 'rechazada'
        except ErrorLexicoEspanol:
            n, estado = 0, 'fuera_de_lexico'
        filas.append(FilaPropia(estado, n, (time.perf_counter() - t0) * 1000))
    return filas


# --------------------------------------------------------------------- NLTK
def exportar_cfg(gram: Gramatica, palabras: list[str]):
    """Gramatica v3 + producciones lexicas SOLO para las palabras de la oracion.

    Devuelve (simbolo_inicial, [(lhs, rhs_tuple, rhs_son_terminales)]). Es
    Python puro para poder probarlo sin NLTK; ver a_nltk() para el ultimo paso.
    """
    prods = [(p.izquierda, tuple(p.derecha), False) for p in gram.producciones]
    lexicos = {s for p in gram.producciones for s in p.derecha if es_categoria_lexica(s)}
    for simbolo_ in sorted(lexicos):
        categoria, rasgos = partes(simbolo_)
        for palabra in dict.fromkeys(palabras):
            if candidatos(palabra, categoria, rasgos):
                prods.append((simbolo_, (palabra,), True))
    return gram.inicial, prods


def a_nltk(inicial: str, prods):
    from nltk import CFG, Nonterminal, Production  # import tardio: opcional
    producciones = [
        Production(Nonterminal(lhs), list(rhs) if terminal else [Nonterminal(x) for x in rhs])
        for lhs, rhs, terminal in prods
    ]
    return CFG(Nonterminal(inicial), producciones)


def evaluar_nltk(casos: list[CasoEs], version: str = 'v3'):
    from nltk.parse import EarleyChartParser
    gram = VERSIONES[version]()
    filas = []
    for caso in casos:
        palabras = tokenizar(caso.oracion)
        t0 = time.perf_counter()
        if not all(candidatos(p) for p in palabras):
            filas.append(FilaPropia('fuera_de_lexico', 0, 0.0))
            continue
        inicial, prods = exportar_cfg(gram, palabras)
        try:
            n = sum(1 for _ in EarleyChartParser(a_nltk(inicial, prods)).parse(palabras))
        except ValueError:        # NLTK avisa asi cuando la gramatica no cubre alguna palabra
            n = 0
        filas.append(FilaPropia('aceptada' if n else 'rechazada', n, (time.perf_counter() - t0) * 1000))
    return filas


# -------------------------------------------------------------------- spaCy
def _rasgo(tok, nombre: str) -> str | None:
    valor = tok.morph.get(nombre)
    return valor[0] if valor else None


def detectar_discordancias(doc) -> list[str]:
    """Regla de concordancia aplicada a la salida de spaCy (ver docstring del modulo).

    Solo usa .dep_, .head, .i, .text y .morph.get(), asi que se prueba con objetos falsos.
    """
    hallazgos = []
    for tok in doc:
        cab = tok.head
        if cab.i == tok.i:
            continue
        if tok.dep_ in ('det', 'amod'):
            for rasgo in ('Gender', 'Number'):
                a, b = _rasgo(tok, rasgo), _rasgo(cab, rasgo)
                if a and b and a != b:
                    hallazgos.append(f'{tok.text}~{cab.text}: {rasgo} {a}/{b}')
        elif tok.dep_ in ('nsubj', 'csubj'):
            a, b = _rasgo(tok, 'Number'), _rasgo(cab, 'Number')
            if a and b and a != b:
                hallazgos.append(f'{tok.text}~{cab.text}: Number {a}/{b}')
    return hallazgos


def _arbol(tok) -> str:
    hijos = ' '.join(_arbol(h) for h in tok.children)
    return f'({tok.dep_}:{tok.text}{" " + hijos if hijos else ""})'


@dataclass
class FilaSpacy:
    parsea: bool
    marcada: bool          # la heuristica de concordancia encontro discrepancia
    hallazgos: list[str]
    ms: float
    arbol: str
    etiquetas: str = ''

    @property
    def acepta(self) -> bool:
        return not self.marcada


def evaluar_spacy(casos: list[CasoEs], modelo: str):
    import spacy
    nlp = spacy.load(modelo)
    filas = []
    for caso in casos:
        t0 = time.perf_counter()
        doc = nlp(caso.oracion)
        ms = (time.perf_counter() - t0) * 1000
        h = detectar_discordancias(doc)
        raiz = next((t for t in doc if t.dep_ == 'ROOT'), None)
        filas.append(FilaSpacy(raiz is not None, bool(h), h, ms, _arbol(raiz) if raiz is not None else '',
                               ' '.join(f'{t.text}/{t.pos_}' for t in doc)))
    return filas


# ------------------------------------------------------------------- informe
def _tabla_md(filas: list[list], cabecera: list[str]) -> str:
    out = ['| ' + ' | '.join(cabecera) + ' |', '|' + '|'.join(' --- ' for _ in cabecera) + '|']
    out += ['| ' + ' | '.join('' if c is None else str(c) for c in f) + ' |' for f in filas]
    return '\n'.join(out)


def _fila_metricas(nombre, pred, real):
    m = metricas(pred, real)
    return [nombre, m['TP'], m['FP'], m['FN'], m['TN'], m['precision'], m['cobertura'],
            m['rechazo_correcto'], m['exactitud']]


CAB_METRICAS = ['Sistema', 'TP', 'FP', 'FN', 'TN', 'Precisión', 'Cobertura', 'Rechazo correcto', 'Exactitud']


def generar_md(casos, propios, nltk_f, spacy_f, modelo) -> str:
    real = [c.gramatical_real for c in casos]
    sel = lambda niveles: [i for i, c in enumerate(casos) if c.nivel in niveles]
    partes_md = ['# Resultados de la comparación (generado por `comparacion_nlp.comparar`)\n',
                 f'Oraciones: {len(casos)} ({sum(c.origen == "equipo" for c in casos)} del equipo + '
                 f'{sum(c.origen == "extra" for c in casos)} extra fuera de alcance). '
                 'Positivo = "la oración es gramatical/aceptable".\n']

    filas = [_fila_metricas(f'Parser propio {v}', [f.acepta for f in fs], real) for v, fs in propios.items()]
    if spacy_f:
        filas.append(_fila_metricas(f'spaCy + regla de concordancia ({modelo})', [f.acepta for f in spacy_f], real))
    partes_md += ['## 1. Todas las oraciones\n', _tabla_md(filas, CAB_METRICAS), '']

    partes_md.append('## 2. Por nivel de complejidad\n')
    for nombre, niv in (('Nivel 1', '1'), ('Nivel 2', '2'), ('Nivel 3', '3'), ('Extra fuera de alcance', 'X')):
        idx = sel(niv)
        r = [real[i] for i in idx]
        filas = [_fila_metricas(f'Parser propio {v}', [fs[i].acepta for i in idx], r)
                 for v, fs in propios.items()]
        if spacy_f:
            filas.append(_fila_metricas('spaCy + concordancia', [spacy_f[i].acepta for i in idx], r))
        partes_md += [f'**{nombre}** ({len(idx)} oraciones)\n', _tabla_md(filas, CAB_METRICAS), '']

    v3 = propios['v3']
    fn = [(c, f) for c, f in zip(casos, v3) if c.gramatical_real and not f.acepta]
    fp = [(c, f) for c, f in zip(casos, v3) if not c.gramatical_real and f.acepta]
    partes_md += ['## 3. Errores del parser propio v3\n',
                  f'**Falsos negativos** (gramaticales que rechaza): {len(fn)}\n',
                  _tabla_md([[c.oracion, f.estado, c.fenomeno] for c, f in fn], ['Oración', 'Motivo', 'Fenómeno']), '',
                  f'**Falsos positivos** (agramaticales que acepta): {len(fp)}\n']
    if fp:
        partes_md += [_tabla_md([[c.oracion, f.derivaciones] for c, f in fp], ['Oración', 'Derivaciones']), '']

    amb = [(c, f) for c, f in zip(casos, v3) if f.derivaciones > 1]
    partes_md += ['## 4. Ambigüedad: análisis por oración (v3)\n',
                  'spaCy devuelve siempre UN árbol por oración; la CFG enumera todos.\n',
                  _tabla_md([[c.oracion, f.derivaciones, 1 if spacy_f else 'n/d'] for c, f in amb],
                            ['Oración', 'Análisis v3', 'Árboles spaCy']), '']

    if nltk_f:
        igual = sum(a.derivaciones == b.derivaciones for a, b in zip(v3, nltk_f))
        dif = [(c, a, b) for c, a, b in zip(casos, v3, nltk_f) if a.derivaciones != b.derivaciones]
        partes_md += ['## 5. Verificación cruzada con NLTK (misma gramática v3, EarleyChartParser)\n',
                      f'Coinciden en el número de derivaciones en {igual}/{len(casos)} oraciones.\n']
        if dif:
            partes_md += [_tabla_md([[c.oracion, a.derivaciones, b.derivaciones] for c, a, b in dif],
                                    ['Oración', 'Propio', 'NLTK']), '']
        partes_md.append(f'Tiempo medio por oración: propio {sum(f.ms for f in v3)/len(v3):.2f} ms, '
                         f'NLTK {sum(f.ms for f in nltk_f)/len(nltk_f):.2f} ms.\n')

    if spacy_f:
        analizadas = sum(f.parsea for f in spacy_f)
        partes_md += [f'## 6. spaCy ({modelo})\n',
                      f'Produjo árbol para {analizadas}/{len(casos)} oraciones '
                      f'(el parser propio v3 aceptó {sum(f.acepta for f in v3)}).\n',
                      f'Tiempo medio por oración: {sum(f.ms for f in spacy_f)/len(spacy_f):.2f} ms.\n']
    return '\n'.join(partes_md)


def guardar_csv(ruta: Path, casos, propios, nltk_f, spacy_f) -> None:
    with ruta.open('w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        cab = ['oracion', 'nivel', 'origen', 'en_lexico', 'esperado_v3', 'gramatical_real', 'fenomeno']
        for v in propios:
            cab += [f'{v}_estado', f'{v}_derivaciones']
        if nltk_f:
            cab += ['nltk_estado', 'nltk_derivaciones']
        if spacy_f:
            cab += ['spacy_parsea', 'spacy_marcada', 'spacy_hallazgos', 'spacy_arbol', 'spacy_etiquetas']
        w.writerow(cab)
        for i, c in enumerate(casos):
            fila = [c.oracion, c.nivel, c.origen, c.en_lexico, c.esperado_v3, c.gramatical_real, c.fenomeno]
            for fs in propios.values():
                fila += [fs[i].estado, fs[i].derivaciones]
            if nltk_f:
                fila += [nltk_f[i].estado, nltk_f[i].derivaciones]
            if spacy_f:
                s = spacy_f[i]
                fila += [s.parsea, s.marcada, '; '.join(s.hallazgos), s.arbol, s.etiquetas]
            w.writerow(fila)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--sin-spacy', action='store_true')
    ap.add_argument('--sin-nltk', action='store_true')
    ap.add_argument('--modelo', default='es_core_news_sm')
    ap.add_argument('--salida', default='comparacion_nlp/resultados')
    args = ap.parse_args()

    casos = cargar()
    propios = {v: evaluar_propio(v, casos) for v in ('v1', 'v2', 'v3')}
    nltk_f = spacy_f = None
    if not args.sin_nltk:
        try:
            nltk_f = evaluar_nltk(casos)
        except ImportError:
            print('[aviso] NLTK no esta instalado: pip install nltk')
    if not args.sin_spacy:
        try:
            spacy_f = evaluar_spacy(casos, args.modelo)
        except ImportError:
            print('[aviso] spaCy no esta instalado: pip install spacy')
        except OSError:
            print(f'[aviso] falta el modelo: python -m spacy download {args.modelo}')

    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    md = generar_md(casos, propios, nltk_f, spacy_f, args.modelo)
    (salida / 'resultados.md').write_text(md, encoding='utf-8')
    guardar_csv(salida / 'resultados.csv', casos, propios, nltk_f, spacy_f)
    if spacy_f:
        (salida / 'arboles_spacy.txt').write_text(
            '\n'.join(f'{c.oracion}\n  {s.arbol}\n  {s.etiquetas}\n' for c, s in zip(casos, spacy_f)), encoding='utf-8')
    print(md)
    print(f'\nArchivos escritos en {salida}/')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
