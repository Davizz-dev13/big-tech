"""Gráficos: dos figuras de Plotly (diseñadas en Python) y minigráficos SVG por empresa."""
from __future__ import annotations

import plotly.graph_objects as go

from . import formato as F

TINTA = "#111111"
GRIS = "#8a8a8a"
VERDE = "#1f7a3a"
ROJO = "#b3261e"
CAPEX = "#2b2b2b"
FUENTE = "Latin Modern Roman, Computer Modern Serif, CMU Serif, Georgia, serif"


def _base(fig: go.Figure, alto: int) -> go.Figure:
    fig.update_layout(
        height=alto, margin=dict(l=8, r=8, t=8, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FUENTE, size=13, color=TINTA), separators=",.", hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, font=dict(size=13)),
        hoverlabel=dict(bgcolor="white", bordercolor=TINTA, font=dict(family=FUENTE, size=13)),
    )
    return fig


def evolucion(serie: dict, ttm: dict, etiqueta_ttm: str) -> go.Figure:
    """Capex, FCF y beneficio de las 7 por año fiscal, más los últimos 12 meses."""
    xs = [str(a) for a in serie["años"]] + [etiqueta_ttm]
    fig = go.Figure()
    for clave, nombre, color in (("capex", "Capex", CAPEX), ("fcf", "Caja libre (FCF)", VERDE),
                                 ("beneficio", "Beneficio neto", "#9bb7a4")):
        ys = [v / 1e9 for v in serie[clave]] + [ttm[clave] / 1e9]
        fig.add_bar(x=xs, y=ys, name=nombre, marker_color=color, marker_line_width=0,
                    text=[F.num(y, 0) for y in ys], textposition="outside", textfont=dict(size=11),
                    cliponaxis=False,
                    hovertemplate=f"<b>{nombre}</b> · %{{x}}<br>%{{customdata}}<extra></extra>",
                    customdata=[F.dinero(y * 1e9) for y in ys])
    fig.update_layout(barmode="group", bargap=0.22, bargroupgap=0.06)
    fig.update_yaxes(title_text="miles de millones de $", gridcolor="#e6e6e6", zeroline=True, zerolinecolor=TINTA,
                     tickformat=",.0f", title_font=dict(size=12))
    fig.update_xaxes(showline=True, linecolor=TINTA)
    return _base(fig, 380)


def capex_sobre_caja(filas: list[dict]) -> go.Figure:
    """Capex como % del flujo de caja operativo, de mayor a menor."""
    filas = sorted([f for f in filas if f["capex_ocf"] is not None], key=lambda f: f["capex_ocf"])
    xs = [f["capex_ocf"] * 100 for f in filas]
    colores = [ROJO if x >= 100 else (CAPEX if x >= 50 else GRIS) for x in xs]
    fig = go.Figure(go.Bar(
        x=xs, y=[f["nombre"] for f in filas], orientation="h", marker_color=colores, marker_line_width=0,
        text=[F.pct(x / 100) for x in xs], textposition="outside", cliponaxis=False, textfont=dict(size=12),
        customdata=[[F.dinero(f["capex"]), F.dinero(f["ocf"])] for f in filas],
        hovertemplate="<b>%{y}</b><br>Capex: %{customdata[0]}<br>Caja operativa: %{customdata[1]}<extra></extra>"))
    fig.add_vline(x=100, line=dict(color=ROJO, width=1, dash="dot"))
    fig.update_xaxes(ticksuffix=" %", gridcolor="#e6e6e6", range=[0, max(xs + [100]) * 1.18])
    fig.update_yaxes(automargin=True)
    fig.update_layout(bargap=0.28, showlegend=False)
    return _base(fig, 26 * len(filas) + 60)


def mini(hist: list[dict]) -> str:
    """SVG pequeño: capex (barra oscura) y FCF (verde o rojo) por ejercicio y últimos 12 meses."""
    if not hist:
        return ""
    vals = [abs(h.get(k) or 0) for h in hist for k in ("capex", "fcf")]
    top = max(vals) or 1
    neg = max([-(h.get("fcf") or 0) for h in hist] + [0])
    alto, base_y = 64, 64 * (top / (top + neg)) if neg else 64
    escala = (alto - 14) / (top + neg)
    base_y = 4 + top * escala
    ancho_g = 30
    w = len(hist) * ancho_g
    partes = [f'<svg viewBox="0 0 {w} {alto + 14}" class="bt-mini" role="img" aria-label="Capex y caja libre por año">']
    for i, h in enumerate(hist):
        x = i * ancho_g + 4
        c = h.get("capex")
        if c is not None:
            hc = c * escala
            partes.append(f'<rect x="{x}" y="{base_y - hc:.1f}" width="10" height="{max(hc, 0.6):.1f}" fill="{CAPEX}"/>')
        f = h.get("fcf")
        if f is not None:
            hf = abs(f) * escala
            y = base_y - hf if f >= 0 else base_y
            partes.append(f'<rect x="{x + 11}" y="{y:.1f}" width="10" height="{max(hf, 0.6):.1f}" fill="{VERDE if f >= 0 else ROJO}"/>')
        et = "12 m" if h.get("ttm") else ("’" + h["f"][2:4])
        partes.append(f'<text x="{x + 10.5}" y="{alto + 11}" text-anchor="middle">{et}</text>')
    partes.append(f'<line x1="0" x2="{w}" y1="{base_y:.1f}" y2="{base_y:.1f}" stroke="{TINTA}" stroke-width="0.6"/>')
    partes.append("</svg>")
    return "".join(partes)
