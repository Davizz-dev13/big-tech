# Big Tech: ¿rentable?

¿Les sale a cuenta la IA a las grandes tecnológicas? Capex, caja libre y beneficio de las 7 magníficas, los laboratorios de IA y otras grandes tecnológicas, con fuentes. Hecho en Python. Forma parte de [Sharpe Lab](https://davizz-dev13.github.io/sharpe-lab/).

**Web:** https://davizz-dev13.github.io/big-tech/

Inspirado en [isaiprofitable.com](https://isaiprofitable.com/), que mide sólo el gasto y el ingreso de IA de cada empresa. Aquí se mira la empresa entera: cuánto invierte (capex), cuánta caja le queda libre y cuánto gana.

- **Titular**: la respuesta (sale de los datos con una regla fija: «De momento, sí» si las 7 tienen beneficio y su caja libre conjunta es positiva; «A medias» si la caja es positiva pero alguna pierde dinero; «No» si la caja libre conjunta es negativa) y avisos automáticos (quién quema caja, quién dedica más del 75 % de su caja al capex, cuánto ha crecido el capex).
- **Cifras de las 7** de los últimos 12 meses y un **contador** del capex gastado desde que abres la página (estimación: capex anual repartido por igual).
- **Tarjetas** por empresa: capex, caja libre (FCF), capex / caja operativa, capex / FCF, FCF frente a hace un año, ingresos, beneficio neto, margen, PER, capitalización y la etiqueta **SÍ/NO rentable**. Toca una tarjeta para ver el minigráfico de capex y caja libre por año, las notas (divisa, datos que faltan) y los enlaces a las fuentes.
- **Ordenar** por capitalización, capex, capex / caja, FCF, beneficio, margen, ingresos, PER o A–Z, y **filtrar** por sector o país.
- **Laboratorios de IA** (OpenAI, Anthropic, xAI): no cotizan, así que sus cifras salen de folletos ante la SEC o de prensa, con fuente y fecha. Se mantienen a mano en [`datos/labs_ia.json`](datos/labs_ia.json).
- Dos gráficos de Plotly: capex, caja libre y beneficio de las 7 por año fiscal, y el capex como % de la caja operativa de cada empresa.

## Datos

| Qué | De dónde |
| --- | --- |
| Ingresos, beneficio neto, flujo operativo, capex y caja libre de los últimos 12 meses y anuales | Yahoo Finance (series `fundamentals-timeseries`: `trailing*` y `annual*`) |
| Sector, industria | Yahoo Finance (`quoteSummary`, módulo `assetProfile`) |
| Tipos de cambio | Yahoo Finance (cierres diarios de `XXX=X`) |
| Capitalización en dólares, país y logotipos | [companiesmarketcap.com](https://companiesmarketcap.com/) (CSV del ranking mundial) |
| Laboratorios de IA | Folletos S-1 / F-1 en la SEC y prensa, enlazados uno a uno en `datos/labs_ia.json` |

- **Últimos 12 meses** = suma de los cuatro últimos trimestres publicados por cada empresa. **Rentable** = beneficio neto atribuible a los accionistas positivo. **Caja libre (FCF)** = flujo operativo − capex. **PER** = capitalización / beneficio neto de 12 meses, todo en dólares.
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
build.py               orquesta todo: descarga, cálculos, gráficos y página
bigtech/universo.py    qué empresas salen y por qué (edítalo para añadir o quitar)
bigtech/fuentes.py     companiesmarketcap + Yahoo Finance (curl_cffi)
bigtech/calculos.py    paso a dólares, ratios, hace un año y agregados
bigtech/graficos.py    figuras de Plotly y minigráficos SVG
bigtech/formato.py     números a la española
bigtech/paises.py      países, banderas y sectores en español
datos/labs_ia.json     cifras de OpenAI, Anthropic y xAI con sus fuentes (a mano)
plantillas/index.html  plantilla Jinja
estatico/              CSS, el JavaScript mínimo (ordenar, filtrar, contador) y el favicon
tests/                 pruebas (pytest)
```

*Proyecto personal de aprendizaje. Nada de esto es asesoramiento financiero.*
