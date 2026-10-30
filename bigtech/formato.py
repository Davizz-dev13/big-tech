"""Formato de números a la española: coma decimal, punto de millares."""
from __future__ import annotations

from datetime import date

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MENOS = "−"


def num(x: float, dec: int = 2) -> str:
    s = f"{x:,.{dec}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def pct(r: float | None, dec: int = 0, signo: bool = False) -> str:
    if r is None:
        return "—"
    v = r * 100
    txt = num(abs(v), dec)
    if signo:
        txt = ("+" if v > 0 else MENOS if v < 0 else "") + txt
    elif v < 0:
        txt = MENOS + txt
    return f"{txt} %"


def dinero(x: float | None) -> str:
    """586.012 M$ · 1,23 bill. $ (billón español = 10¹²)."""
    if x is None:
        return "—"
    s = MENOS if x < 0 else ""
    a = abs(x)
    if a >= 1e12:
        return f"{s}{num(a / 1e12, 2)} bill. $"
    if a >= 1e6:
        return f"{s}{num(a / 1e6, 0)} M$"
    return f"{s}{num(a, 0)} $"


def veces(x: float | None) -> str:
    return "—" if x is None else f"{num(x, 1)}×"


def per(x: float | None) -> str:
    if x is None:
        return "—"
    return num(x, 0) if x >= 100 else num(x, 1)


def fecha(d) -> str:
    if isinstance(d, str):
        d = date.fromisoformat(d[:10])
    return f"{d.day} {MESES[d.month - 1]} {d.year}"


def mes(d) -> str:
    if isinstance(d, str):
        d = date.fromisoformat(d[:10])
    return f"{MESES[d.month - 1]} {d.year}"
