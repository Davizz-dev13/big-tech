"""Cálculos: todo a dólares, ratios de capex y caja, comparación con hace un año y agregados."""
from __future__ import annotations

from datetime import date

SEGUNDOS_AÑO = 365.25 * 86400


def _d(f: str) -> date:
    return date.fromisoformat(f)


def hace_un_año(hist: list, fecha: str, tolerancia: int = 45):
    """El punto de `hist` (fecha, valor) más cercano a un año antes de `fecha` (± `tolerancia` días)."""
    if not fecha:
        return None
    obj = _d(fecha).toordinal() - 365
    cands = [(abs(_d(f).toordinal() - obj), f, v) for f, v in hist if f < fecha]
    cands = [c for c in cands if c[0] <= tolerancia]
    if not cands:
        return None
    _, f, v = min(cands, key=lambda c: (c[0], c[1]))
    return f, v


def cambio(ahora, antes):
    if ahora is None or antes is None or antes == 0:
        return None
    return (ahora - antes) / abs(antes)


def metricas(e) -> dict:
    """Métricas en USD de una empresa (objeto con .ttm, .tipo_cambio, .anual, .trailing_hist, .cap)."""
    tc = e.tipo_cambio
    t = dict(e.ttm)
    derivado = []
    if "capex" not in t and {"flujo_operativo", "fcf"} <= t.keys():
        t["capex"] = t["fcf"] - t["flujo_operativo"]
        derivado.append("capex")
    usd = (lambda x: None if x is None or tc is None else x * tc)
    ingresos, beneficio = usd(t.get("ingresos")), usd(t.get("beneficio"))
    ocf, fcf = usd(t.get("flujo_operativo")), usd(t.get("fcf"))
    capex = usd(abs(t["capex"])) if t.get("capex") is not None else None
    m = {
        "cap": e.cap, "ingresos": ingresos, "beneficio": beneficio, "ocf": ocf, "capex": capex, "fcf": fcf,
        "margen": beneficio / ingresos if ingresos and beneficio is not None else None,
        "capex_ocf": capex / ocf if capex is not None and ocf and ocf > 0 else None,
        "capex_fcf": capex / fcf if capex is not None and fcf and fcf > 0 else None,
        "per": e.cap / beneficio if e.cap and beneficio and beneficio > 0 else None,
        # Lo que enseña la tarjeta: flujo de caja libre (FCF = flujo operativo − capex).
        "margen_fcf": fcf / ingresos if ingresos and fcf is not None else None,
        "p_fcf": e.cap / fcf if e.cap and fcf and fcf > 0 else None,   # FCF ≤ 0 → sin múltiplo (n. s.)
        "rentable": None if beneficio is None else beneficio > 0,
        "derivado": derivado,
    }
    # Hace un año: misma cifra de 12 meses (o el ejercicio anual) que acaba ~un año antes.
    for clave, dest in (("fcf", "fcf"), ("capex", "capex")):
        hist = sorted(set(e.trailing_hist.get(clave, []) + e.anual.get(clave, [])))
        p = hace_un_año(hist, e.fecha_cuentas)
        if p and t.get(clave) is not None:
            antes = abs(p[1]) if clave == "capex" else p[1]
            ahora = abs(t[clave]) if clave == "capex" else t[clave]
            m[dest + "_antes"] = usd(antes)
            m[dest + "_antes_fecha"] = p[0]
            m[dest + "_cambio"] = cambio(ahora, antes)   # en moneda local: el tipo de cambio no lo distorsiona
            m[dest + "_modo"] = "12m"
        else:
            # Sin una cifra de 12 meses de hace justo un año: último ejercicio anual frente al anterior.
            an = e.anual.get(clave, [])
            if len(an) >= 2:
                (f0, v0), (f1, v1) = an[-2], an[-1]
                if clave == "capex":
                    v0, v1 = abs(v0), abs(v1)
                m[dest + "_antes"], m[dest + "_antes_fecha"] = usd(v0), f0
                m[dest + "_ultimo_ej"], m[dest + "_ultimo_ej_fecha"] = usd(v1), f1
                m[dest + "_cambio"] = cambio(v1, v0)
                m[dest + "_modo"] = "ejercicio"
            else:
                m[dest + "_antes"] = m[dest + "_antes_fecha"] = m[dest + "_cambio"] = m[dest + "_modo"] = None
    # Historia anual para el minigráfico (al mismo tipo de cambio medio, para comparar formas).
    años = {}
    for f, v in e.anual.get("capex", []):
        años.setdefault(f, {})["capex"] = usd(abs(v))
    for f, v in e.anual.get("fcf", []):
        años.setdefault(f, {})["fcf"] = usd(v)
    hist = [{"f": f, **d} for f, d in sorted(años.items())][-4:]
    if e.fecha_cuentas and (not hist or hist[-1]["f"] != e.fecha_cuentas):
        hist.append({"f": e.fecha_cuentas, "capex": capex, "fcf": fcf, "ttm": True})
    elif hist:
        hist[-1]["ttm"] = True
    m["hist"] = hist
    return m


def agregado(ms: list[dict]) -> dict:
    def suma(k):
        vals = [m[k] for m in ms if m.get(k) is not None]
        return sum(vals) if vals else None
    a = {k: suma(k) for k in ("cap", "ingresos", "beneficio", "ocf", "capex", "fcf")}
    a["n"] = len(ms)
    a["rentables"] = sum(1 for m in ms if m.get("rentable"))
    a["fcf_negativo"] = sum(1 for m in ms if m.get("fcf") is not None and m["fcf"] < 0)
    a["capex_ocf"] = a["capex"] / a["ocf"] if a["capex"] and a["ocf"] else None
    a["capex_fcf"] = a["capex"] / a["fcf"] if a["capex"] and a["fcf"] and a["fcf"] > 0 else None
    a["margen"] = a["beneficio"] / a["ingresos"] if a["beneficio"] is not None and a["ingresos"] else None
    a["capex_por_segundo"] = a["capex"] / SEGUNDOS_AÑO if a["capex"] else None
    a["beneficio_por_segundo"] = a["beneficio"] / SEGUNDOS_AÑO if a["beneficio"] else None
    return a


def año_fiscal(f: str) -> int:
    """Convención de Compustat: el ejercicio cuenta como del año en que acaba si acaba de junio en adelante;
    si acaba entre enero y mayo, como del año anterior (NVIDIA ene-2026 → 2025, Microsoft jun-2026 → 2026)."""
    d = date.fromisoformat(f)
    return d.year if d.month >= 6 else d.year - 1


def serie_grupo(empresas_metricas: list[tuple]) -> dict:
    """Capex, FCF y beneficio anuales sumados por año fiscal. Sólo años en los que están todas las empresas."""
    por_año: dict = {}
    for e, m in empresas_metricas:
        tc = e.tipo_cambio or 0
        for clave in ("capex", "fcf", "beneficio"):
            for f, v in e.anual.get(clave, []):
                a = año_fiscal(f)
                por_año.setdefault(a, {}).setdefault(clave, {})[e.ticker] = (abs(v) if clave == "capex" else v) * tc
    n = len(empresas_metricas)
    años = sorted(a for a, d in por_año.items() if all(len(d.get(c, {})) == n for c in ("capex", "fcf", "beneficio")))
    return {"años": años, **{c: [sum(por_año[a][c].values()) for a in años] for c in ("capex", "fcf", "beneficio")}}
