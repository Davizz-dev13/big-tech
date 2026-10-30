/* Big Tech: ¿rentable? — lo mínimo en el navegador: ordenar y filtrar tarjetas, el contador y los dos gráficos. */
(function () {
  "use strict";
  var fmt = new Intl.NumberFormat("es-ES", { maximumFractionDigits: 0 });

  // Contador: capex de las 7 desde que se abrió la página (estimación lineal)
  var c = document.getElementById("contador");
  if (c) {
    var ritmo = parseFloat(c.dataset.ritmo) || 0, t0 = performance.now();
    var tick = function () {
      c.textContent = fmt.format(ritmo * (performance.now() - t0) / 1000).replace(/\u00a0/g, ".") + " $";
      requestAnimationFrame(tick);
    };
    if (ritmo) requestAnimationFrame(tick);
  }

  // Ordenar y filtrar
  var orden = document.getElementById("orden"), fs = document.getElementById("f-sector"), fp = document.getElementById("f-pais");
  var num = function (el, k) { var v = el.dataset[k.replace(/_(.)/g, function (_, x) { return x.toUpperCase(); })]; return v === "" || v === undefined ? NaN : parseFloat(v); };
  function aplicar() {
    var k = orden.value, s = fs.value, p = fp.value;
    document.querySelectorAll(".bt-cards[data-grupo]").forEach(function (cont) {
      var cards = Array.prototype.slice.call(cont.children);
      cards.sort(function (a, b) {
        if (k === "az") return a.dataset.nombre.localeCompare(b.dataset.nombre, "es");
        var x = num(a, k), y = num(b, k);
        if (isNaN(x) && isNaN(y)) return 0;
        if (isNaN(x)) return 1;
        if (isNaN(y)) return -1;
        return k === "per" ? x - y : y - x;
      });
      var visibles = 0;
      cards.forEach(function (el) {
        var ok = (!s || el.dataset.sector === s) && (!p || el.dataset.pais === p);
        el.hidden = !ok; if (ok) visibles++;
        cont.appendChild(el);
      });
      var vacio = cont.parentElement.querySelector(".bt-vacio");
      if (vacio) vacio.hidden = visibles > 0;
    });
  }
  [orden, fs, fp].forEach(function (el) { if (el) el.addEventListener("change", aplicar); });

  // Gráficos (diseñados en Python; aquí sólo se dibujan)
  function dibujar() {
    if (!window.Plotly) return;
    var figs = JSON.parse(document.getElementById("figs").textContent);
    var cfg = { displayModeBar: false, responsive: true, locale: "es" };
    var movil = window.matchMedia("(max-width: 760px)").matches;
    [["g-evolucion", figs.evolucion], ["g-capex-caja", figs.capex_caja]].forEach(function (par) {
      var el = document.getElementById(par[0]); if (!el) return;
      var lay = par[1].layout;
      if (movil) { lay.font = Object.assign({}, lay.font, { size: 11 }); if (par[0] === "g-evolucion") par[1].data.forEach(function (t) { t.textfont = { size: 8 }; }); }
      Plotly.newPlot(el, par[1].data, lay, cfg);
    });
  }
  if (document.readyState === "complete") dibujar(); else window.addEventListener("load", dibujar);
})();
