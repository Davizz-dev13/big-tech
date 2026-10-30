# Big Tech

Ingresos, flujo de caja libre (FCF), margen FCF, precio / FCF y gasto en capex de las 7 magníficas, los laboratorios de IA y otras grandes tecnológicas, con fuentes. Hecho en Python. Forma parte de [Sharpe Lab](https://davizz-dev13.github.io/sharpe-lab/).

**Web:** https://davizz-dev13.github.io/big-tech/

- **Tarjetas** por empresa, sencillas: nombre y logo, margen FCF, precio / FCF y tres barras a la misma escala dentro de la tarjeta: **gasto en capex**, **ingresos** y **flujo de caja libre (FCF)** (en rojo, a la izquierda de la línea del cero, si es negativo). Cifras de los últimos 12 meses, en formato corto («471 mil M$»).
- **Ordenar** por ingresos, FCF, margen FCF, precio / FCF (menor primero; «n. s.» al final), gasto en capex o A–Z.
- **Laboratorios de IA** (OpenAI, Anthropic, xAI): no cotizan, así que sus cifras de 2025 salen de folletos ante la SEC o de prensa, con fuente y fecha. Se mantienen a mano en [`datos/labs_ia.json`](datos/labs_ia.json).
- **Fuentes y metodología** al final de la página. `datos.json` lleva además el resto de métricas (beneficio neto, margen neto, PER, capex / caja operativa, capitalización, histórico).

## Datos

| Qué | De dónde |
| --- | --- |
| Ingresos, beneficio neto, flujo operativo, capex y caja libre de los últimos 12 meses y anuales | Yahoo Finance (series `fundamentals-timeseries`: `trailing*` y `annual*`) |
| Sector, industria | Yahoo Finance (`quoteSummary`, módulo `assetProfile`) |
| Tipos de cambio | Yahoo Finance (cierres diarios de `XXX=X`) |
| Capitalización en dólares, país y logotipos | [companiesmarketcap.com](https://companiesmarketcap.com/) (CSV del ranking mundial) |
| Laboratorios de IA | Folletos S-1 / F-1 en la SEC y prensa, enlazados uno a uno en `datos/labs_ia.json` |

- **Últimos 12 meses** = suma de los cuatro últimos trimestres publicados por cada empresa. **Rentable** = beneficio neto atribuible a los accionistas positivo. **Caja libre (FCF)** = flujo operativo − capex. **PER** = capitalización / beneficio neto de 12 meses (sólo en `datos.json`). **Margen FCF** = FCF / ingresos. **Precio / FCF** = capitalización / FCF; con FCF ≤ 0 no hay múltiplo («n. s.»). Todo en dólares.
- **Divisas**: las cuentas en otra moneda (TWD, KRW, CNY, EUR) se pasan a dólares con la media de los cierres diarios de los 12 meses que cubren. El cambio frente a hace un año se calcula en la moneda original, así que la divisa no lo distorsiona.
- **Hace un año**: si Yahoo tiene la cifra de 12 meses que acaba justo un año antes (±45 días) se compara con ella; si no, se compara el último ejercicio anual con el anterior, y la tarjeta lo indica.
- **Nunca se rellena un número**: si falta un dato se muestra «—» y se apunta en el log y en la web. Si Yahoo no da el capex de 12 meses pero sí el flujo operativo y el FCF, se calcula como diferencia y se avisa.
- Si companiesmarketcap no responde, se usa la copia del ranking guardada en `datos/ranking_respaldo.csv`. Si menos de 20 empresas traen cuentas, la Action falla a propósito y la web se queda como estaba.

## Actualización

La Action [`actualizar.yml`](.github/workflows/actualizar.yml) se ejecuta de lunes a viernes a las 22:15 UTC (tras el cierre de Nueva York), además de con cada push a `main` y a mano desde *Actions → Run workflow*. Descarga los datos, pasa las pruebas, genera la web y la publica en GitHub Pages. Las capitalizaciones cambian a diario; las cuentas, cuando cada empresa publica resultados. Los laboratorios de IA se actualizan editando `datos/labs_ia.json`.

## Ejecutarlo en local

```bash
python -m venv .venv && source .venv/bin/activate   # en Windows: .venv\Scripts\activate
pip install -r requirements.txt pytest
python -m pytest -q
python build.py                      # descarga los datos y genera _site/
python -m http.server -d _site 8000  # abre http://localhost:8000
```

`python build.py --cache crudo.pkl` guarda la descarga la primera vez y la reutiliza después, para retocar el diseño sin volver a pedir los datos.

## Estructura

```
build.py               orquesta todo: descarga, cálculos y página
bigtech/universo.py    qué empresas salen y por qué (edítalo para añadir o quitar)
bigtech/fuentes.py     companiesmarketcap + Yahoo Finance (curl_cffi)
bigtech/calculos.py    paso a dólares, ratios, hace un año y agregados
bigtech/graficos.py    figuras de Plotly y minigráficos SVG (no se usan en la página actual)
bigtech/formato.py     números a la española
bigtech/paises.py      países, banderas y sectores en español
datos/labs_ia.json     cifras de OpenAI, Anthropic y xAI con sus fuentes (a mano)
plantillas/index.html  plantilla Jinja
estatico/              CSS, el JavaScript mínimo (ordenar) y el favicon
tests/                 pruebas (pytest)
```

*Proyecto personal de aprendizaje. Nada de esto es asesoramiento financiero.*
