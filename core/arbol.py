"""Árbol genérico para representar análisis sintácticos (sin dependencias)."""
from __future__ import annotations
from dataclasses import dataclass, field
from html import escape
from pathlib import Path


@dataclass
class Nodo:
    etiqueta: str
    hijos: list["Nodo"] = field(default_factory=list)

    def texto(self, nivel: int = 0) -> str:
        """Representación legible en terminal."""
        lineas = ["  " * nivel + self.etiqueta]
        for hijo in self.hijos:
            lineas.append(hijo.texto(nivel + 1))
        return "\n".join(lineas)

    def guardar_dot(self, ruta: str | Path) -> None:
        """Guardar archivo DOT para Graphviz (Graphviz NO es obligatorio)."""
        lineas = ['digraph Arbol {', '  rankdir=TB;', '  node [shape=box, style=rounded];']
        contador = 0
        def visitar(nodo: Nodo, padre: int | None = None) -> None:
            nonlocal contador
            actual = contador
            contador += 1
            etiqueta = nodo.etiqueta.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
            lineas.append(f'  n{actual} [label="{etiqueta}"];')
            if padre is not None:
                lineas.append(f'  n{padre} -> n{actual};')
            for hijo in nodo.hijos:
                visitar(hijo, actual)
        visitar(self)
        lineas.append('}')
        destino = Path(ruta)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text("\n".join(lineas) + "\n", encoding="utf-8")

    def guardar_svg(self, ruta: str | Path) -> None:
        """Árbol vectorial visual: abrir el SVG en un navegador, sin instalar librerías."""
        separacion_x = 212
        separacion_y = 112
        posicion: dict[int, tuple[float, float]] = {}
        numero_hojas = 0
        max_nivel = 0
        nodos: list[Nodo] = []
        aristas: list[tuple[Nodo, Nodo]] = []

        def distribuir(nodo: Nodo, nivel: int) -> float:
            nonlocal numero_hojas, max_nivel
            max_nivel = max(max_nivel, nivel)
            nodos.append(nodo)
            for hijo in nodo.hijos:
                aristas.append((nodo, hijo))
            if nodo.hijos:
                valores_x = [distribuir(hijo, nivel + 1) for hijo in nodo.hijos]
                x = (valores_x[0] + valores_x[-1]) / 2
            else:
                x = 110 + numero_hojas * separacion_x
                numero_hojas += 1
            posicion[id(nodo)] = (x, 65 + nivel * separacion_y)
            return x

        distribuir(self, 0)
        ancho = max(235, numero_hojas * separacion_x + 20)
        alto = (max_nivel + 1) * separacion_y + 45
        partes = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" width="{ancho}" height="{alto}">',
            '<rect width="100%" height="100%" fill="#f8fafc"/>',
            '<g stroke="#64748b" stroke-width="2" fill="none">'
        ]
        for padre, hijo in aristas:
            x1, y1 = posicion[id(padre)]
            x2, y2 = posicion[id(hijo)]
            partes.append(f'<path d="M{x1:.1f} {y1+23:.1f} L{x2:.1f} {y2-23:.1f}"/>')
        partes.append('</g><g font-family="Segoe UI, Arial, sans-serif" font-size="13">')
        for nodo in nodos:
            x, y = posicion[id(nodo)]
            color = '#dbeafe' if nodo.hijos else '#dcfce7'
            borde = '#2563eb' if nodo.hijos else '#059669'
            partes.append(f'<rect x="{x-98:.1f}" y="{y-23:.1f}" width="196" height="46" rx="10" fill="{color}" stroke="{borde}" stroke-width="1.3"/>')
            etiqueta = escape(nodo.etiqueta)
            partes.append(f'<text x="{x:.1f}" y="{y+4:.1f}" text-anchor="middle" fill="#0f172a" textLength="{min(174, max(25, len(nodo.etiqueta)*7.2)):.0f}" lengthAdjust="spacingAndGlyphs">{etiqueta}</text>')
        partes.append('</g></svg>')
        destino = Path(ruta)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text("\n".join(partes) + "\n", encoding="utf-8")
