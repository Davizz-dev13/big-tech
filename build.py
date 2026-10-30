"""Genera «Big Tech: ¿rentable?»: descarga los datos, calcula, dibuja y escribe la web.

Uso:
    python build.py                       # descarga datos reales y genera _site/
    python build.py --salida docs         # otra carpeta de salida
    python build.py --cache crudo.pkl     # guarda/reutiliza la descarga (para retocar el diseño)
"""
from __future__ import annotations

import argparse
import json
import logging
import pickle
import shutil
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import plotly
from jinja2 import Environment, FileSystemLoader, select_autoescape

from bigtech import calculos as C
from bigtech import formato as F
from bigtech import fuentes as S
from bigtech import graficos as G
from bigtech import paises as PZ
from bigtech import universo as U

RAIZ = Path(__file__).resolve().parent
MADRID = ZoneInfo("Europe/Madrid")
MINIMO = 20   # con menos empresas con cuentas completas no se publica (se queda la versión anterior)

log = logging.getLogger("bigtech")

ETIQUETAS_FALTA = {
    "cuentas": "cuentas", "ingresos": "ingresos", "beneficio": "beneficio neto", "flujo_operativo": "flujo operativo",
    "capex": "capex", "fcf": "caja libre", "perfil": "sector y sede", "capitalizacion": "capitalización",
    "tipo_de_cambio": "tipo de cambio",
}


def _cambio_txt(ahora, antes, r):
    if r is None or ahora is None or antes is None:
        return "—"
    if antes < 0 and ahora < 0:
        return "más negativo" if ahora < antes else "menos negativo"
    if antes < 0 <= ahora:
        return "a positivo"
    if antes >= 0 > ahora:
        return "a negativo"
    if antes > 0 and ahora / antes >= 3:
        return "×" + F.num(ahora / antes, 1)
    return F.pct(r, 0, signo=True)


def fila(e, m) -> dict:
    pais_es, bandera = PZ.pais(e.pais)
    tc = e.tc_info or {}
    fuentes = []
    y = f"https://finance.yahoo.com/quote/{e.simbolo}"
    fuentes.append(("Cuentas trimestrales y anuales (Yahoo Finance)", f"{y}/financials/"))
    fuentes.append(("Flujo de caja y capex (Yahoo Finance)", f"{y}/cash-flow/"))
    if e.url_ranking:
        fuentes.append(("Capitalización (companiesmarketcap)", e.url_ranking))
    notas = []
    if e.moneda and e.moneda != "USD" and e.tipo_cambio:
        notas.append(f"Cuentas en {e.moneda}, pasadas a dólares a {F.num(e.tipo_cambio, 5 if e.tipo_cambio < 0.01 else 4)} $ "
                     f"por {e.moneda}: media de {tc.get('dias')} cierres diarios del {F.fecha(tc['desde'])} al "
                     f"{F.fecha(tc['hasta'])} (Yahoo Finance, {tc.get('par')}).")
    if "capex" in m["derivado"]:
        notas.append("Yahoo no da el capex de los últimos 12 meses: se calcula como flujo operativo − caja libre.")
    if e.simbolo != e.simbolo_ranking:
        notas.append(f"Cuentas de la cotización principal ({e.simbolo}); la capitalización, de {e.simbolo_ranking} en el ranking.")
    faltan = [ETIQUETAS_FALTA.get(f, f) for f in e.faltan if not (f == "capex" and "capex" in m["derivado"])]
    # Frase de la tendencia de la caja libre
    if m.get("fcf_modo") == "12m":
        tend = (f"Hace un año (12 m a {F.mes(m['fcf_antes_fecha'])}): {F.dinero(m['fcf_antes'])} → "
                f"{_cambio_txt(m['fcf'], m['fcf_antes'], m['fcf_cambio'])}")
        tend_corto = _cambio_txt(m["fcf"], m["fcf_antes"], m["fcf_cambio"])
        tend_et = "FCF vs hace 1 año"
    elif m.get("fcf_modo") == "ejercicio":
        tend = (f"Último ejercicio ({F.mes(m['fcf_ultimo_ej_fecha'])}): {F.dinero(m['fcf_ultimo_ej'])} frente a "
                f"{F.dinero(m['fcf_antes'])} el anterior → {_cambio_txt(m['fcf_ultimo_ej'], m['fcf_antes'], m['fcf_cambio'])}")
        tend_corto = _cambio_txt(m["fcf_ultimo_ej"], m["fcf_antes"], m["fcf_cambio"])
        tend_et = "FCF último ejercicio"
    else:
        tend, tend_corto, tend_et = "Sin datos de hace un año.", "—", "FCF vs hace 1 año"
    return {
        "ticker": e.ticker, "nombre": e.nombre, "grupo": e.grupo,
        "pais": pais_es, "bandera": bandera, "sector": PZ.sector(e.sector), "industria": PZ.industria(e.industria),
        "logo": f"logos/{e.ticker}.webp" if e.logo else None, "inicial": e.nombre[:1],
        "fecha": F.mes(e.fecha_cuentas) if e.fecha_cuentas else "—", "moneda": e.moneda,
        "rentable": m["rentable"],
        "t": {  # textos
            "cap": F.dinero(m["cap"]), "ingresos": F.dinero(m["ingresos"]), "beneficio": F.dinero(m["beneficio"]),
            "margen": F.pct(m["margen"], 1), "ocf": F.dinero(m["ocf"]), "capex": F.dinero(m["capex"]),
            "fcf": F.dinero(m["fcf"]), "capex_ocf": F.pct(m["capex_ocf"]), "capex_fcf": F.veces(m["capex_fcf"])
            if m["capex_fcf"] is not None else ("FCF < 0" if m["fcf"] is not None and m["fcf"] <= 0 else "—"),
            "per": F.per(m["per"]) if m["per"] is not None else ("pérdidas" if m["rentable"] is False else "—"),
            "tend": tend, "tend_corto": tend_corto, "tend_et": tend_et,
            "capex_cambio": _cambio_txt(m["capex"] if m.get("capex_modo") == "12m" else m.get("capex_ultimo_ej"),
                                        m.get("capex_antes"), m.get("capex_cambio")),
        },
        "v": {  # valores para ordenar
            "cap": m["cap"], "ingresos": m["ingresos"], "beneficio": m["beneficio"], "margen": m["margen"],
            "capex": m["capex"], "fcf": m["fcf"], "capex_ocf": m["capex_ocf"], "per": m["per"],
        },
        "barra_capex": min(m["capex_ocf"], 1.5) / 1.5 * 100 if m["capex_ocf"] is not None else None,
        "capex_ocf_raw": m["capex_ocf"],
        "fcf_neg": m["fcf"] is not None and m["fcf"] < 0,
        "barra_ing": None, "barra_ben": None,
        "mini": G.mini(m["hist"]),
        "fuentes": fuentes, "notas": notas, "faltan": faltan,
    }


def lab(d: dict) -> dict:
    def item(x, clave=None):
        if not x:
            return None
        return {"etiqueta": x.get("etiqueta"), "corta": x.get("corta") or x.get("etiqueta"), "valor": F.dinero(x["valor"]) if x.get("valor") is not None else "—",
                "neg": (x.get("valor") or 0) < 0, "fuente": x.get("fuente"), "url": x.get("url"),
                "fecha": F.fecha(x["fecha"]) if x.get("fecha") else "", "calculado": x.get("calculado", False),
                "texto": x.get("texto")}
    r = d.get("resultado_anual") or {}
    return {
        "id": d["id"], "nombre": d["nombre"], "estado": d.get("estado", ""), "nota": d.get("nota", ""),
        "rentable": None if r.get("valor") is None else r["valor"] > 0, "periodo": r.get("periodo", ""),
        "principales": [item(d.get(k)) for k in ("ingresos_anual", "gasto_anual", "resultado_anual", "ingresos_run_rate", "valoracion")
                        if d.get(k) and not d[k].get("calculado")],
        "otros": [item(o) for o in d.get("otros", []) if not o.get("calculado")], "verificacion": d.get("verificacion", ""),
    }


def construir(empresas, salida: Path, meta: dict) -> dict:
    con_cuentas = [e for e in empresas if e.ttm.get("beneficio") is not None and e.tipo_cambio]
    if len(con_cuentas) < MINIMO:
        raise SystemExit(f"Sólo {len(con_cuentas)} empresas con cuentas (mínimo {MINIMO}); no se publica.")
    metr = {e.ticker: C.metricas(e) for e in empresas}
    filas = [fila(e, metr[e.ticker]) for e in empresas]
    por_grupo = {g: [f for f in filas if f["grupo"] == g] for g, _, _ in U.GRUPOS}
    ag = {g: C.agregado([metr[e.ticker] for e in empresas if e.grupo == g]) for g, _, _ in U.GRUPOS}
    m7 = ag["mag7"]
    serie = C.serie_grupo([(e, metr[e.ticker]) for e in empresas if e.grupo == "mag7"])

    # Barras ingresos vs beneficio, en escala común dentro de cada grupo
    for g, fs in por_grupo.items():
        tope = max((f["v"]["ingresos"] or 0) for f in fs) or 1
        for f in fs:
            if f["v"]["ingresos"]:
                f["barra_ing"] = f["v"]["ingresos"] / tope * 100
                f["barra_ben"] = abs(f["v"]["beneficio"] or 0) / tope * 100

    # ── El titular: se decide con los datos ──
    nombres = {e.ticker: e.nombre for e in empresas}
    m7_tk = [e.ticker for e in empresas if e.grupo == "mag7"]
    queman = [nombres[t] for t in m7_tk if metr[t]["fcf"] is not None and metr[t]["fcf"] < 0]
    aprieta = [nombres[t] for t in m7_tk if metr[t]["capex_ocf"] is not None and 0.75 <= metr[t]["capex_ocf"] < 1]
    if m7["fcf"] and m7["fcf"] > 0 and m7["rentables"] == m7["n"]:
        respuesta, clase = "De momento, sí", "si"
    elif m7["fcf"] and m7["fcf"] > 0:
        respuesta, clase = "A medias", "medias"
    else:
        respuesta, clase = "No", "no"

    def lista(xs):
        return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " y " + xs[-1]
    avisos = []
    if queman:
        avisos.append(f"{lista(queman)} ya {'gasta' if len(queman) == 1 else 'gastan'} más en capex de lo que "
                      f"{'genera' if len(queman) == 1 else 'generan'} su negocio: caja libre negativa.")
    if aprieta:
        avisos.append(f"{lista(aprieta)} {'dedica' if len(aprieta) == 1 else 'dedican'} más del 75 % de su caja operativa al capex.")
    if serie["años"]:
        x = m7["capex"] / serie["capex"][0]
        avisos.append(f"Su capex de los últimos 12 meses es {F.num(x, 1)} veces el de {serie['años'][0]}; "
                      f"la caja libre, en cambio, es {F.pct(m7['fcf'] / serie['fcf'][0] - 1, 0, signo=True)} frente a entonces.")
    ahora = datetime.now(timezone.utc)
    am = ahora.astimezone(MADRID)
    fechas = sorted(e.fecha_cuentas for e in empresas if e.fecha_cuentas)
    labs_json = json.loads((RAIZ / "datos" / "labs_ia.json").read_text(encoding="utf-8"))
    labs = [lab(d) for d in labs_json["labs"]]

    sectores = sorted({f["sector"] for f in filas})
    paises = sorted({f["pais"] for f in filas})
    figs = {
        "evolucion": json.loads(G.evolucion(serie, m7, "Últ. 12 m").to_json()),
        "capex_caja": json.loads(G.capex_sobre_caja([{"nombre": e.nombre, **metr[e.ticker]} for e in empresas]).to_json()),
    }
    faltas = [(f["nombre"], f["faltan"]) for f in filas if f["faltan"]]
    for nombre, fs in faltas:
        log.warning("Faltan datos de %s: %s", nombre, ", ".join(fs))

    contexto = dict(
        version=int(ahora.timestamp()),
        sello=f"Datos a {F.fecha(am)}, {am:%H:%M} (hora de Madrid) · cuentas de los últimos 12 meses publicados "
              f"(último trimestre entre {F.mes(fechas[0])} y {F.mes(fechas[-1])})",
        respuesta=respuesta, clase=clase, avisos=avisos,
        m7={k: (F.dinero(v) if k in ("cap", "ingresos", "beneficio", "ocf", "capex", "fcf") else v) for k, v in m7.items()},
        m7_capex_ocf=F.pct(m7["capex_ocf"]), m7_capex_fcf=F.veces(m7["capex_fcf"]), m7_margen=F.pct(m7["margen"], 1),
        capex_por_segundo=m7["capex_por_segundo"], capex_seg_txt=F.num(m7["capex_por_segundo"], 0),
        otras=ag["otras"], otras_t={k: F.dinero(ag["otras"][k]) for k in ("capex", "fcf", "beneficio", "ingresos")},
        grupos=[(g, nombre, por_grupo[g]) for g, nombre, _ in U.GRUPOS],
        labs=labs, labs_actualizado=F.fecha(labs_json["actualizado"]), labs_metodo=labs_json.get("metodo", ""),
        sectores=sectores, paises=paises, figs=json.dumps(figs, separators=(",", ":")),
        plotly_js=f"https://cdn.plot.ly/plotly-{plotly.offline.get_plotlyjs_version()}.min.js",
        origen_ranking=meta.get("ranking", ""), faltas=faltas, n=len(empresas),
        tcs=sorted({(e.moneda, F.num(e.tipo_cambio, 5 if e.tipo_cambio < 0.01 else 4), e.tc_info.get("dias"),
                     F.fecha(e.tc_info["desde"]), F.fecha(e.tc_info["hasta"]))
                    for e in empresas if e.moneda and e.moneda != "USD" and e.tc_info}),
        años_serie=serie["años"],
    )

    salida.mkdir(parents=True, exist_ok=True)
    (salida / "logos").mkdir(exist_ok=True)
    for e in empresas:
        if e.logo:
            (salida / "logos" / f"{e.ticker}.webp").write_bytes(e.logo)
    for f in (RAIZ / "estatico").iterdir():
        shutil.copy(f, salida / f.name)
    env = Environment(loader=FileSystemLoader(RAIZ / "plantillas"), autoescape=select_autoescape(["html"]))
    (salida / "index.html").write_text(env.get_template("index.html").render(**contexto), encoding="utf-8")
    (salida / ".nojekyll").write_text("")
    datos = {
        "generado": ahora.isoformat(timespec="seconds"), "ranking": meta.get("ranking"),
        "empresas": [{"ticker": e.ticker, "nombre": e.nombre, "grupo": e.grupo, "simbolo_yahoo": e.simbolo,
                      "pais": e.pais, "sector": e.sector, "industria": e.industria, "moneda_cuentas": e.moneda,
                      "fecha_cuentas": e.fecha_cuentas, "usd_por_unidad": e.tipo_cambio, "faltan": e.faltan,
                      **{k: v for k, v in metr[e.ticker].items() if k not in ("hist",)}} for e in empresas],
        "agregados": ag, "serie_mag7": serie, "labs": labs_json,
    }
    (salida / "datos.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    return datos


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--salida", default="_site")
    p.add_argument("--cache")
    a = p.parse_args()
    if a.cache and Path(a.cache).exists():
        empresas, meta = pickle.loads(Path(a.cache).read_bytes())
    else:
        empresas, meta = S.descargar(U.GRUPOS, respaldo=RAIZ / "datos" / "ranking_respaldo.csv")
        if a.cache:
            Path(a.cache).write_bytes(pickle.dumps((empresas, meta)))
    d = construir(empresas, Path(a.salida), meta)
    log.info("Hecho: %d empresas, %d rentables", len(d["empresas"]), sum(1 for e in d["empresas"] if e["rentable"]))


if __name__ == "__main__":
    main()
