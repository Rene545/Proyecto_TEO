"""
Inspección uno por uno de los falsos positivos de spaCy + regla de concordancia.

En `comparacion_nlp` quedaron 7 oraciones agramaticales que la regla no marca.
Tres se habían revisado a mano y las otras cuatro se presumían "del mismo tipo".
Este script las revisa todas y clasifica cada una comparando los rasgos que
spaCy asigna con los rasgos verdaderos del léxico del equipo:

  rasgo_vacio      spaCy no asigna el rasgo a una palabra que sí lo tiene,
                   así que la regla no tiene con qué comparar.
  rasgo_asimilado  spaCy asigna un valor distinto al real y justo el que
                   concuerda con la palabra vecina: "corrige" el rasgo en
                   silencio y la discordancia desaparece.
  regla_relativa   la discordancia está entre el antecedente y el verbo de la
                   relativa (relación acl); el sujeto es "que", que no tiene
                   número, y la regla no sigue la relación hasta el antecedente.

Uso (necesita spaCy, igual que comparacion_nlp.comparar):

    pip install spacy
    python -m spacy download es_core_news_sm
    python -m analisis_formal.inspeccionar_spacy
    python -m analisis_formal.inspeccionar_spacy --guardar   # escribe resultados/inspeccion_spacy.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

from comparacion_nlp.comparar import detectar_discordancias
from comparacion_nlp.oro import cargar
from fase1_extension_espanol.lexico import candidatos

SALIDA = Path(__file__).parent / 'resultados' / 'inspeccion_spacy.md'

# léxico del equipo -> notación de spaCy (Universal Dependencies)
UD = {
    'genero': ('Gender', {'m': 'Masc', 'f': 'Fem'}),
    'numero': ('Number', {'sg': 'Sing', 'pl': 'Plur'}),
}
NOMINALES = {'DET', 'SUST', 'ADJ', 'V_INTR', 'V_TRANS', 'COP'}
RELATIVOS = {'que'}


def rasgo_real(palabra: str, rasgo: str) -> str | None:
    """Valor del rasgo según el léxico del equipo, si es único (en notación UD)."""
    _, tabla = UD[rasgo]
    valores = {e.rasgo(rasgo) for e in candidatos(palabra) if e.categoria in NOMINALES}
    valores.discard(None)
    if len(valores) != 1:
        return None
    return tabla[valores.pop()]


def rasgo_spacy(tok, rasgo: str) -> str | None:
    valor = tok.morph.get(UD[rasgo][0])
    return valor[0] if valor else None


def clasificar(doc) -> tuple[str, list[str]]:
    """Devuelve (categoría, evidencia) para un falso positivo.

    Solo usa .text, .dep_, .head, .i, .children y .morph.get(), así que se
    puede probar con objetos simulados, igual que detectar_discordancias.
    """
    evidencia: list[str] = []

    # 1. ¿La discordancia está en una relativa?
    for tok in doc:
        if tok.dep_ == 'acl':
            sujetos = [h for h in tok.children if h.text.lower() in RELATIVOS]
            ant, verbo = tok.head, tok
            a, v = rasgo_real(ant.text, 'numero'), rasgo_real(verbo.text, 'numero')
            if sujetos and a and v and a != v:
                rel = sujetos[0]
                evidencia.append(
                    f'"{rel.text}" ({rel.dep_} de "{verbo.text}") no tiene número; '
                    f'la discordancia {ant.text}[{a}] ~ {verbo.text}[{v}] pasa por la relación acl, '
                    f'que la regla no revisa')
                return 'regla_relativa', evidencia

    # 2. ¿Rasgo vacío o asimilado en algún par que la regla sí revisa?
    categoria = None
    for tok in doc:
        if tok.i == tok.head.i or tok.dep_ not in ('det', 'amod', 'nsubj'):
            continue
        rasgos = ('numero',) if tok.dep_ == 'nsubj' else ('genero', 'numero')
        for r in rasgos:
            for palabra in (tok, tok.head):
                real, dado = rasgo_real(palabra.text, r), rasgo_spacy(palabra, r)
                if real is None:
                    continue
                if dado is None:
                    nota = f'"{palabra.text}": {UD[r][0]} real={real}, spaCy=(vacío)'
                    categoria = categoria or 'rasgo_vacio'
                elif dado != real:
                    nota = f'"{palabra.text}": {UD[r][0]} real={real}, spaCy={dado}'
                    categoria = 'rasgo_asimilado' if categoria in (None, 'rasgo_asimilado') else categoria
                else:
                    continue
                if nota not in evidencia:
                    evidencia.append(nota)
    return categoria or 'sin_clasificar', evidencia


def falsos_positivos(nlp) -> list[tuple[str, object]]:
    salida = []
    for caso in cargar():
        if caso.gramatical_real:
            continue
        doc = nlp(caso.oracion)
        if not detectar_discordancias(doc):
            salida.append((caso.oracion, doc))
    return salida


def tabla_tokens(doc) -> list[str]:
    filas = ['| Palabra | POS | Dependencia | Cabeza | Rasgos de spaCy |', '| --- | --- | --- | --- | --- |']
    for t in doc:
        filas.append(f'| {t.text} | {t.pos_} | {t.dep_} | {t.head.text} | {t.morph or "(vacío)"} |')
    return filas


def informe(nlp, modelo: str) -> str:
    import spacy
    fps = falsos_positivos(nlp)
    lineas = [
        '# Inspección de los falsos positivos de spaCy + regla',
        '',
        f'Generado por `python -m analisis_formal.inspeccionar_spacy --guardar` '
        f'(spaCy {spacy.__version__}, modelo {modelo} {nlp.meta.get("version", "")}).',
        '',
        '| Oración agramatical | Clasificación | Evidencia |',
        '| --- | --- | --- |',
    ]
    detalle = []
    conteo: dict[str, int] = {}
    for oracion, doc in fps:
        cat, ev = clasificar(doc)
        conteo[cat] = conteo.get(cat, 0) + 1
        lineas.append(f'| {oracion} | {cat} | {"; ".join(ev)} |')
        detalle += ['', f'### {oracion}', '', *tabla_tokens(doc)]
    lineas += ['', f'Total: {len(fps)} falsos positivos. ' +
               ', '.join(f'{k}: {v}' for k, v in sorted(conteo.items())) + '.', '', '## Detalle por oración']
    return '\n'.join(lineas + detalle) + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(description='Clasifica los falsos positivos de spaCy + regla.')
    parser.add_argument('--modelo', default='es_core_news_sm')
    parser.add_argument('--guardar', action='store_true', help=f'escribir {SALIDA.name}')
    args = parser.parse_args()
    try:
        import spacy
        nlp = spacy.load(args.modelo)
    except (ImportError, OSError):
        print('[aviso] spaCy o el modelo no están instalados:')
        print('  pip install spacy && python -m spacy download es_core_news_sm')
        return 1
    texto = informe(nlp, args.modelo)
    print(texto)
    if args.guardar:
        SALIDA.parent.mkdir(exist_ok=True)
        SALIDA.write_text(texto, encoding='utf-8')
        print(f'Escrito {SALIDA}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
