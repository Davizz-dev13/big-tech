"""Pruebas de los cálculos, el formato y la página (python -m pytest)."""
from types import SimpleNamespace

from bigtech import calculos as C
from bigtech import formato as F
from bigtech import universo as U


def empresa(**kw):
    base = dict(ttm={}, tipo_cambio=1.0, anual={}, trailing_hist={}, cap=1e12, fecha_cuentas="2026-06-30", ticker="X")
    base.update(kw)
    return SimpleNamespace(**base)


def test_formato_espanol():
    assert F.dinero(586_027e6) == "586.027 M$"
    assert F.dinero(-11_625e6) == "−11.625 M$"
    assert F.dinero(2.69e12) == "2,69 bill. $"
    assert F.dinero(None) == "—"
    assert F.pct(0.613) == "61 %"
    assert F.pct(0.0634, 1, signo=True) == "+6,3 %"
    assert F.veces(1.58) == "1,6×"
    assert F.fecha("2026-10-30") == "30 oct 2026"


def test_metricas_basicas():
    e = empresa(ttm={"ingresos": 100.0, "beneficio": 20.0, "flujo_operativo": 50.0, "capex": -30.0, "fcf": 20.0},
                cap=400.0)
    m = C.metricas(e)
    assert m["capex"] == 30.0                 # el capex se muestra en positivo
    assert abs(m["capex_ocf"] - 0.6) < 1e-12
    assert abs(m["capex_fcf"] - 1.5) < 1e-12
    assert abs(m["margen"] - 0.2) < 1e-12
    assert m["per"] == 20.0
    assert m["rentable"] is True


def test_conversion_de_moneda_y_capex_derivado():
    e = empresa(ttm={"ingresos": 1000.0, "beneficio": -10.0, "flujo_operativo": 300.0, "fcf": -100.0}, tipo_cambio=0.5)
    m = C.metricas(e)
    assert m["capex"] == 200.0                # (300 − (−100)) × 0,5
    assert m["derivado"] == ["capex"]
    assert m["rentable"] is False and m["per"] is None
    assert m["capex_fcf"] is None             # sin FCF positivo no hay ratio


def test_hace_un_año():
    hist = [("2024-06-30", 1.0), ("2025-06-30", 2.0), ("2025-12-31", 3.0)]
    assert C.hace_un_año(hist, "2026-06-30") == ("2025-06-30", 2.0)
    assert C.hace_un_año(hist, "2026-09-30") is None   # ninguno a ±45 días de un año antes


def test_año_fiscal():
    assert C.año_fiscal("2026-06-30") == 2026
    assert C.año_fiscal("2026-01-31") == 2025
    assert C.año_fiscal("2025-12-31") == 2025


def test_agregado():
    ms = [C.metricas(empresa(ttm={"ingresos": 10.0, "beneficio": 2.0, "flujo_operativo": 5.0, "capex": -3.0, "fcf": 2.0})),
          C.metricas(empresa(ttm={"ingresos": 10.0, "beneficio": 1.0, "flujo_operativo": 5.0, "capex": -6.0, "fcf": -1.0}))]
    a = C.agregado(ms)
    assert a["capex"] == 9.0 and a["fcf"] == 1.0 and a["rentables"] == 2 and a["fcf_negativo"] == 1
    assert abs(a["capex_ocf"] - 0.9) < 1e-12


def test_universo():
    tick = [t for _, _, l in U.GRUPOS for _, _, t, _ in l]
    assert len(U.MAG7) == 7 and len(set(tick)) == len(tick)
    for pedido in ("TSM", "MU", "AVGO"):
        assert pedido in tick
