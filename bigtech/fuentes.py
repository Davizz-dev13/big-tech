"""Descarga de datos.

- companiesmarketcap.com: capitalización en dólares (CSV público del ranking mundial) y logotipos.
- Yahoo Finance: cuentas de los últimos doce meses (serie "fundamentals-timeseries": los valores
  trailing* son la suma de los cuatro últimos trimestres publicados), cuentas anuales, perfil
  (sector, sede) y tipos de cambio.
"""
from __future__ import annotations

import csv
import io
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from curl_cffi import requests

log = logging.getLogger("bigtech")

URL_RANKING = "https://companiesmarketcap.com/?download=csv"
URL_LOGO = "https://companiesmarketcap.com/img/company-logos/64/{}.webp"
URL_SERIES = "https://query2.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/{}"
URL_PERFIL = "https://query2.finance.yahoo.com/v10/finance/quoteSummary/{}"
URL_GRAFICO = "https://query2.finance.yahoo.com/v8/finance/chart/{}"

TTM = {
    "ingresos": "trailingTotalRevenue",
    "beneficio": "trailingNetIncomeCommonStockholders",
    "beneficio_total": "trailingNetIncome",
    "flujo_operativo": "trailingOperatingCashFlow",
    "capex": "trailingCapitalExpenditure",
    "fcf": "trailingFreeCashFlow",
}
ANUAL = {
    "flujo_operativo": "annualOperatingCashFlow",
    "capex": "annualCapitalExpenditure",
    "fcf": "annualFreeCashFlow",
    "beneficio": "annualNetIncomeCommonStockholders",
    "ingresos": "annualTotalRevenue",
}


@dataclass
class Empresa:
    grupo: str
    simbolo_ranking: str
    simbolo: str               # Yahoo
    ticker: str
    nombre: str
    pais: str = ""
    cap: float | None = None   # USD
    origen_cap: str = ""
    sector: str = ""
    industria: str = ""
    moneda: str = ""           # moneda de las cuentas
    fecha_cuentas: str = ""    # cierre del último trimestre incluido en los 12 meses
    ttm: dict = field(default_factory=dict)            # moneda original
    trailing_hist: dict = field(default_factory=dict)  # clave -> [(fecha, valor)]
    anual: dict = field(default_factory=dict)          # clave -> [(fecha, valor)]
    tipo_cambio: float | None = None                   # USD por unidad (media de 12 meses)
    tc_info: dict | None = None
    url_ranking: str = ""
    logo: bytes | None = None
    faltan: list = field(default_factory=list)


def sesion() -> requests.Session:
    s = requests.Session(impersonate="chrome")
    s.headers.update({"Accept-Language": "en-US,en;q=0.9"})
    return s


def _get(s, url, intentos=4, **kw):
    ultimo = None
    for i in range(intentos):
        try:
            r = s.get(url, timeout=30, **kw)
            if r.status_code == 200:
                return r
            ultimo = f"HTTP {r.status_code}"
            if r.status_code == 404:
                break
        except Exception as e:
            ultimo = str(e)
        time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"{url}: {ultimo}")


def ranking(s, respaldo: Path | None = None) -> tuple[dict, str]:
    """{símbolo: fila} del ranking mundial por capitalización."""
    origen = "companiesmarketcap.com"
    try:
        texto = _get(s, URL_RANKING).text
        if not texto.startswith('"Rank"'):
            raise RuntimeError("respuesta inesperada")
        if respaldo:
            respaldo.write_text("\n".join(texto.splitlines()[:301]) + "\n", encoding="utf-8")
    except Exception as e:
        if not (respaldo and respaldo.exists()):
            raise
        log.warning("Ranking en vivo no disponible (%s); uso la copia guardada", e)
        texto = respaldo.read_text(encoding="utf-8")
        origen = "companiesmarketcap.com (copia guardada en el repo; la descarga de hoy falló)"
    return {f["Symbol"].strip(): f for f in csv.DictReader(io.StringIO(texto))}, origen


def fichas_ranking(s) -> dict:
    """{símbolo: URL de su ficha en companiesmarketcap} para las 100 primeras (mejor esfuerzo)."""
    import re
    try:
        h = _get(s, "https://companiesmarketcap.com/", intentos=2).text
    except Exception as e:
        log.info("Sin fichas de companiesmarketcap (%s)", e)
        return {}
    pares = re.findall(r'href="/([a-z0-9\-]+)/marketcap/".{0,400}?company-code">(?:<span[^>]*></span>)?([^<]+)<', h, flags=re.S)
    return {sim.strip(): f"https://companiesmarketcap.com/{slug}/marketcap/" for slug, sim in pares}


def _crumb(s) -> str | None:
    try:
        s.get("https://fc.yahoo.com", timeout=20)
    except Exception:
        pass
    try:
        return _get(s, "https://query2.finance.yahoo.com/v1/test/getcrumb").text.strip()
    except Exception as e:
        log.warning("Sin crumb de Yahoo (%s)", e)
        return None


def _serie(s, simbolo, tipos, años):
    hasta = int(time.time())
    r = _get(s, URL_SERIES.format(simbolo), params={
        "type": ",".join(tipos), "period1": hasta - años * 365 * 86400, "period2": hasta,
        "merge": "false", "padTimeSeries": "true", "lang": "en-US", "region": "US"})
    out = {}
    for bloque in r.json()["timeseries"]["result"]:
        t = bloque["meta"]["type"][0]
        vals = [v for v in (bloque.get(t) or []) if v and v.get("reportedValue")]
        out[t] = [(v["asOfDate"], float(v["reportedValue"]["raw"]), v.get("currencyCode") or "") for v in vals]
    return out


def cuentas(s, e: Empresa) -> None:
    try:
        ser = _serie(s, e.simbolo, list(TTM.values()) + list(ANUAL.values()), 6)
    except Exception as ex:
        log.warning("%s: sin cuentas (%s)", e.simbolo, ex)
        e.faltan.append("cuentas")
        return
    ult = {t: v[-1] for t, v in ser.items() if v and t.startswith("trailing")}
    fechas = sorted({v[0] for v in ult.values()})
    e.fecha_cuentas = fechas[-1] if fechas else ""
    for clave, tipo in TTM.items():
        v = ult.get(tipo)
        # Sólo cifras del mismo cierre, para no mezclar periodos distintos.
        if v and v[0] == e.fecha_cuentas:
            e.ttm[clave] = v[1]
            e.moneda = e.moneda or v[2]
        e.trailing_hist[clave] = [(f, x) for f, x, _ in ser.get(tipo, [])]
    for clave, tipo in ANUAL.items():
        e.anual[clave] = [(f, x) for f, x, _ in ser.get(tipo, [])]
        if not e.moneda and ser.get(tipo):
            e.moneda = ser[tipo][-1][2]
    if "beneficio" not in e.ttm and "beneficio_total" in e.ttm:
        e.ttm["beneficio"] = e.ttm["beneficio_total"]
    if "fcf" not in e.ttm and {"flujo_operativo", "capex"} <= e.ttm.keys():
        e.ttm["fcf"] = e.ttm["flujo_operativo"] + e.ttm["capex"]
    for clave in ("ingresos", "beneficio", "flujo_operativo", "capex", "fcf"):
        if clave not in e.ttm:
            e.faltan.append(clave)


def perfil(s, e: Empresa, crumb: str | None) -> dict:
    try:
        params = {"modules": "assetProfile,financialData,price"}
        if crumb:
            params["crumb"] = crumb
        q = _get(s, URL_PERFIL.format(e.simbolo), params=params).json()["quoteSummary"]["result"][0]
    except Exception as ex:
        log.warning("%s: sin perfil (%s)", e.simbolo, ex)
        e.faltan.append("perfil")
        return {}
    ap = q.get("assetProfile") or {}
    e.sector = ap.get("sector") or ""
    e.industria = ap.get("industry") or ""
    if not e.pais:
        e.pais = ap.get("country") or ""
    if not e.moneda:
        e.moneda = (q.get("financialData") or {}).get("financialCurrency") or ""
    return q.get("price") or {}


def tipo_de_cambio(s, moneda: str, fin: str, cache: dict) -> dict | None:
    """USD por unidad de `moneda`: media de los cierres diarios de los 12 meses que acaban en `fin`."""
    if moneda == "USD":
        return {"usd_por_unidad": 1.0}
    clave = (moneda, fin)
    if clave in cache:
        return cache[clave]
    try:
        f = datetime.fromisoformat(fin).replace(tzinfo=timezone.utc)
        ini = f - timedelta(days=365)
        r = _get(s, URL_GRAFICO.format(f"{moneda}=X"), params={
            "period1": int(ini.timestamp()), "period2": int((f + timedelta(days=1)).timestamp()), "interval": "1d"})
        cierres = [x for x in r.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"] if x]
        if len(cierres) < 150:
            raise RuntimeError(f"sólo {len(cierres)} cierres")
        # Media del tipo USD→moneda y luego la inversa: equivale a convertir un flujo repartido por igual en el año.
        cache[clave] = {"usd_por_unidad": len(cierres) / sum(cierres), "dias": len(cierres),
                        "desde": ini.date().isoformat(), "hasta": fin, "par": f"{moneda}=X"}
    except Exception as ex:
        log.warning("Tipo de cambio %s no disponible (%s)", moneda, ex)
        cache[clave] = None
    return cache[clave]


def spot(s, moneda: str, cache: dict) -> float | None:
    if moneda == "USD":
        return 1.0
    if ("spot", moneda) not in cache:
        try:
            r = _get(s, URL_GRAFICO.format(f"{moneda}=X"), params={"range": "5d", "interval": "1d"})
            cache[("spot", moneda)] = 1 / r.json()["chart"]["result"][0]["meta"]["regularMarketPrice"]
        except Exception:
            cache[("spot", moneda)] = None
    return cache[("spot", moneda)]


def logo(s, simbolo_ranking: str) -> bytes | None:
    try:
        r = _get(s, URL_LOGO.format(simbolo_ranking), intentos=2)
        return r.content if r.content[:4] == b"RIFF" else None
    except Exception as ex:
        log.info("%s: sin logo (%s)", simbolo_ranking, ex)
        return None


def descargar(grupos, respaldo: Path | None = None) -> tuple[list[Empresa], dict]:
    s = sesion()
    filas, origen = ranking(s, respaldo)
    crumb = _crumb(s)
    fichas = fichas_ranking(s)
    cache: dict = {}
    out = []
    for gid, _, lista in grupos:
        for sr, sy, tk, nombre in lista:
            e = Empresa(grupo=gid, simbolo_ranking=sr, simbolo=sy, ticker=tk, nombre=nombre)
            e.url_ranking = fichas.get(sr, "")
            fila = filas.get(sr)
            if fila:
                e.cap = float(fila["marketcap"])
                e.pais = fila["country"].strip()
                e.origen_cap = origen
            cuentas(s, e)
            precio = perfil(s, e, crumb)
            if e.cap is None:
                mc = (precio.get("marketCap") or {}).get("raw")
                tc = spot(s, precio.get("currency") or "USD", cache) if mc else None
                if mc and tc:
                    e.cap = mc * tc
                    e.origen_cap = "Yahoo Finance (no estaba en el ranking)"
                else:
                    e.faltan.append("capitalizacion")
            if e.moneda and e.fecha_cuentas:
                e.tc_info = tipo_de_cambio(s, e.moneda, e.fecha_cuentas, cache)
                e.tipo_cambio = e.tc_info["usd_por_unidad"] if e.tc_info else None
            if e.tipo_cambio is None:
                e.faltan.append("tipo_de_cambio")
            e.logo = logo(s, sr)
            out.append(e)
            time.sleep(0.3)
    return out, {"ranking": origen}
